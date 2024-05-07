import base64
import os
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from django.db.models import Sum
from .models import *
from it.users.models import *
from finance.purchase_request.models import PurchaseRequest, PrItem, Attachment, UnitOfMeasurement
from ACE2.models import Ace2
from finance.comparative_schedules.models import *
from django.db.models import Q, Exists, OuterRef
import pandas as pd

def import_old_rfq(request):
    tender_csv = 'tender.csv'
    rfq_csv = 'rfq.csv'
    bid_update_csv = 'bid_update.csv'
    bids_csv = 'bids.csv'
    items_csv = 'items.csv'
    required_items_csv = 'required_items.csv'
    suppliers_csv = 'suppliers.csv'
    
    # Read the tender CSV file using pandas
    # tender_data = pd.read_csv(tender_csv)
    # print(tender_data.head())
    rfq_data = pd.read_csv(rfq_csv)
    print(rfq_data.head())
    # bid_update_data = pd.read_csv(bid_update_csv)
    # print(bid_update_data.head())
    # bids_data = pd.read_csv(bids_csv)
    # print(bids_data.head())
    # items_data = pd.read_csv(items_csv)
    # print(items_data.head())
    required_items_data = pd.read_csv(required_items_csv)
    print(required_items_data.head())
    # suppliers_data = pd.read_csv(suppliers_csv)
    # print(suppliers_data.head())
    
    # save suppliers
    # for index, row in suppliers_data.iterrows():
    #     supplier_id = row['sup_id']
    #     supplier_name = row['supplier']
    #     supplier = Supplier(
    #         name = supplier_name,
    #     )
    #     supplier.save()
    
    # save rfq
    for index, row in rfq_data.iterrows():
        print("")
        section = Sections.objects.filter(section=row['section']).first() if row['section'] else None
        procurement_plan = ProcPlan.objects.filter(proc_ref=row['proc_ref']).first() if row['proc_ref'] else None
        created_by = UserProfile.objects.filter(username=row['created_by']).first() if row['created_by'] else None
        ace = Ace2.objects.filter(ace=row['ace']).first() if row['ace'] else None
        
        pr = PurchaseRequest(
            pr_no = row['rfq_number'],
            section = section,
            procurement_plan = procurement_plan,
            requested_by = created_by,
            created_at = row['date_created'],
            ace = ace,
            scope_of_work = row['scope_of_work'],
        )
        pr.save()
        
        # att_path = 'uploads/finance/pr/attachments/' + row['specifications'].split('/')[-1] if row['specifications'] else ""

        # attachments = Attachment(
        #     file = row['attachment'],
        # )
        
    # save required items
    # for index, row in required_items_data.iterrows():
    #     pr = PurchaseRequest.objects.filter(pr_no=row['rfq_no']).first() if row['rfq_no'] else None
    #     uom = UnitOfMeasurement.objects.filter(name=row['unit_of_measurement']).first() if row['unit_of_measurement'] else None
    #     pr_item = PrItem(
    #         item_required = row['item_required'],
    #         quantity = row['quantity'],
    #         unit_of_measurement = uom,
    #         purchase_request = pr,
    #     )
    #     pr_item.save()
    
    
    
    # save comperative schedules
    # for index, row in tender_data.iterrows():
    #     cs_id = row['document_id']
    #     pr_number = row['rfq_no']
    #     pr = PurchaseRequest.objects.filter(id=pr_id).first()
    #     proc_plan = ProcPlan.objects.filter(proc_ref=row['proc_plan']).first()
    #     cs_query = ComparativeSchedules(
    #         cs_id = cs_id,
    #         pr_id = pr,
    #         proc_plan = proc_plan,
    #         scope_of_work = row['scope_of_work'],
    #         closing_date = row['closing_date'],
    #         closing_time = row['closing_time'],
    #         advert = row['advert'],
    #         pr_number = row['pr_number'],
    #         pr_date = row['pr_date'],
    #         ref_date = row['ref_date'],
    #         cs_opened = row['cs_opened'],
    #         tac_date = row['tac_date'],
    #         region = row['region'],
    #     )
    #     cs_query.save()
    
    return JsonResponse({
        "success": True,
        "message": "Data imported successfully",
        }, safe=False)

def clear_approvals(cs_id):

    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
        
    committee = Committee.objects.filter(cs_id=cs_query).all()
    if committee:
        for member in committee:
            member.committee_approval = ""
            member.committee_status = ""
            member.save()
    
    approvals = CSApproval.objects.filter(cs_id=cs_query).all()
    if approvals:
        for approval in approvals:
            approval.approval = ""
            approval.justification = ""
            approval.approval_date = None
            approval.save()
            
    return True

def get_comperative_schedules(request):
    
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    # fetch schedules created by the user
    cs = ComparativeSchedules.objects.all()

    cs_list = []
    for c in cs:
        pr = PurchaseRequest.objects.filter(id=c.pr_id_id).first()
        user = UserProfile.objects.filter(id=c.created_by_id).first()
        region = Regions.objects.filter(id=c.region_id).first()
        section = Sections.objects.filter(id=c.section_id).first()
        cs_list.append({
            "cs_id": c.cs_id,
            "pr_id": pr.id if pr else "",
            "pr_number": c.pr_number,
            "pr_date": c.pr_date,
            "scope_of_work": c.scope_of_work,
            "closing_date": c.closing_date,
            "closing_time": c.closing_time,
            "advert": c.advert,
            "pr_number": c.pr_number,
            "pr_date": c.pr_date,
            "cs_opened": c.cs_opened,
            "tac_date": c.tac_date,
            "created_by": user.username,
            "section": section.section if section else "",
            "region": region.region if region else "",
            "created_at": c.created_at,
        })
        
    context = json.dumps(cs_list, default=str)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    return render(request, user_page, {"cs": context})

def get_pending_committee(request):
    
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    # fetch schedules if user exists in the committee and has not yet approved
    cs = ComparativeSchedules.objects.filter(
    committee__user_id=user_id,
    committee__committee_approval="",
    ).all()

    cs_list = []
    for c in cs:
        pr = PurchaseRequest.objects.filter(id=c.pr_id_id).first()
        user = UserProfile.objects.filter(id=c.created_by_id).first()
        region = Regions.objects.filter(id=c.region_id).first()
        section = Sections.objects.filter(id=c.section_id).first()
        cs_list.append({
            "cs_id": c.cs_id,
            "pr_id": pr.id if pr else "",
            "pr_number": c.pr_number,
            "pr_date": c.pr_date,
            "scope_of_work": c.scope_of_work,
            "closing_date": c.closing_date,
            "closing_time": c.closing_time,
            "advert": c.advert,
            "pr_number": c.pr_number,
            "pr_date": c.pr_date,
            "cs_opened": c.cs_opened,
            "tac_date": c.tac_date,
            "created_by": user.username,
            "section": section.section if section else "",
            "region": region.region if region else "",
            "created_at": c.created_at,
        })
        
    context = json.dumps(cs_list, default=str)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    return render(request, user_page, {"cs": context})

def get_pending_approval(request):
    
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    # fetch all pending approvals
    cs = ComparativeSchedules.objects.filter(    
        Exists(Committee.objects.filter(
            cs_id=OuterRef('pk'),
            committee_approval="",
        )),
        Q(csapproval__approval=None) | Q(csapproval__approval="Rejected"),
    ).distinct()

    cs_list = []
    for c in cs:
        pr = PurchaseRequest.objects.filter(id=c.pr_id_id).first()
        user = UserProfile.objects.filter(id=c.created_by_id).first()
        region = Regions.objects.filter(id=c.region_id).first()
        section = Sections.objects.filter(id=c.section_id).first()
        cs_list.append({
            "cs_id": c.cs_id,
            "pr_id": pr.id if pr else "",
            "pr_number": c.pr_number,
            "pr_date": c.pr_date,
            "scope_of_work": c.scope_of_work,
            "closing_date": c.closing_date,
            "closing_time": c.closing_time,
            "advert": c.advert,
            "pr_number": c.pr_number,
            "pr_date": c.pr_date,
            "cs_opened": c.cs_opened,
            "tac_date": c.tac_date,
            "created_by": user.username,
            "section": section.section if section else "",
            "region": region.region if region else "",
            "created_at": c.created_at,
        })
        
    context = json.dumps(cs_list, default=str)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    return render(request, user_page, {"cs": context})


def get_comperative_schedule(request, cs_id):
    
    username = request.user.username
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "cs_id": cs_id,
        "username": username,
    })

def create_comperative_schedule(request):

    username = request.user.username
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "username": username,
    })

def get_comperative_schedule_data(request, cs_id):
    
    request_user = request.user
    request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
    
    user_comparative_schedule_role = None
    for role in request_user_profile.roles.all():
        print("role id:", role.id)
        user_ace_role_ = Roles.objects.filter(id=role.id).first() if role.id else None
        print("role application:", user_ace_role_.application)
        if user_ace_role_.application == "comparative_schedule":
            user_comparative_schedule_role = user_ace_role_
            
    cs = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    pr = PurchaseRequest.objects.filter(id=cs.pr_id_id).first()
    proc_plans = ProcPlan.objects.all()
    proc_plan = ""
    try:
        proc_plan = cs.proc_plan if cs.proc_plan else ""
    except Exception as ex:
        print("Error: ", ex)
    user = UserProfile.objects.filter(id=cs.created_by_id).first()
    region = Regions.objects.filter(id=cs.region_id).first()
    section = Sections.objects.filter(id=cs.section_id).first()
    items = CSItems.objects.filter(cs_id=cs).all()
    cs_items = CSRequiredItems.objects.filter(cs_id=cs).all()
    bids = Bids.objects.filter(cs_id=cs).all()
    compliance = CSCompliance.objects.filter(cs_id=cs).all()
    complianceRemarks = CSComplianceRemarks.objects.filter(cs_id=cs).all()
    print("compliance remarks: ", complianceRemarks)
    # compliance remarks
    
    rankings = Ranking.objects.filter(cs_id=cs).all()
    committee = Committee.objects.filter(cs_id=cs).all()
    gm_approval = CSApproval.objects.filter(cs_id=cs, approver_role="general_manager").first()
    fm_approval = CSApproval.objects.filter(cs_id=cs, approver_role="finance_manager").first()
    
    suppliers = Supplier.objects.all()
    pr_items = PrItem.objects.filter(purchase_request=cs.pr_id_id, ordered=False).all()
    users = UserProfile.objects.all()
    
    items_list = []
    for item in items:
        items_list.append({
            "item_id": item.item_id,
            "item_required": item.item_name,
            "quantity": item.quantity,
            "unit_of_measurement": item.unit_of_measurement,
            "created_at": item.created_at,
        })
        
    grouped_by_bid = {}
    grouped_data = {}
    for bid in bids:
        bid_no = bid.bid_no
        if bid_no not in grouped_data:
            encoded_file_data = ""
            if bid.bid_document:
                with open(bid.bid_document, 'rb') as f:
                    file_data = f.read()
                encoded_file_data = base64.b64encode(file_data).decode('utf-8')

            grouped_data[bid_no] = {
                'bid_count': bid.bid_no,
                'supplier_name': bid.sup_id.name,
                'bid_no': bid.bid_no,
                'bid_date': bid.quote_date,
                'bid_document': encoded_file_data,
                'items': []
            }
        grouped_data[bid_no]['items'].append({
            'item_id': bid.item_id.item_id,
            'item_required': bid.item_id.item_name,  # assume this is constant
            'quantity': bid.item_id.quantity,
            'unit_of_measurement': bid.item_id.unit_of_measurement,
            'unit_price': bid.unit_price,
            'vat': bid.vat,
            'total_price': bid.total,
        })

    result = list(grouped_data.values())
        
    compliance_list = []
    for comp in compliance:
        print("comp: ", comp.supplier_id)
        compliance_list.append({
            "supplier_name": comp.supplier_id.name if comp.supplier_id else "",
            "payment_terms": comp.payment_terms,
            "bid_validity": comp.bid_validity,
            "delivery_period": comp.delivery_period,
            "technical_specifications": comp.technical_specifications,
            "valid_tax_clearance": comp.valid_tax_clearance,
            "registered_with_praz": comp.registered_with_praz,
            "site_visit_done": comp.site_visit_done,
            "samples_delivered": comp.samples_delivered,
            "decision": comp.decision,
            "remarks": comp.remarks,
            "created_at": comp.created_at,
        })
    
    compliance_remarks = []
    for remark in complianceRemarks:
        compliance_remarks.append({
        "supplier": remark.supplier_id.id,
        "supplier_name": remark.supplier_id.name,
        "remarks": remark.remarks,
        })
        
    rankings_list = []
    for rank in rankings:
        supplier = Supplier.objects.filter(id=rank.supplier_id.id).first()
        rankings_list.append({
            "supplier_name": supplier.name if supplier else "",
            "rank": rank.rank,
            "remarks": rank.remarks,
            "decision": rank.decision,
            "total": rank.total,
            "created_at": rank.created_at,
        })
        
    committee_list = []
    for member in committee:
        if member.user:
            committee_list.append({
                "memberUserName": member.user.username if member.user else "",
                "memberName": member.user.first_name + " " + member.user.last_name if member.user else "",
                "memberPosition": member.committee_position,
                "committeeStatus": member.committee_status,
                "memberApproval": member.committee_approval if member.committee_approval else "",
                "committeeJustification": member.justification,
                "committeeDate": member.committee_date,
            }) 
    
    encoded_advert_file = ""
    try:
        if cs.advert:
            with open(cs.advert, 'rb') as f:
                file_data = f.read()
            encoded_advert_file = base64.b64encode(file_data).decode('utf-8')
    except Exception as ex:
        print("Error: ", ex)
        
    cs_owner = UserProfile.objects.filter(id=cs.created_by_id).first()
    pr_item_list = []
    for pr_item in pr_items:
        pr_item_list.append({
            "id": pr_item.id,
            "item_required": pr_item.item_required,
            "quantity": pr_item.quantity,
            "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
            "ordered": pr_item.ordered,
        })
        
    pr_attachments = Attachment.objects.filter(purchase_request=pr).all()
    
    pr_at_list = []
    for at in pr_attachments:
        encoded_file_data = ""
        if at.file:
            try:
                file_data = at.file.read()
                encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                pr_at_list.append({
                    "id": at.id,
                    "file": encoded_file_data,
                    "name": os.path.basename(at.file.name),
                })
            except Exception as ex:
                print("Error: ", ex)
                
    cs_item_list = []
    for cs_item in cs_items:
        cs_item_list.append({
            "id": cs_item.id,
            "item_required": cs_item.item_name,
            "quantity": cs_item.quantity,
            "unit_of_measurement": cs_item.unit_of_measurement,
        })

    context = {
        "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
        "cs_id": cs.cs_id,
        "cs_owner": cs_owner.username if cs_owner else "",
        "pr_id": pr.id,
        "pr_number": cs.pr_number,
        "pr_date": cs.pr_date,
        "proc_plan": {
            "id": proc_plan.id,
            "proc_ref": proc_plan.proc_ref,
            "description": proc_plan.description,
            } if proc_plan else {},
        "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
        "scope_of_work": cs.scope_of_work,
        "closing_date": cs.closing_date,
        "closing_time": cs.closing_time,
        "advert": encoded_advert_file,
        "pr_number": cs.pr_number,
        "pr_date": cs.pr_date,
        "ref_date": cs.ref_date,
        "cs_opened": cs.cs_opened,
        "tac_date": cs.tac_date,
        "created_by": user.username,
        "section": section.section if section else "",
        "region": region.region if region else "",
        "created_at": cs.created_at,
        "items": items_list,
        "bids": result,
        "compliance": compliance_list,
        "complianceRemarks": compliance_remarks,
        "rankings": rankings_list,
        "committee": committee_list,
        "gm_approval": {
            "id": gm_approval.id,
            "approver": gm_approval.user.username if gm_approval.user else "",
            "approver_name": gm_approval.user.first_name + " " + gm_approval.user.last_name if gm_approval.user else "",
            "approver_role": gm_approval.approver_role,
            "approval": gm_approval.approval,
            "justification": gm_approval.justification,
            "approval_date": gm_approval.approval_date,
            } if gm_approval else {},
        "fm_approval": {
            "id": fm_approval.id,
            "approver": fm_approval.user.username if fm_approval.user else "",
            "approver_name": fm_approval.user.first_name + " " + fm_approval.user.last_name if fm_approval.user else "",
            "approver_role": fm_approval.approver_role,
            "approval": fm_approval.approval,
            "justification": fm_approval.justification,
            "approval_date": fm_approval.approval_date,
            } if fm_approval else {},
        
        "pr_items": pr_item_list,
        "pr_attachments": pr_at_list,
        "cs_items": cs_item_list,
        "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
        "suppliers": list(suppliers.values('id', 'name')),
        "users": list(users.values('id', 'username', 'first_name', 'last_name')),
    }
    
    context = json.dumps(context, default=str)
    
    return JsonResponse(context, safe=False)

def save_file(f, file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
            return True
    else:
        return False
    
def get_create_data(request, pr_id):

    purchase_request = PurchaseRequest.objects.filter(id=pr_id).first()
    if purchase_request:
        proc_plans = ProcPlan.objects.all()
        suppliers = Supplier.objects.all()
        users = UserProfile.objects.all()
        uom = UnitOfMeasurement.objects.all()
        pr_items = PrItem.objects.filter(purchase_request=purchase_request, ordered=False).all()
        pr_attachments = Attachment.objects.filter(purchase_request=purchase_request).all()
        
        pr_at_list = []
        for at in pr_attachments:
            encoded_file_data = ""
            if at.file:
                try:
                    file_data = at.file.read()
                    encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                    pr_at_list.append({
                        "id": at.id,
                        "file": encoded_file_data,
                        "name": os.path.basename(at.file.name),
                    })
                except Exception as ex:
                    print("Error: ", ex)

        pr_item_list = []
        for pr_item in pr_items:
            pr_item_list.append({
                "id": pr_item.id,
                "item_required": pr_item.item_required,
                "quantity": pr_item.quantity,
                "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
                "ordered": pr_item.ordered,
            })
        
        return JsonResponse({
                "success": True,
                "message": "PR details retrieved successfully",
                "pr_id": pr_id,
                "scope_of_work": purchase_request.scope_of_work if purchase_request.scope_of_work else "",
                "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                "proc_plan": {
                    "id": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                    "name": purchase_request.procurement_plan_reference.name if purchase_request.procurement_plan_reference else ""
                } if purchase_request.procurement_plan_reference else {},
                "pr_date": purchase_request.created_at.strftime("%Y-%m-%d") if purchase_request.created_at else "",
                "pr_items": pr_item_list,
                "pr_attachments": pr_at_list,
                "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
                "uom": list(uom.values('unit', 'name')),
                "suppliers": list(suppliers.values('id', 'name')),
                "users": list(users.values('id', 'username', 'first_name', 'last_name')),
            }, safe=False)
    else:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        }, safe=False)

def get_create_cs(request, pr_id):

    print("get_create_cs pr_id: ", pr_id)
    # get proc plans
    proc_plans = ProcPlan.objects.all()
    username = request.user.username
    
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "proc_plans": proc_plans,
        "username": username,
        "pr_id": pr_id,
    })

def create(request):

    if request.method == "POST":
        tender_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")
        advert_file = request.FILES['advert']
        bid_document_file = request.FILES['advert']
        item_count = request.POST['item_count']
        rfq_no = request.POST['rfq_id']
        rfq = request.POST['rfq']
        scope = request.POST['scope_of_work']
        quantity = request.POST['quantity']
        rfq_date = request.POST['rfq_date']
        closing_date = request.POST['closing_date']
        closing_time = request.POST['closing_time_hour']
        pr_number = request.POST['pr_number']
        pr_date = request.POST['pr_date']
        date_tender_opened = request.POST['date_tender_opened']
        tender_adjudication_committee_date = request.POST['tender_adjudication_committee_date']
        supplier_name = request.POST['supplier_name']
        supplier_key = request.POST['supplier_key']
        bid_date = request.POST['bid_date']
        bid_no = request.POST['supplier[bid][0]']
        
        # store attachments
        advert_path = ""
        bid_document_path = ""
        try:
            if 'advert' in request.FILES:
                advert_file = request.FILES['advert']
                advert_path = 'uploads/finance/cs/adverts/' + \
                                  datetime.now().strftime("%Y%m%d%I%M%S%p") + advert_file.name
                save_file(advert_file, advert_path)
                
            if 'bid_document' in request.FILES:
                bid_document_file = request.FILES['bid_document']
                bid_document_path = 'uploads/finance/cs/bids/' + \
                                  datetime.now().strftime("%Y%m%d%I%M%S%p") + bid_document_file.name
                save_file(bid_document_file, bid_document_path)
        
        except Exception as ex:
            print("Error: ", ex)
        
        for i in range(0,int(item_count)):
            item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name]['+str(i)+']']
            quantity = request.POST['supplier[quantity]['+str(i)+']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement]['+str(i)+']']
            vat = request.POST['supplier[vat]['+str(i)+']']
            unit_price = request.POST['supplier[unit_price]['+str(i)+']']
            total_price = request.POST['supplier[total_price]['+str(i)+']']
            
            item = CSItems(
                cd_id = tender_id,
                item_id = item_id,
                item = description,
                required_qty = quantity,
                unit_of_measurement = unit_of_measurement,
            )
            item.save()
            
            supplier_id = ""
            if supplier_key:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
            supplier_query = Supplier(
                sup_id = supplier_id,
                supplier = supplier_name
            )
            supplier_query.save()
            
            bid = Bids(
                document_id = tender_id,
                item_id = item_id,
                sup_id = supplier_id,
                unit_price = unit_price,
                vat = vat,
                quoted_qty = quantity,
                bid_no = bid_no,
                quote_date = bid_date,
                rfq_no = rfq_no,
                total = total_price,
                bid_document = bid_document_path,
            )
            bid.save()
        
        cs_query = ComparativeSchedules(
            document_id = tender_id,
            rfq_date = rfq_date,
            scope_of_work = scope,
            closing_date = closing_date,
            closing_time = closing_time,
            rfq_no = rfq,
            advert = advert_path,
            date_created = date_tender_opened,
            pr_number = pr_number,
            pr_date = pr_date,
            tender_opened = date_tender_opened,
            tac_date = tender_adjudication_committee_date,
            region = "",
        )
        cs_query.save()
        
        # rfq_query = RFQUPDATE.objects.filter(document_id=rfq).first()
        # if rfq_query:
        #     rfq_query.tender_board = 'yes'
        #     rfq_query.save()
        
        if 'add_supplier' in request.POST:
            return redirect('add_supplier', tender_id=tender_id)
            
        return render(request, 'finance/comparative_schedules/cs_create.html', {
            "proc_plans": None,
        })
        
def save_comparative_schedule(request):

    try:
        
        cs_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")
        advert_files = request.FILES.getlist("advert", None)
        proc_ref = request.POST.get("proc_ref", "")
        print("proc plan: ", proc_ref)
        # check if proc ref has 'acc' prefix
        if not proc_ref.startswith("acc"):
            temp_proc_ref = "acc" + proc_ref
            proc_ref = temp_proc_ref
            
        proc_plan = ProcPlan.objects.filter(proc_ref=proc_ref).first()
        print("proc_plan: ", proc_plan)
        scope_of_work = request.POST.get("scope_of_work", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        # quantity = data['quantity']
        closing_date = request.POST.get("closing_date", "")
        closing_time = request.POST.get("closing_time", "")
        date_tender_opened = request.POST.get("date_tender_opened", "")
        tender_adjudication_committee_date = request.POST.get("tender_adjudication_committee_date", "")
        username = request.POST.get("username", "")
        
        # save advert file
        advert_path = ""
        try:
            if advert_files:
                advert_file = advert_files[0]
                advert_path = 'uploads/comparative/adverts/' + \
                                datetime.now().strftime("%Y%m%d%I%M%S%p") + advert_file.name
                print("Advert path: ", advert_path)
                save_file(advert_file, advert_path)
        except Exception as ex:
            print("Error: ", ex)
        
        # save cs details
        # fetch purchase request
        print("pr number: ", pr_number)
        pr = PurchaseRequest.objects.get(id=pr_number)
        print("PR: ", pr, pr_number, username)
        # fetch user
        user = UserProfile.objects.filter(username=username).first()
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules(
            cs_id = cs_id,
            pr_id_id = pr.id,
            scope_of_work = scope_of_work,
            closing_date = closing_date,
            closing_time = closing_time,
            advert = advert_path,
            pr_number = pr_number,
            pr_date = pr_date,
            ref_date = ref_date,
            proc_plan = proc_plan,
            cs_opened = date_tender_opened,
            tac_date = tender_adjudication_committee_date,
            created_by_id = user.id,
            section_id = None,
            region_id = None,
        )
        cs_query.save()
        
        return JsonResponse({
            "message": "Comparative Schedule saved successfully",
            "success": True,
            "cs_id": cs_id,
            "cs_owner": user.username if user else "",
            }, safe=False)
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Error saving Comparative Schedule",
            "error": str(ex),
            "success": False,
            }, safe=False)
   
def update_comparative_schedule(request):

    try:
        
        advert_files = request.FILES.getlist("advert", None)
        cs_id = request.POST.get("cs_id", "")
        plan_ref = request.POST.get("proc_ref", "")
        # proc_plan = data['proc_plan']
        proc_plan_ = ProcPlan.objects.filter(proc_ref=plan_ref).first()
        scope_of_work = request.POST.get("scope_of_work", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        # quantity = data['quantity']
        closing_date = request.POST.get("closing_date", "")
        closing_time = request.POST.get("closing_time", "")
        date_tender_opened = request.POST.get("date_tender_opened", "")
        tender_adjudication_committee_date = request.POST.get("tender_adjudication_committee_date", "")
        username = request.POST.get("username", "")
        
        # save advert file
        advert_path = ""
        try:
            if advert_files:
                advert_file = advert_files[0]
                advert_path = 'uploads/comparative/adverts/' + \
                                datetime.now().strftime("%Y%m%d%I%M%S%p") + advert_file.name
                print("Advert path: ", advert_path)
                save_file(advert_file, advert_path)
        except Exception as ex:
            print("Error: ", ex)
        
        # save cs details
        # fetch purchase request
        pr = PurchaseRequest.objects.filter(id=pr_number).first()

        # fetch user
        user = UserProfile.objects.filter(username=username).first()
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()

        if cs_query:
            clear_approvals(cs_id)
            print(scope_of_work)
            if scope_of_work:
                cs_query.scope_of_work = scope_of_work 
            print(closing_date)
            if closing_date:
                cs_query.closing_date = closing_date
            print(closing_time)
            if closing_time:
                cs_query.closing_time = closing_time
            print(advert_path)
            if advert_path:
                cs_query.advert = advert_path
            print(pr_number)
            if pr_number:
                cs_query.pr_number = pr_number
            print(pr_date)
            if pr_date:
                cs_query.pr_date = pr_date
            print(date_tender_opened)
            if date_tender_opened:
                cs_query.cs_opened = date_tender_opened
            print(tender_adjudication_committee_date)
            if tender_adjudication_committee_date:
                cs_query.tac_date = tender_adjudication_committee_date
            print(proc_plan_)
            if proc_plan_:
                cs_query.proc_plan = proc_plan_
            if ref_date:
                cs_query.ref_date = ref_date
            
            cs_query.save()
        else:
            print("ComparativeSchedule record not found with cs_id:", cs_id)
        
        return JsonResponse({
            "message": "Comparative Schedule saved successfully",
            "success": True,
            "cs_id": cs_id,
            }, safe=False)
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Error saving Comparative Schedule",
            "error": str(ex),
            "success": False,
            }, safe=False)

def update_pritem_ordered(request):
    
    cs_id = request.POST.get("cs_id", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    
    if cs_query:
        pr_item_id = request.POST.get("pr_id", "")
        csitems_data = json.loads(request.POST.get("json_data", "{}"))
        print("csitems_data: ", csitems_data)
        items = csitems_data.get("cs_items", [])
        print("items ", items, type(items))
        print("pr_item_id: ", pr_item_id)
        purchase_request = PurchaseRequest.objects.filter(id=pr_item_id).first()
        print("purchase request: ", purchase_request)

        for item in items:
            # check if item exists
            cs_item = CSItems.objects.filter(item_id=item['id'], cs_id=cs_query).first()
            if cs_item:
                cs_item.item_name = item['item_required']
                cs_item.quantity = item['quantity']
                cs_item.unit_of_measurement = item['unit_of_measurement']
                cs_item.save()
            else:
                cs_required_items = CSRequiredItems(
                    cs_id = cs_query,
                    item_id = item['id'],
                    item_name = item['item_required'],
                    quantity = item['quantity'],
                    unit_of_measurement = item['unit_of_measurement'],
                )
                cs_required_items.save()

        
        # set all items to ordered
        for item in items:
            print("item: ", item)
            pr_item = PrItem.objects.filter(item_required=item['item_required'], purchase_request=purchase_request).first()
            if pr_item:
                pr_item.ordered = True
                pr_item.save()
            else:
                return JsonResponse({
                    "message": "PR Item not found",
                    "success": False,
                    }, safe=False)
        

        return JsonResponse({
            "message": "PR Item updated successfully",
            "success": True,
            }, safe=False)
    else:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
def save_cs_bid(request):

    cs_id = request.POST.get("cs_id", "")
    bid_no = request.POST.get("bid_no", "")
    print("bid_no: ", bid_no)
    
    bid_docs = request.FILES.get("bid_document", None)
    bid_date = request.POST.get("bid_date", "")
    supplier_id = request.POST.get("supplier_id", "")
    supplier_name = request.POST.get("supplier_name", "")
    # get items json
    json_data = json.loads(request.POST.get("json_data", "{}"))
    print("json_data: ", json_data)
    items = json_data.get("bid_items", [])
    print("items ", items, type(items))
    
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
      
    supplier = Supplier.objects.filter(name=supplier_name).first()
    if not supplier:
        supplier_ = Supplier(
            name = supplier_name
        )
        supplier_.save()
        supplier = supplier_   
        
    # check if bid exists
    bid_query = Bids.objects.filter(cs_id=cs_query, sup_id=supplier, bid_no=bid_no).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = CSItems.objects.filter(item_id=bid.item_id).first()
            if item:
                item.delete()
            bid.delete()
            
    # save bids
    bid_doc_path = ""
    try:
        if bid_docs:
            bid_doc = bid_docs
            bid_doc_path = 'uploads/comparative/adverts/' + \
                            datetime.now().strftime("%Y%m%d%I%M%S%p") + bid_doc.name
            print("Advert path: ", bid_doc_path)
            save_file(bid_doc, bid_doc_path)
    except Exception as ex:
        print("Error: ", ex)
        
    for item in items:
        print("item: ", item)
        item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
        item_query = CSItems(
            cs_id = cs_query,
            item_id = item_id,
            item_name = item['item_required'],
            quantity = item['quantity'],
            unit_of_measurement = item['unit_of_measurement'],
        )
        item_query.save()    
        
        print("bid_no", bid_no)
        bid = Bids(
            cs_id = cs_query,
            item_id = item_query,
            sup_id = supplier,
            unit_price = item['unit_price'] if 'unit_price' in item else "",
            vat = item['vat'] if 'vat' in item else "",
            quoted_qty = item['quantity'] if 'quantity' in item else "",
            bid_no = bid_no,
            quote_date = bid_date,
            total = item['total_price'] if 'total_price' in item else "",
            bid_document = bid_doc_path,
        )
        bid.save()
        
    return JsonResponse({
        "message": "Bids saved successfully",
        "success": True,
    })

def delete_cs_bid(request):
    cs_id = request.POST.get("cs_id", "")
    supplier_name = request.POST.get("supplier_name", "")
    bid_no = request.POST.get("bid_count", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    supplier = Supplier.objects.filter(name=supplier_name).first()
    if not supplier:
        return JsonResponse({
            "message": "Supplier not found",
            "success": False,
            }, safe=False)
    
    # check if bid exists
    bid_query = Bids.objects.filter(cs_id=cs_query, sup_id=supplier).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = CSItems.objects.filter(item_id=bid.item_id).first()
            if item:
                item.delete()
            bid.delete()
            
    return JsonResponse({
        "message": "Bid deleted successfully",
        "success": True,
    })

def save_cs_compliance(request):

    cs_id = request.POST.get("cs_id", "")
    json_data = json.loads(request.POST.get("compliance", "{}"))
    print("json_data: ", json_data)
    compliances = json_data.get("compliance", [])
    print("items ", compliances, type(compliances))
    json_data_ = json.loads(request.POST.get("complianceRemarks", "{}"))
    print("json_data_: ", json_data_)
    compliance_remarks = json_data_.get("complianceRemarks", [])
    print("compliance_remarks ", compliance_remarks, type(compliance_remarks))
    
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
      
    # check if compliance exists
    compliance_query = CSCompliance.objects.filter(cs_id=cs_query).all()
    if compliance_query:
        clear_approvals(cs_id)
        for compliance in compliance_query:
            compliance.delete()
    
    for comp in compliances:
        print("comp: ", comp)
        supplier_name = comp['supplier_name'] if 'supplier_name' in comp else False
        payment_terms = comp['payment_terms'] if 'payment_terms' in comp else False
        bid_validity = comp['bid_validity'] if 'bid_validity' in comp else False
        delivery_period = comp['delivery_period'] if 'delivery_period' in comp else False
        technical_specifications = comp['technical_specifications'] if 'technical_specifications' in comp else False
        valid_tax_clearance = comp['valid_tax_clearance'] if 'valid_tax_clearance' in comp else False
        registered_with_praz = comp['registered_with_praz'] if 'registered_with_praz' in comp else False
        site_visit_done = comp['site_visit'] if 'site_visit' in comp else False
        samples_delivered = comp['samples_required'] if 'samples_required' in comp else False
        decision = comp['decision'] if 'decision' in comp else False
        remarks = comp['remarks'] if 'remarks' in comp else False
        
        supplier = Supplier.objects.filter(name=supplier_name).first()
        compliance_query = CSCompliance(
            cs_id = cs_query,
            supplier_id = supplier,
            payment_terms = payment_terms,
            bid_validity = bid_validity,
            delivery_period = delivery_period,
            technical_specifications = technical_specifications,
            valid_tax_clearance = valid_tax_clearance,
            registered_with_praz = registered_with_praz,
            site_visit_done = site_visit_done,
            samples_delivered = samples_delivered,
            decision = decision,
            remarks = remarks,
        )
        compliance_query.save()
    
    # check if compliance remarks exists
    compliance_remarks_query = CSComplianceRemarks.objects.filter(cs_id=cs_query).all()
    if compliance_remarks_query:
        for remark in compliance_remarks_query:
            remark.delete()
            
    for remark in compliance_remarks:
        supplier_name = remark['supplier_name'] if 'supplier_name' in remark else ""
        print("supplier_name: ", supplier_name, cs_query)
        supplier = Supplier.objects.filter(name=supplier_name).first()
        print("supplier: ", supplier)
        _remark = CSComplianceRemarks(
            cs_id = cs_query,
            supplier_id = supplier,
            remarks = remark['remarks'] if 'remarks' in remark else "",
        )  
        _remark.save()
        
    return JsonResponse({
        "message": "Compliance saved successfully",
        "success": True,
    })
    
def save_supplier(request):

    supplier_name = request.POST.get("supplier_name", "")
    
    supplier_query = Supplier.objects.filter(name=supplier_name).first()
    if not supplier_query:
        supplier_query = Supplier(
            name = supplier_name
        )
        supplier_query.save()
        
    return JsonResponse({
        "message": "Supplier saved successfully",
        "success": True,
    })
     
def save_cs_ranking(request):
    cs_id = request.POST.get("cs_id", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    # check if rankings exists
    ranking_query = Ranking.objects.filter(cs_id=cs_query).all()
    if ranking_query:
        clear_approvals(cs_id)
        for ranking in ranking_query:
            ranking.delete()
    # get bids
    bids = Bids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total'))
    compliant_bids = []
    for bid in bids:
        supplier = Supplier.objects.filter(id=bid['sup_id']).first()
        _compliance = CSCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier, decision=True).first()
        if _compliance:
            compliant_bids.append(bid)
    rankings = {bid['sup_id']: bid['total_sum'] for bid in compliant_bids}
    print("rankings: ", rankings)
    sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])
    print("sorted_rankings: ", sorted_rankings)
    rank = 1
    sorted_rankings_dict = dict(sorted_rankings)
    for supplier_id, total in sorted_rankings_dict.items():
        supplier = Supplier.objects.filter(id=supplier_id).first()
        remarks = ""
        decision = ""
        if rank == 1:
            decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of ZIG" + str(total) + " excluding VAT."
        ranking_query = Ranking(
            cs_id = cs_query,
            supplier_id = supplier,
            rank = rank,
            remarks = remarks,
            decision = decision,
            total = total,
        )
        ranking_query.save()
        rank += 1
        
    # get rankings
    rankings = Ranking.objects.filter(cs_id=cs_query).all()
    custom_rankings = []
    for ranking in rankings:
        supplier = ranking.supplier_id
        custom_rankings.append({
            "id": ranking.id,
            "supplier_name": supplier.name,
            "rank": ranking.rank,
            "remarks": ranking.remarks,
            "decision": ranking.decision,
            "total": ranking.total,
        })
        
    return JsonResponse({
        "message": "Ranking saved successfully",
        "success": True,
        "rankings": list(custom_rankings),
    })
    
def save_cs_committee(request):
    cs_id = request.POST.get("cs_id", "")
    json_data = json.loads(request.POST.get("committee", "{}"))
    committee = json_data.get("committee", [])
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    # check if committee exists
    for member in committee:
        # check if member exists
        # get member user profile
        member_profile = UserProfile.objects.filter(username=member['memberUserName']).first()
        if member_profile:
            committee_query = Committee.objects.filter(cs_id=cs_query, user=member_profile).first()
            if committee_query:
                clear_approvals(cs_id)
                committee_query.committee_position = member['memberPosition']
                committee_query.committee_date = datetime.now()
                committee_query.save()
            else:
                committee_query = Committee(
                    cs_id = cs_query,
                    user = member_profile,
                    committee_name = member['memberUserName'],
                    committee_position = member['memberPosition'],
                    committee_date = datetime.now(),
                )
            committee_query.save()
        
    return JsonResponse({
        "message": "Committee saved successfully",
        "success": True,
    })

def delete_cs_committee_member(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    print("username: ", username)
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = Committee.objects.filter(cs_id=cs_query, user=member_profile).first()
        print("committee_query: ", committee_query)
        if committee_query:
            clear_approvals(cs_id)
            committee_query.delete()
            return JsonResponse({
                "message": "Committee member deleted successfully",
                "success": True,
            })
        else:
            return JsonResponse({
                "message": "Committee member not found",
                "success": False,
            })
    else:
        return JsonResponse({
            "message": "Committee member not found",
            "success": False,
        })

def approve_cs_committee(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    print("username: ", username)
    approval = request.POST.get("approval", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = Committee.objects.filter(cs_id=cs_query, user=member_profile).first()
        if committee_query:
            committee_query.committee_approval = approval
            committee_query.committee_date = datetime.now()
            committee_query.save()
            print("approval: ", approval)
            return JsonResponse({
                "message": "Committee member approved successfully",
                "success": True,
                "data": {
                    "committee_date": committee_query.committee_date,
                    "committee_status": committee_query.committee_status,
                    "committee_fullname": member_profile.first_name + " " + member_profile.last_name,
                    "committee_approval": approval,
                }
            })
        else:
            return JsonResponse({
                "message": "Committee member not found",
                "success": False,
            })
    else:
        return JsonResponse({
            "message": "Committee member not found",
            "success": False,
        })

def approve_cs(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    approval = request.POST.get("approval", "")
    justification = request.POST.get("justification", "")
    role = request.POST.get("role", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    user = UserProfile.objects.filter(username=username).first()
    if user:
        if role == "general_manager":
            gm_approval = CSApproval(
                cs_id = cs_query,
                user = user,
                approver_role = role,
                approval = approval,
                justification = justification,
                approval_date = datetime.now(),
                created_at = datetime.now(),
            )
            gm_approval.save()
            
            return JsonResponse({
                "message": "GM approval saved successfully",
                "success": True, 
                "role": role,
                "approval": approval,           
                "gm_approval": {
                    "id": gm_approval.id,
                    "approver": gm_approval.user.username if gm_approval.user else "",
                    "approver_name": gm_approval.user.first_name + " " + gm_approval.user.last_name if gm_approval.user else "",
                    "approver_role": gm_approval.approver_role,
                    "approval": gm_approval.approval,
                    "justification": gm_approval.justification,
                    "approval_date": gm_approval.approval_date,
                }
            })
        elif role == "finance_manager":
            fm_approval = CSApproval(
                cs_id = cs_query,
                user = user,
                approver_role = role,
                approval = approval,
                justification = justification,
                approval_date = datetime.now(),
                created_at = datetime.now(),
            )
            fm_approval.save()
        
            return JsonResponse({
                "message": "FM approval saved successfully",
                "success": True, 
                "role": role,
                "approval": approval,          
                "fm_approval": {
                    "id": fm_approval.id,
                    "approver": fm_approval.user.username if fm_approval.user else "",
                    "approver_name": fm_approval.user.first_name + " " + fm_approval.user.last_name if fm_approval.user else "",
                    "approver_role": fm_approval.approver_role,
                    "approval": fm_approval.approval,
                    "justification": fm_approval.justification,
                    "approval_date": fm_approval.approval_date,
                }
            })
        else:
            return JsonResponse({
                "message": "User Role not found",
                "success": False,
            })
    else:
        return JsonResponse({
            "message": "User not found",
            "success": False,
        })

def save_cs_decision(request):
    cs_id = request.POST.get("cs_id", "")
    committee_id = request.POST.get("committee_id", "")
    committee_decision = request.POST.get("committee_decision", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    committee_query = Committee.objects.filter(cs_id=cs_query, id=committee_id).first()
    if committee_query:
        if committee_decision == "approve":
            committee_query.committee_status = True
            committee_query.committee_date = datetime.now()
            committee_query.save()
        elif committee_decision == "reject":
            committee_query.committee_status = False
            committee_query.committee_date = datetime.now()
            committee_query.save() 
            
    return JsonResponse({
        "message": "Committee decision saved successfully",
        "success": True,
    })   
        
def cs_add_supplier(request, cs_id):
    
    if request.method == 'GET':
        
        # tender_id = request.GET['tender_id']
        # get tender bids supplier items
        tender = ComparativeSchedules.objects.filter(document_id=tender_id).first()
        proc_plan = ProcPlan.objects.filter(proc_ref=tender.pr_number).first()
        bids = Bids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})
            
        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Supplier.objects.filter(sup_id=bid.sup_id).first()
                    item = CSItems.objects.filter(item_id=bid.item_id).first()

                    if supplier:
                        print(supplier, supplier.supplier, supplier.sup_id)
                        supplier_id = supplier.sup_id
                        supplier_name = supplier.supplier
                        bids_dict[str(i)].append({
                            "bid_no": int(bid.bid_no),
                            "supplier_name": supplier_name,
                            "supplier_id": supplier_id,
                            "bid": bid,
                            "item": item,
                        })
                
        # get proc plans
        proc_plans = ProcPlan.objects.all()
        suppliers = Suppliers.objects.all()
        supplier_list = {}
        for supplier in suppliers:
            supplier_list.update({supplier.sup_id:supplier.supplier})
            
        suppliers_json = json.dumps(supplier_list, default=str)
        
        return render(request, 'finance/tenders/tenders_add_supplier.html', {
            "proc_plans": proc_plans,
            "suppliers": suppliers_json,
            "tender": tender,
            "bids_items": bids_dict,
            "next_bid": len(bids_dict)+1,
            "proc_plan": proc_plan
        })
    elif request.method == "POST":
        print("request: ", request.POST)
        print(i)
        tender_id = request.POST['tender_id']
        item_count = request.POST['item_count']
        rfq_no = request.POST['rfq_id']
        supplier_name = request.POST['supplier_name']
        supplier_id = request.POST['supplier_key']
        supplier_key = request.POST['supplier_key']
        bid_date = request.POST['bid_date']
        bid_no = request.POST['supplier[bid][0]']
        # store attachments
        bid_document_path = ""
        try:
                
            if 'bid_document' in request.FILES:
                bid_document_file = request.FILES['bid_document']
                bid_document_path = 'uploads/finance/cs/bids/' + \
                                  datetime.now().strftime("%Y%m%d%I%M%S") + bid_document_file.name
                save_file(bid_document_file, bid_document_path)
        
        except Exception as ex:
            print("Error: ", ex)
        
        for i in range(0,int(item_count)):
            item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name]['+str(i)+']']
            quantity = request.POST['supplier[quantity]['+str(i)+']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement]['+str(i)+']']
            vat = request.POST['supplier[vat]['+str(i)+']']
            unit_price = request.POST['supplier[unit_price]['+str(i)+']']
            total_price = request.POST['supplier[total_price]['+str(i)+']']
            
            item = CSItems(
                document_id = tender_id,
                item_id = item_id,
                item = description,
                required_qty = quantity,
                unit_of_measurement = unit_of_measurement,
                rfq_no = rfq_no,
            )
            item.save()
            
            supplier_id = ""
            if supplier_id:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
            supplier_query = Suppliers(
                sup_id = supplier_id,
                supplier = supplier_name
            )
            supplier_query.save()
            
            bid = Bids(
                document_id = tender_id,
                item_id = item_id,
                sup_id = supplier_id,
                unit_price = unit_price,
                vat = vat,
                quoted_qty = quantity,
                bid_no = bid_no,
                quote_date = bid_date,
                rfq_no = rfq_no,
                total = total_price,
                bid_document = bid_document_path,
            )
            bid.save()
        
        if 'add_supplier' in request.POST:
            return redirect('add_supplier', tender_id=tender_id)
            
        return render(request, 'finance/tenders/tenders_create.html', {
            "proc_plans": proc_plans,
            "suppliers": suppliers_json
        })
      
def cs_compliance_table(request, cs_id):
    
    if request.method == 'GET':
        tender_id = tender_id
        tender = ComparativeSchedules.objects.filter(document_id=tender_id).first()
        bids = Bids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})
            
        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Suppliers.objects.filter(sup_id=bid.sup_id).first()
                    item = CSItems.objects.filter(item_id=bid.item_id).first()
                    
                    print(supplier, supplier.supplier, supplier.sup_id)
                    supplier_id = supplier.sup_id
                    supplier_name = supplier.supplier
                    bids_dict[str(i)].append({
                        "bid_no": int(bid.bid_no),
                        "supplier_name": supplier_name,
                        "supplier_id": supplier_id,
                        "bid": bid,
                    })
    elif request.method == 'POST':
        document_id = request.POST['document_id']
        rfq_no = request.POST['rfq_no']
        bid_count = request.POST['bid_count']
        
        # get compliance table values
        for i in range(1,bid_count):
            supplier_id = request.POST['supplier_id'+i+'']
            payment_terms = request.POST['payment_terms'+i+'']
            bid_validity = request.POST['bid_validity'+i+'']
            delivery_period = request.POST['delivery_period'+i+'']
            technical_specifications = request.POST['technical_specifications'+i+'']
            valid_tax_clearance = request.POST['valid_tax_clearance'+i+'']
            registered_with_praz = request.POST['registered_with_praz'+i+'']
            site_visit_done = request.POST['site_visit_done'+i+'']
            samples_delivered = request.POST['samples_delivered'+i+'']
            decision = request.POST['decision'+i+'']
            remarks = request.POST['remarks'+i+'']
            
            # insert into compliance table
            tender_compliance = CSCompliance(
                document_id = document_id,
                supplier_id = supplier_id,
                rfq_no = rfq_no,
                payment_terms = payment_terms,
                bid_validity = bid_validity,
                delivery_period = delivery_period,
                technical_specifications = technical_specifications,
                valid_tax_clearance = valid_tax_clearance,
                registered_with_praz = registered_with_praz,
                site_visit_done = site_visit_done,
                samples_delivered = samples_delivered,
                decision = decision,
                remarks = remarks,
            )
            tender_compliance.save()
            
        return redirect('tender_compliance', tender_id=document_id)


    return render(request, 'finance/comparative_schedules/cs_compliance_table.html', {"bids_items": bids_dict})
