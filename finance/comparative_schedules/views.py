import base64
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from django.db.models import Sum
from .models import *
from it.users.models import *
from finance.purchase_request.models import ProcurementPlanReference, PurchaseRequest, PrItem, Attachment, UnitOfMeasurement
from ACE2.models import Ace2
from finance.comparative_schedules.models import *
from django.db.models import Q, Exists, OuterRef, Count, F
import pandas as pd
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required

APP_NAME = "comparative_schedule"

def debug_time(request):
    system_time = datetime.now()
    aware_system_time = timezone.make_aware(system_time, timezone.get_default_timezone())
    django_time = timezone.now()
    
    current_timezone = timezone.get_current_timezone_name()
    django_time_utc = timezone.now()
    local_time = django_time_utc.astimezone(timezone.get_current_timezone())
    
    return HttpResponse(f"System Time: {system_time}<br>"
                        f"Aware System Time: {aware_system_time}<br>"
                        f"Django Time: {django_time}<br>"
                        f"Current Timezone: {current_timezone}<br>"
                        f"Django Time UTC: {django_time_utc}<br>"
                        f"Local Time: {local_time}<br>")

@login_required
def import_old_rfq(request):
    tender_csv = 'tender.csv'
    rfq_csv = 'rfq.csv'
    bid_update_csv = 'bid_update.csv'
    bids_csv = 'bids.csv'
    items_csv = 'items.csv'
    required_items_csv = 'required_items.csv'
    suppliers_csv = 'suppliers.csv'
    
    # Read the tender CSV file using pandas
    tender_data = pd.read_csv(tender_csv)
    print(tender_data.head())
    rfq_data = pd.read_csv(rfq_csv)
    print(rfq_data.head())
    bid_update_data = pd.read_csv(bid_update_csv)
    print(bid_update_data.head())
    bids_data = pd.read_csv(bids_csv)
    print(bids_data.head())
    items_data = pd.read_csv(items_csv)
    print(items_data.head())
    required_items_data = pd.read_csv(required_items_csv)
    print(required_items_data.head())
    suppliers_data = pd.read_csv(suppliers_csv)
    print(suppliers_data.head())
    
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
        try:
            section = Sections.objects.filter(code=row['section_code']).first() if row['section_code'] else None
            cost_center = CostCenter.objects.filter(id=row['section_code']).first() if row['section_code'] else None
            proc_ref = row["proc_ref"]
            if proc_ref.startswith("acc"):
                proc_ref = proc_ref.lstrip('acc')
            procurement_plan = ProcurementPlanReference.objects.filter(id=proc_ref).first() if proc_ref else None
            created_by = None
            # print("created by: ", row['created_by'])
            if row['created_by']:
                # print("using User")
                created_by = UserProfile.objects.filter(username=row['created_by']).first()
            if created_by == None: 
                created_by = UserProfile.objects.filter(username='ze123').first()
                # print("using No User")
            # ace = Ace2.objects.filter(ace=row['ace']).first() if row['ace'] else None
            # print("created by: ", created_by, datetime.strptime(row['date_created'], "%Y-%m-%d %H:%M:%S"))
            dc = timezone.make_aware(datetime.strptime(row['date_created'], "%Y-%m-%d %H:%M:%S")) if row['date_created'] != '0000-00-00 00:00:00' else None
            pr = PurchaseRequest(
                pr_no = row['rfq_number'],
                section = section,
                cost_center = cost_center,
                procurement_plan_reference = procurement_plan,
                requested_by = created_by,
                created_at = dc,
                ace = None,
                scope_of_work = row['scope_of_work'],
            )
            pr.save()
            
            # att_path = 'uploads/finance/pr/attachments/' + row['specifications'].split('/')[-1] if row['specifications'] else ""

            attachments = Attachment(
                file = row['specifications'],
                purchase_request = pr,
            )
            attachments.save()
            
        except Exception as ex:
            print("Error: ", ex)    
            
    # # save required items
    try:
        for index, row in required_items_data.iterrows():
            document_id = row['document_id']
            filtered_rows = rfq_data[rfq_data['document_id'] == document_id]
            if not filtered_rows.empty:
                pr_row = filtered_rows.iloc[0]
            else:
                pr_row = None
            
            if pr_row is not None:
                pr_no = pr_row['rfq_number']
                pr = PurchaseRequest.objects.filter(pr_no=pr_no).first()

                uom = None
                if row['uom'] == "None":
                    print("uom is None")
                if row['uom'] is not None:
                    _uom = row['uom']
                    if row['uom'] == "kgs":
                        _uom = "Kilogram"
                    elif row['uom'] == "litres":
                        _uom = "Liter"
                    elif row['uom'] == "metres":
                        _uom = "Meter"
                    uom = UnitOfMeasurement.objects.filter(name=_uom).first() 

                else: 
                    uom = UnitOfMeasurement.objects.filter(name='each').first()

                pr_item = PrItem(
                    item_required = row['item_required'],
                    quantity = row['qty'],
                    unit_of_measurement = uom,
                    purchase_request = pr,
                )
                pr_item.save()
    except Exception as ex:
        print("error: ", ex)
    
    # # save comperative schedules
    cs_df = pd.DataFrame(columns=['document_id', 'pr_number', 'status', 'message'])
    try:
        # initialize dataframe that records all failied and successfull comperative schedules
        for index, tender_row in tender_data.iterrows():
            cs_id = tender_row['document_id']
            pr_number = tender_row['rfq_no']
            print("pr_number: ", pr_number)
            if pr_number:
                pr = PurchaseRequest.objects.filter(pr_no=pr_number).first()
                if not pr:
                    pr = PurchaseRequest.objects.filter(pr_no="10000000").first()
                    print("pr 001: ", pr)
                if pr:
                    print("pr: ", pr)
                    _proc_plan = tender_row['pr_number']
                    proc_plan = ProcPlan.objects.filter(proc_ref=_proc_plan).first()
                    tender_update = bid_update_data[bid_update_data['document_id'] == cs_id]
                    if not tender_update.empty:
                        tender_update_row = tender_update.iloc[0]
                    else:
                        tender_update_row = None
                    if tender_update_row is not None:
                        created_by = UserProfile.objects.filter(username=tender_update_row['user3']).first()
                        if created_by == None: 
                            created_by = UserProfile.objects.filter(username='ze123').first()
                        print("tender_row: ", tender_row['region'])
                        region = None
                        if tender_row['region']:
                            region_name = str(tender_row['region']).upper()
                            region = Regions.objects.filter(region=region_name).first()
                        else:
                            region = Regions.objects.filter(id=1).first()
                        try:
                            currency = Currency.objects.filter(currency='ZWL').first()
                            cs_query = ComparativeSchedules(
                                cs_id = cs_id,
                                pr_id = pr,
                                proc_plan = proc_plan,
                                scope_of_work = tender_row['scope_of_work'],
                                currency = currency,
                                closing_date = tender_row['closing_date'],
                                closing_time = tender_row['closing_time'],
                                advert = tender_row['advert'],
                                pr_number = pr_number,
                                pr_date = tender_row['pr_date'],
                                ref_date = tender_row['pr_date'],
                                cs_opened = tender_row['tender_opened'],
                                tac_date = tender_row['tac_date'],
                                created_by = created_by,
                                region = region,
                                created_at = tender_row['pr_date'],
                            )
                            cs_query.save()
                            cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr.id], 'status': ['Success'], 'message': ['Success']})], ignore_index=True)
                        except Exception as ex:
                            print("Error: ", ex)
                            cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': [ex]})], ignore_index=True)
                    else:
                        cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['Tender Update not found']})], ignore_index=True)
                else:
                    cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Object not found']})], ignore_index=True)
            else:
                cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Number not found']})], ignore_index=True)
        cs_df.to_csv('cs_df.csv')
        print("cs_df: ", cs_df)
    
    except Exception as ex:
        print("Error: ", ex)
        
    # # save bids
    
    try:
        item_df = pd.DataFrame(columns=['document_id', 'item_id', 'sup_id', 'status', 'message'])
        for index, row in bids_data.iterrows():
            cs_id = row['document_id']
            sup_id = row['sup_id']
            item_id	= row['item_id']
            unit_price = row['unit_price']	
            vat = row['vat']
            quoted_qty = row['quoted_qty']
            bid_no = row['bid_no']
            quote_date = row['quote_date']
            rfq_no = row['rfq_no']
            total = row['total']
            bid_document = row['bid_document']
            print("cs_id: ", cs_id)
            cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
            print("cs_query: ", cs_query)
            if cs_query:
                current_supplier = suppliers_data[suppliers_data['sup_id'] == sup_id]
                supplier = None
                if not current_supplier.empty:
                    current_supplier_row = current_supplier.iloc[0]
                    supplier_name = current_supplier_row['supplier']
                    if supplier_name and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A":
                        supplier = Supplier.objects.get_or_create(name=supplier_name).first()
                    
                else:
                    item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [""], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Supplier Not Found']})], ignore_index=True)
                
                if supplier:
                    current_item = items_data[items_data['item_id'] == item_id]
                    if not current_item.empty:
                        current_item_row = current_item.iloc[0]
                        item_name = current_item_row['item']
                        quantity = current_item_row['required_qty']
                        unit_of_measurement = current_item_row['unit_of_measurement']
                        item_query = CSItems(
                            cs_id = cs_query,
                            item_id = item_id,
                            item_name = item_name,
                            quantity = quantity,
                            unit_of_measurement = unit_of_measurement,
                        )
                        item_query.save()    
                    
                        print("bid_no", bid_no)
                        bid = Bids(
                            cs_id = cs_query,
                            item_id = item_query,
                            sup_id = supplier,
                            unit_price = unit_price,
                            vat = vat,
                            quoted_qty = quoted_qty,
                            bid_no = bid_no,
                            quote_date = quote_date,
                            total = total,
                            bid_document = bid_document,
                        )
                        bid.save()
                        item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['SUCCESS'], 'message': ['SUCCESS']})], ignore_index=True)
                    else:
                        item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Item Not Found']})], ignore_index=True)
                else:
                    item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['DB Supplier Not Found']})], ignore_index=True)
            else:
                item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Schedule Not Found']})], ignore_index=True)
    except Exception as ex:
        print("Error: ", ex)          
    
    item_df.to_csv('item_df.csv')
    
    # save bid update
    other_df = pd.DataFrame(columns=['document_id', 'sup_id', 'model', 'status', 'message'])
    try:
        for index, row in bid_update_data.iterrows():
            cs_id = row['document_id']
            cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
            if cs_query:
                # reason1 = row['reason1']
                # reason2 = row['reason2']
                # reason3 = row['reason3']
                for i in range(1, 30):
                    
                    supplier_name = row[f'supplier{i}'] if f'supplier{i}' in row else None	
                    payment_terms = row[f'payment_terms{i}'] if f'payment_terms{i}' in row else ""
                    bid_validity = row[f'bid_validity{i}'] if f'bid_validity{i}' in row else ""
                    delivery_period = row[f'delivery_period{i}'] if f'delivery_period{i}' in row else ""	
                    technical_specifications = row[f'technical_specifications{i}'] if f'technical_specifications{i}' in row else ""	
                    valid_tax_clearance = row[f'valid_tax_clearance{i}'] if f'valid_tax_clearance{i}' in row else ""	
                    registered_with_praz = row[f'registered_with_praz{i}'] if f'registered_with_praz{i}' in row else ""	
                    tax_status = row[f'tax_status{i}'] if f'tax_status{i}' in row else ""
                    site_visit_done = row[f'site_visit_done{i}'] if f'site_visit_done{i}' in row else ""	
                    samples_delivered = row[f'samples_delivered{i}'] if f'samples_delivered{i}' in row else ""
                    decision = row[f'decision{i}'] if f'decision{i}' in row else ""
                    total = row[f'total{i}'] if f'total{i}' in row else ""
                    remarks = row[f'remarks{i}'] if f'remarks{i}' in row else ""
                    
                    if supplier_name and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A" and supplier_name != "N/A":
                        supplier = Supplier.objects.filter(name=supplier_name).first()
                        if supplier and supplier != "" and supplier != " " and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A" and supplier_name != "N/A":
                            Supplier.objects.get_or_create(
                                name = supplier_name
                            )
                        
                        if supplier:
                            compliance_query = CSCompliance(
                                cs_id = cs_query,
                                supplier_id = supplier,
                                payment_terms = True if payment_terms == "on" else False,
                                bid_validity = True if bid_validity == "on" else False,
                                delivery_period = True if delivery_period == "on" else False,
                                technical_specifications = True if technical_specifications == "on" else False,
                                valid_tax_clearance = True if valid_tax_clearance == "on" else False,
                                registered_with_praz = True if registered_with_praz == "on" else False,
                                site_visit_done = True if site_visit_done == "on" else False,
                                samples_delivered = True if samples_delivered == "on" else False,
                                decision = True if decision == "on" else False,
                                remarks = remarks if remarks and remarks != "nan" else "",
                            )
                            compliance_query.save()
                            
                            _remark = CSComplianceRemarks(
                                cs_id = cs_query,
                                supplier_id = supplier,
                                remarks = remarks if remarks and remarks != "nan" else "",
                            )  
                            _remark.save()
                            other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Successs'], 'message': ['SUCCESS']})], ignore_index=True) 
                            
                        else:
                            other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Failed'], 'message': ['DB Supplier not found']})], ignore_index=True) 
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Failed'], 'message': ['Supplier not found']})], ignore_index=True) 
                
                # save ranking
                try:
                    for i in range(1, 6):
                        rank_supplier = row[f'ranking{i}'] if f'ranking{i}' in row else ""
                        if rank_supplier and rank_supplier != "None" and rank_supplier != "nan" and rank_supplier != "N/A":
                            supplier = Supplier.objects.filter(name=rank_supplier).first()
                            
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
                            # search dict for supplier and total
                            total = 0
                            for key, value in sorted_rankings_dict.items():
                                if key == supplier.id:
                                    total = value
                                    break
                            
                            if i == 1:
                                decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(total) + " excluding VAT."
                            ranking_query = Ranking(
                                cs_id = cs_query,
                                supplier_id = supplier,
                                rank = i,
                                remarks = "",
                                decision = decision,
                                total = total,
                            )
                            ranking_query.save()
                            print("ranking_query: ", ranking_query)
                        else:
                            print("Ranking Supplier not found")
                    
                except Exception as ex:
                    print("Error: ", ex)        
                # save committee
                for i in range(1,10):
                    username = row[f'user{i}'] if f'user{i}' in row else None
                    status = row[f'status_{i}'] if f'status_{i}' in row else None
                    approved_at = row[f'date_{i}'] if f'date_{i}' in row else None
                    position = ""
                    if i == 1:
                        position = "Chairman"
                    elif i == 2:
                        position = 'Finance'
                    elif i == 3:
                        position = 'Procurement'
                    elif i == 4:
                        position = 'User'
                    else:
                        position = 'Other'
                        
                    if status == 1:
                        status = "Approved"
                    elif status == 2:
                        status = "Rejected"
                    else:
                        status = ""
                    
                    # check if committee exists
                    if username:
                        # check if member exists
                        # get member user profile
                        member_profile = UserProfile.objects.filter(username=username).first()
                        if member_profile:
                            committee_query = Committee(
                                cs_id = cs_query,
                                user = member_profile,
                                committee_name = username,
                                committee_position = position,
                                committee_approval = status,
                                committee_date = timezone.make_aware(datetime.strptime(approved_at, "%Y-%m-%d %H:%M:%S")) if approved_at != '0000-00-00 00:00:00' else None
                            )
                            committee_query.save()
                            other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
                        else:
                            other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Failed'], 'message': ['member profile empty']})], ignore_index=True)
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["Committee"], 'status': ['Failed'], 'message': ['username empty']})], ignore_index=True) 
                
                finance_user = row['finance_user']
                finance_date = row['finance_date']
                finance_status = row['finance_status']
      
                if finance_status == 1:
                    finance_status = "Approved"
                elif finance_status == 2:
                    finance_status = "Rejected"
                else:
                    finance_status = ""
                
                if finance_user:
                    finance_profile = UserProfile.objects.filter(username=finance_user).first()
                    if finance_profile:
                        finance_query = CSApproval(
                            cs_id = cs_query,
                            user = finance_profile,
                            approver_role = "finance_manager",
                            approval = finance_status,
                            justification = "",
                            approval_date = timezone.make_aware(datetime.strptime(finance_date, "%Y-%m-%d %H:%M:%S")) if finance_date != '0000-00-00 00:00:00' else None,
                        )
                        finance_query.save()
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['DB finance_user empty']})], ignore_index=True)
                else:
                    other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['finance_user empty']})], ignore_index=True)
                
                gm_user = row['gm_user']
                gm_date = row['gm_date']
                gm_status = row['gm_status']
      
                if gm_status == 1:
                    gm_status = "Approved"
                elif gm_status == 2:
                    gm_status = "Rejected"
                else:
                    gm_status = ""
                
                if gm_user:
                    gm_profile = UserProfile.objects.filter(username=gm_user).first()
                    if gm_profile:
                        gm_query = CSApproval(
                            cs_id = cs_query,
                            user = gm_profile,
                            approver_role = "general_manager",
                            approval = gm_status,
                            justification = "",
                            approval_date = timezone.make_aware(datetime.strptime(gm_date, "%Y-%m-%d %H:%M:%S")) if gm_date != '0000-00-00 00:00:00' else None,
                        )
                        gm_query.save()
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Success'], 'message': ['SUCCESS GM']})], ignore_index=True)
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['GM DB finance_user empty']})], ignore_index=True)
                else:
                    other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['GM finance_user empty']})], ignore_index=True)
            else:
                print("cs not found")
                other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [""], 'model': ["ComparativeSchedules"], 'status': ['Failed'], 'message': ['Schedule not found']})], ignore_index=True)

    except Exception as ex:
        print("Error: ", ex)   
    
    other_df.to_csv('other_df.csv')    
      
    return JsonResponse({
        "success": True,
        "message": "Data imported successfully",
        # "data": other_df.to_json()
        # "data": cs_df.to_json()
        # "data": item_df.to_json()
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
            # approval.approval_date = None
            approval.save()
            
    return True

def getUserFMGMRoles(user):
    print("user: ", user.username, user.id  )
    fm_role, gm_role, procurement_role = False, False, False
    for role in user.roles.all():
        print("role id:", role.id)
        user_ace_role_ = Roles.objects.filter(id=role.id).first() if role.id else None

        if user_ace_role_.application == APP_NAME:
            if user_ace_role_.role == "check":
                fm_role = True
            if user_ace_role_.role == "approve":
                gm_role = True
            if user_ace_role_.role == "procurement":
                procurement_role = True
    
    return fm_role, gm_role, procurement_role

def notify_user(user_, msg, notification_type, url, id):
            
        Notification.objects.create(
            user=user_,
            message=msg,
            notification_type=notification_type,
            notification_id=id,
            url=url,
            created_at=datetime.now(),
        )
        
        return True
 
def ms_exchange():
    # Set up the EWS connection
    ews = pyexchange.ExchangeService('https://example.com/EWS/Exchange.asmx')

    # Authenticate with the Exchange server
    ews.authenticate('username', 'password')

    # Get the inbox folder
    inbox = ews.get_folder('inbox')

    # Get the emails in the inbox
    emails = inbox.get_items()

    # Loop through the emails and print the subject
    for email in emails:
        print(email.subject)
 
def notification_update(user, id):
    notification = Notification.objects.filter(user=user, notification_id=id).first()
    if notification:
        notification.is_read = True
        notification.save()
    return True

@login_required    
def get_comperative_schedules(request):
    
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user.username, user.id)
    
    fm_role, gm_role, procurement_role = False, False, False
    
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)
    print("roles ,,,, : ", fm_role, gm_role, procurement_role)

    if fm_role == True:
        return redirect('/comperative_schedule/pending_fm_approval')
    elif gm_role == True:
        return redirect('/comperative_schedule/pending_gm_approval')
    elif procurement_role == True:
        return redirect('/comperative_schedule/your_schedules')
    else:
        return redirect('/comperative_schedule/pending_commitee')

@login_required
def your_comperative_schedules(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)

    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,})

@login_required
def get_all_schedules(request):
    
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    
    print("roles: ", fm_role, gm_role)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    return render(request, user_page, { "fm_role": fm_role, "gm_role": gm_role, "procurement_role": procurement_role,})

@login_required
def get_pending_committee(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
        
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)   
        
    print("roles: ", fm_role, gm_role)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role})

@login_required
def get_pending_gm_approval(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role})

@login_required
def get_pending_fm_approval(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role})


def get_your_schedules(user_id, search_value=None, column_name=None):
    
    cs = ComparativeSchedules.objects.filter(
        created_by_id=user_id,
    ).all()

    # Filter based on search value
    if search_value:
                cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_pending_committee_table(user_id, search_value=None, column_name=None):

    print("user id: ", user_id)
    # fetch schedules if user exists in the committee and has not yet approved
    cs = ComparativeSchedules.objects.filter(
        Q(committee__committee_approval=None) | Q(committee__committee_approval=""),
        Q(committee__user_id=user_id)
    ).all()

    # Filter based on search value
    if search_value:
        cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_finance_manager(search_value=None, column_name=None):
    
    cs = ComparativeSchedules.objects.annotate(
        approved_count=Count('committee', filter=Q(committee__committee_approval="Approved")),
        not_approved_count=Count('committee', filter=Q(committee__committee_approval="")),
        rejected_count=Count('committee', filter=Q(committee__committee_approval="Rejected")),
        committee_count=Count('committee')
    ).filter(
        approved_count=F('committee_count'),
        committee_count__gt=2,
        not_approved_count=0,
        rejected_count=0,
        csapproval__approval=None
    ).distinct()

    # Filter based on search value
    if search_value:
                cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_general_manager(search_value=None, column_name=None):
    # fetch all pending approvals
    cs = ComparativeSchedules.objects.annotate(
        all_approved=Exists(
            Committee.objects.filter(
                cs_id=OuterRef('pk'),
                committee_approval="Approved"
            )
        ),
        any_not_approved=Exists(
            Committee.objects.filter(
                cs_id=OuterRef('pk'),
                committee_approval="Approved"
            )
        ),
        gm_approved=Exists(
            CSApproval.objects.filter(
                cs_id=OuterRef('pk'),
                approver_role="general_manager",
                approval="Approved"
            )
        ),
    ).filter(
        all_approved=True,
        any_not_approved=True,
        gm_approved=False,
        csapproval__approver_role="finance_manager",
        csapproval__approval="Approved"
    ).distinct()
    
    # Filter based on search value
    if search_value:
                cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_all_schedules_table(search_value=None, column_name=None, start=0, length=10):
    cs = ComparativeSchedules.objects.all()
    
    # Filter based on search value
    if search_value:
        cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def add_details(cs):
    cs_list = []
    
    for c in cs:
        committee_approval = ""
        gm_approval = None
        fm_approval = None
        committee = Committee.objects.filter(
                cs_id=c.id
        ).all()
        
        if len(committee) > 0:            
            committee_approved = all([c.committee_approval == "Approved" for c in committee])
            if committee_approved:
                committee_approval = "Approval Complete"
                fm_approval = CSApproval.objects.filter(
                    cs_id=c,
                    approver_role="finance_manager",
                ).first()
                    
                gm_approval = CSApproval.objects.filter(
                    cs_id=c,
                    approver_role="general_manager",
                ).first()
            else:
                committee_approval = "Pending"
                fm_approval = None
                gm_approval = None
            
                committee_rejected = Committee.objects.filter(
                cs_id=c,
                    committee_approval="Rejected"
                ).exists()

                if committee_rejected:
                    committee_approval = "Rejected"
                
                committee_pending = Committee.objects.filter(
                    cs_id=c,
                    committee_approval__in=["", None]
                ).exists()

                if committee_pending:
                    committee_approval = "Pending"
        else:
            committee_approval = "Pending"
            fm_approval = None
            gm_approval = None
            
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
            "committee_approval": committee_approval,
            "gm_approval": gm_approval.approval if gm_approval else "Pending",
            "fm_approval": fm_approval.approval if fm_approval else "Pending",
            "section": section.section if section else "",
            "region": region.region if region else "",
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
        })

    return cs_list

def datatable_data(request, view):
    
    user_id = request.user.id
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    length = int(request.GET.get('length', default=10))
    search_value = request.GET.get('search[value]', default='')

    # Sorting
    order_column = request.GET.get('order[0][column]')
    order = request.GET.get('order[0][dir]')
    column_name = ""
    if order_column:
        column_name = request.GET.get(f'columns[{order_column}][data]')
        if order == 'desc':
            column_name = f'-{column_name}'

    # Fetch your data from the
    print("view: ", view) 
    data = []
    if view == "your_schedules":
        print("your schedules ...")
        data = get_your_schedules(user_id, search_value, column_name)
    elif view == "pending_committee":
        print("pending_committee schedules ...", user_id)
        data = get_pending_committee_table(user_id, search_value, column_name)
    elif view == "pending_fm":
        print("pending_fm schedules ...")
        data = get_finance_manager(search_value, column_name)
    elif view == "pending_gm":
        print("pending_gm schedules ...")
        data = get_general_manager(search_value, column_name)
    elif view == "all_schedules":
        print("all__schedules schedules ...")
        data = get_all_schedules_table(search_value, column_name, start, length)
    

    # Total number of records before filtering
    total = len(data)
    print("total: ", total)
    # Pagination
    paginator = Paginator(data, length)
    page_number = start // length + 1
    page_obj = paginator.get_page(page_number)

    # Prepare response
    data = add_details(page_obj.object_list)
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': total,
        'data': data
    })


@login_required
def get_comperative_schedule(request, cs_id):
    
    username = request.user.username
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "cs_id": cs_id,
        "username": username,
    })

@login_required
def create_comperative_schedule(request):

    username = request.user.username
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "username": username,
    })

@login_required
def get_comperative_schedule_data(request, cs_id):
    
    request_user = request.user
    request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
    
    user_comparative_schedule_role = None
    for role in request_user_profile.roles.all():
        print("role id:", role.id)
        user_ace_role_ = Roles.objects.filter(id=role.id).first() if role.id else None
        print("role application:", user_ace_role_.application)
        if user_ace_role_.application == APP_NAME:
            user_comparative_schedule_role = user_ace_role_
            
    cs = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    pr = PurchaseRequest.objects.filter(id=cs.pr_id_id).first()
    proc_plans = ProcPlan.objects.all()
    currencies = Currency.objects.all()
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
    print("bids: ", bids)
    compliance = CSCompliance.objects.filter(cs_id=cs).all()
    print("compliance: ", compliance)
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
                try:
                    with open(bid.bid_document, 'rb') as f:
                        file_data = f.read()
                    encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                except Exception as ex:
                    print("Error: ", ex)
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
        sup_name = ""
        try:
            sup_name = comp.supplier_id.name
        except Exception as ex:
            print("Error: ", ex)
        
        if sup_name:
            compliance_list.append({
                "supplier_name": sup_name,
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
        try:
            compliance_remarks.append({
            "supplier": remark.supplier_id.id,
            "supplier_name": remark.supplier_id.name,
            "remarks": remark.remarks,
            })
        except Exception as ex:
            print("Error: ", ex)
        
    rankings_list = []
    for rank in rankings:
        try:
            supplier = Supplier.objects.filter(id=rank.supplier_id.id).first()
            rankings_list.append({
                "supplier_name": supplier.name if supplier else "",
                "rank": rank.rank,
                "remarks": rank.remarks,
                "decision": rank.decision,
                "total": rank.total,
                "created_at": rank.created_at,
            })
        except Exception as ex:
            print("Error: ", ex)
        
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
                "committeeDate": member.committee_date.astimezone() if member.committee_date else "",
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

    #print("current user role: ", user_comparative_schedule_role.role)
    context = {
        "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
        "cs_id": cs.cs_id,
        "cs_owner": cs_owner.username if cs_owner else "",
        "creator": cs_owner.first_name + " " + cs_owner.last_name if cs_owner else "",
        "pr_id": pr.id,
        "pr_number": cs.pr_number,
        "pr_date": cs.pr_date,
        "proc_plan": {
            "id": proc_plan.id,
            "proc_ref": proc_plan.proc_ref,
            "description": proc_plan.description,
            } if proc_plan else {},
        "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
        "currencies": list(currencies.values('id', 'currency')),
        "currency": {
            "id": cs.currency.id,
            "currency": cs.currency.currency,
            } if cs.currency else {},
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

@login_required    
def get_create_data(request, pr_id):

    purchase_request = PurchaseRequest.objects.filter(id=pr_id).first()
    if purchase_request:
        proc_plans = ProcPlan.objects.all()
        currencies = Currency.objects.all()
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
                "currencies": list(currencies.values('id', 'currency')),
                "suppliers": list(suppliers.values('id', 'name')),
                "users": list(users.values('id', 'username', 'first_name', 'last_name')),
            }, safe=False)
    else:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        }, safe=False)

@login_required
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

@login_required
def create(request):

    if request.method == "POST":
        tender_id = "CS" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S")
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
                                  timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S%p") + advert_file.name
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

@login_required        
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
        currency = request.POST.get("currency", "")
        print("currency: ", currency)
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
        currency = Currency.objects.filter(id=currency).first() if currency else None
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules(
            cs_id = cs_id,
            pr_id_id = pr.id,
            scope_of_work = scope_of_work,
            currency = currency,
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

@login_required   
def update_comparative_schedule(request):

    try:
        
        advert_files = request.FILES.getlist("advert", None)
        cs_id = request.POST.get("cs_id", "")
        plan_ref = request.POST.get("proc_ref", "")
        # proc_plan = data['proc_plan']
        proc_plan_ = ProcPlan.objects.filter(proc_ref=plan_ref).first()
        scope_of_work = request.POST.get("scope_of_work", "")
        currency = request.POST.get("currency", "")
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
        currency = Currency.objects.filter(id=currency).first() if currency else None
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()

        if cs_query:
            clear_approvals(cs_id)
            if currency:
                cs_query.currency = currency
            if scope_of_work:
                cs_query.scope_of_work = scope_of_work 
            if closing_date:
                cs_query.closing_date = closing_date
            if closing_time:
                cs_query.closing_time = closing_time
            if advert_path:
                cs_query.advert = advert_path
            if pr_number:
                cs_query.pr_number = pr_number
            if pr_date:
                cs_query.pr_date = pr_date
            if date_tender_opened:
                cs_query.cs_opened = date_tender_opened
            if tender_adjudication_committee_date:
                cs_query.tac_date = tender_adjudication_committee_date
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

@login_required
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

@login_required    
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

@login_required
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
            compliance = CSCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier).first()
            if compliance:
                compliance.delete()
            bid.delete()
            
    return JsonResponse({
        "message": "Bid deleted successfully",
        "success": True,
    })

@login_required
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

@login_required    
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

@login_required     
def save_cs_ranking(request):
    cs_id = request.POST.get("cs_id", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    print("cs_query: ", cs_query)
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
            decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(total) + " excluding VAT."
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

@login_required    
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
                committee_query.save()
            else:
                committee_query = Committee(
                    cs_id = cs_query,
                    user = member_profile,
                    committee_name = member['memberUserName'],
                    committee_position = member['memberPosition']
                )
                msg = "You have been added to the committee for RFQ " + cs_query.cs_id
                url = "/comperative_schedule/comperative_schedule/" + cs_query.cs_id
                notify_user(member_profile, msg, "RFQ", url, cs_query.cs_id)
            committee_query.save()
            
        
    return JsonResponse({
        "message": "Committee saved successfully",
        "success": True,
    })

@login_required
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

@login_required
def approve_cs_committee(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    approval = request.POST.get("approval", "")
    justification = request.POST.get("justification", "")

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
            committee_query.justification = justification
            committee_query.committee_date = timezone.now()
            committee_query.save()
            notification_update(member_profile, cs_query.cs_id)
        
        committees = Committee.objects.filter(cs_id=cs_query).all()
        committee_approved = all([c.committee_approval == "Approved" for c in committees])
        if committee_approved:
            fm_role = Roles.objects.filter(name="Finance Manager", application=APP_NAME).first()
            print("fm role: ", fm_role)
            fm_user = UserProfile.objects.filter(roles=fm_role).first()
            print("fm user: ", fm_user.username, fm_user.id)
            msg = "Comperative Schedule is ready for your approval " + cs_query.cs_id
            url = "/comperative_schedule/comperative_schedule/" + cs_query.cs_id
            notify_user(fm_user, msg, "RFQ", url, cs_query.cs_id)

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

@login_required
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
    
    committees = Committee.objects.filter(cs_id=cs_query).all()
    user = UserProfile.objects.filter(username=username).first()
    if user:
        if role == "general_manager":
            gm_approval = CSApproval(
                cs_id = cs_query,
                user = user,
                approver_role = role,
                approval = approval,
                justification = justification,
                approval_date = timezone.now(),
                created_at = timezone.now(),
            )
            gm_approval.save()
            notification_update(user, cs_query.cs_id)
            
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
                approval_date = timezone.now(),
                created_at = timezone.now(),
            )
            fm_approval.save()
            notification_update(user, cs_query.cs_id)
                
            committee_approved = all([c.committee_approval == "Approved" for c in committees])
            if committee_approved and approval == "Approved":
                gm_role = Roles.objects.filter(name="General Manager", application=APP_NAME).first()
                print("gm role: ", gm_role)
                gm_user = UserProfile.objects.filter(roles=gm_role).first()
                print("gm user: ", gm_user.username, gm_user.id)
                notify_user(gm_user, "Comperative Schedule is ready for your approval " + cs_query.cs_id, "RFQ", "/comperative_schedule/comperative_schedule/" + cs_query.cs_id, cs_query.cs_id)
        
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

@login_required
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
            committee_query.committee_date = timezone.now()
            committee_query.save()
        elif committee_decision == "reject":
            committee_query.committee_status = False
            committee_query.committee_date = timezone.now()
            committee_query.save() 
            
    return JsonResponse({
        "message": "Committee decision saved successfully",
        "success": True,
    })   

@login_required        
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
                                  timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S") + bid_document_file.name
                save_file(bid_document_file, bid_document_path)
        
        except Exception as ex:
            print("Error: ", ex)
        
        for i in range(0,int(item_count)):
            item_id = "Item" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S%p")
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
                supplier_id = "SUP" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S")
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

@login_required      
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
