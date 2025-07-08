import base64
import copy
import os
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from django.db.models import Sum

from finance.comparative_schedules.models import Currency
from finance.comparative_schedules.views import notification_update, notify_user
from .models import *
from it.users.models import *
from finance.purchase_request.models import PurchaseRequest, PrItem, Attachment, UnitOfMeasurement
from ACE2.models import Ace2
from finance.ristricted_bidding.models import *
from django.db.models import Q, Exists, OuterRef, Count, F
import pandas as pd
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages

APP_NAME = "restricted_biddings"


def clear_approvals(cs_id):
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    committee = RBCommittee.objects.filter(cs_id=cs_query).all()
    if committee:
        for member in committee:
            member.committee_approval = ""
            member.committee_status = ""
            member.save()

    approvals = RBApproval.objects.filter(cs_id=cs_query).all()
    if approvals:
        for approval in approvals:
            approval.approval = ""
            approval.justification = ""
            approval.save()

    return True


def getUserFMGMRoles(user):
    fm_role, gm_role, procurement_role = False, False, False
    try:
        user_comparative_schedule_role = user.roles.filter(application=APP_NAME).first()

        if user_comparative_schedule_role.application == APP_NAME:
            if user_comparative_schedule_role.role == "check":
                fm_role = True
            if user_comparative_schedule_role.role == "approve":
                gm_role = True
            if user_comparative_schedule_role.role == "procurement":
                procurement_role = True
    except Exception as ex:
        print("Error: ", ex)

    return fm_role, gm_role, procurement_role


@login_required
def get_comperative_schedules(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role, procurement_role = False, False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)
    print("fm_role: ", fm_role, "gm_role: ", gm_role, "procurement_role: ", procurement_role)

    if fm_role == True:
        return redirect('/restricted_bidding/pending_fm_approval')
    elif gm_role == True:
        return redirect('/restricted_bidding/pending_gm_approval')
    elif procurement_role == True:
        return redirect('/restricted_bidding/your_schedules')
    else:
        return redirect('/restricted_bidding/pending_commitee')


@login_required
def your_comperative_schedules(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)

    user_page = 'finance/restricted_bidding/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {
        "fm_role": fm_role,
        "gm_role": gm_role,
        "procurement_role": procurement_role})


@login_required
def get_all_schedules(request):
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)

    print("roles: ", fm_role, gm_role)
    user_page = 'finance/restricted_bidding/cs_schedules.html'
    return render(request, user_page, {"procurement_role": procurement_role, "fm_role": fm_role, "gm_role": gm_role})


@login_required
def get_pending_committee(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)

    print("roles: ", fm_role, gm_role)
    user_page = 'finance/restricted_bidding/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {"procurement_role": procurement_role,
                                       "fm_role": fm_role,
                                       "gm_role": gm_role, })


@login_required
def get_pending_gm_approval(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/restricted_bidding/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {"procurement_role": procurement_role,
                                       "fm_role": fm_role,
                                       "gm_role": gm_role, })


@login_required
def get_pending_fm_approval(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/restricted_bidding/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {"procurement_role": procurement_role,
                                       "fm_role": fm_role,
                                       "gm_role": gm_role, })


def get_your_schedules(user_id, search_value=None, column_name=None, region=None):
    cs = RistricedBiddings.objects.filter(
        region=region,
        created_by_id=user_id,
        cancelled=False,
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


def get_pending_committee_table(user_id, search_value=None, column_name=None, region=None):
    print("user id: ", user_id)
    # fetch schedules if user exists in the committee and has not yet approved
    cs = RistricedBiddings.objects.filter(
        Q(rbcommittee__committee_approval=None) | Q(rbcommittee__committee_approval=""),
        Q(rbcommittee__user_id=user_id),
        cancelled=False,
        region=region
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


def get_finance_manager(user_id, search_value=None, column_name=None, region=None):
    cs = RistricedBiddings.objects.annotate(
        approved_count=Count('rbcommittee', filter=Q(rbcommittee__committee_approval="Approved")),
        not_approved_count=Count('rbcommittee', filter=Q(rbcommittee__committee_approval="")),
        rejected_count=Count('rbcommittee', filter=Q(rbcommittee__committee_approval="Rejected")),
        committee_count=Count('rbcommittee')
    ).filter(
        approved_count=F('committee_count'),
        committee_count__gt=2,
        not_approved_count=0,
        rejected_count=0,
        rbapproval__approval=None,
        region=region, cancelled=False
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


def get_general_manager(user_id, search_value=None, column_name=None, region=None):
    # fetch all pending approvals
    cs = RistricedBiddings.objects.annotate(
        all_approved=Exists(
            RBCommittee.objects.filter(
                cs_id=OuterRef('pk'),
                committee_approval="Approved"
            )
        ),
        any_not_approved=Exists(
            RBCommittee.objects.filter(
                cs_id=OuterRef('pk'),
                committee_approval="Approved"
            )
        ),
        gm_approved=Exists(
            RBApproval.objects.filter(
                cs_id=OuterRef('pk'),
                approver_role="general_manager",
                approval="Approved"
            )
        ),
        any_reject=Exists(
            RBApproval.objects.filter(
                cs_id=OuterRef('pk'),
                approval="Rejected"
            )
        ),
    ).filter(
        all_approved=True,
        any_not_approved=True,
        gm_approved=False,
        rbapproval__approver_role="finance_manager",
        rbapproval__approval="Approved",
        any_reject=False,
        region=region, cancelled=False
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


def get_all_schedules_table(user_id, search_value=None, column_name=None, region=None):
    cs = RistricedBiddings.objects.filter(region=region, cancelled=False).all()

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
    committee_reject_reason = ""

    for c in cs:
        committee_approval = ""
        gm_approval = None
        fm_approval = None
        committee = RBCommittee.objects.filter(
            cs_id=c
        ).all()

        if len(committee) > 0:
            committee_approved = all([c.committee_approval == "Approved" for c in committee])
            if committee_approved:
                committee_approval = "Approval Complete"
                fm_approval = RBApproval.objects.filter(
                    cs_id=c,
                    approver_role="finance_manager",
                ).first()

                gm_approval = RBApproval.objects.filter(
                    cs_id=c,
                    approver_role="general_manager",
                ).first()
            else:
                committee_approval = "Pending"
                fm_approval = None
                gm_approval = None

                committee_rejected = RBCommittee.objects.filter(
                    cs_id=c,
                    committee_approval="Rejected"
                ).first()

                if committee_rejected:
                    committee_reject_reason = committee_rejected.justification
                    committee_approval = "Rejected"

                committee_pending = RBCommittee.objects.filter(
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
            "created_by": user.username if user else None,
            "committee_approval": committee_approval,
            "committee_reject_reason": committee_reject_reason,
            "gm_approval": gm_approval.approval if gm_approval else "Pending",
            "gm_reject_reason": gm_approval.justification if gm_approval else "",
            "fm_approval": fm_approval.approval if fm_approval else "Pending",
            "fm_reject_reason": fm_approval.justification if fm_approval else "",
            "section": section.section if section else "",
            "region": region.region if region else "",
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
        })

    return cs_list


def datatable_data(request, view):
    user_id = request.user.id
    try:
        user_region = Regions.objects.filter(region=request.user.region).first()
    except Exception as ex:
        user_region = None
        print("error: ", ex)
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

    data = []
    if view == "your_schedules":
        data = get_your_schedules(user_id, search_value, column_name, user_region)
    elif view == "pending_committee":
        data = get_pending_committee_table(user_id, search_value, column_name, user_region)
    elif view == "pending_fm":
        data = get_finance_manager(user_id, search_value, column_name, user_region)
    elif view == "pending_gm":
        data = get_general_manager(user_id, search_value, column_name, user_region)
    elif view == "all_schedules":
        print("region inside: ", user_region)
        data = get_all_schedules_table(user_id, search_value, column_name, user_region)

    # Total number of records before filtering
    total = len(data)
    print("total: ", total)
    # Pagination
    paginator = Paginator(data, length)
    page_number = start // length + 1
    page_obj = paginator.get_page(page_number)

    # Prepare response
    print("adding details")
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
    return render(request, 'finance/restricted_bidding/rb_create.html', {
        "cs_id": cs_id,
        "username": username,
    })


@login_required
def create_comperative_schedule(request):
    username = request.user.username
    return render(request, 'finance/restricted_bidding/rb_create.html', {
        "username": username,
    })


@login_required
def get_comperative_schedule_data(request, cs_id):
    request_user = request.user
    request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
    user_comparative_schedule_role = request_user_profile.get_user_role_for_application(APP_NAME)
    print("user_comparative_schedule_role: ", user_comparative_schedule_role)

    cs = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    pr = PurchaseRequest.objects.filter(id=cs.pr_id_id).first()
    proc_plans = RBProcPlan.objects.all()
    currencies = Currency.objects.all()
    proc_plan = ""
    try:
        proc_plan = cs.proc_plan if cs.proc_plan else ""
    except Exception as ex:
        print("Error: ", ex)
    user = UserProfile.objects.filter(id=cs.created_by_id).first()
    region = Regions.objects.filter(id=cs.region_id).first()
    section = Sections.objects.filter(id=cs.section_id).first()
    items = RBItems.objects.filter(cs_id=cs).all()
    cs_items = RBRequiredItems.objects.filter(cs_id=cs).all()
    bids = RBBids.objects.filter(cs_id=cs).all()
    compliance = RBCompliance.objects.filter(cs_id=cs).all()
    complianceRemarks = RBComplianceRemarks.objects.filter(cs_id=cs).all()
    print("compliance remarks: ", complianceRemarks)
    # compliance remarks

    rankings = RBRanking.objects.filter(cs_id=cs).all()
    committee = RBCommittee.objects.filter(cs_id=cs).all()
    gm_approval = RBApproval.objects.filter(cs_id=cs, approver_role="general_manager").first()
    fm_approval = RBApproval.objects.filter(cs_id=cs, approver_role="finance_manager").first()

    suppliers = Supplier.objects.all()
    pr_items = PrItem.objects.filter(purchase_request=cs.pr_id_id, ordered=False).all()
    users = UserProfile.objects.all()
    print("checking 1....")
    items_list = []
    for item in items:
        items_list.append({
            "item_id": item.item_id,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit_of_measurement": item.unit_of_measurement,
            "created_at": item.created_at,
        })

    print("checking 2....")
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
            'description': bid.item_id.item_name,  # assume this is constant
            'quantity': bid.item_id.quantity,
            'unit_of_measurement': bid.item_id.unit_of_measurement,
            'unit_price': bid.unit_price,
            'vat': bid.vat,
            'total_price': bid.total,
        })

    print("checking 3....")
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
    print("checking 4....")
    compliance_remarks = []
    for remark in complianceRemarks:
        compliance_remarks.append({
            "supplier": remark.supplier_id.id,
            "supplier_name": remark.supplier_id.name,
            "remarks": remark.remarks,
        })

    print("checking 5....")
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

    print("checking 2 ...")
    cs_owner = UserProfile.objects.filter(id=cs.created_by_id).first()
    pr_item_list = []
    print("pr_items: ", pr_items)
    for pr_item in pr_items:
        pr_item_list.append({
            "id": pr_item.id,
            "item_required": pr_item.item_required,
            "quantity": pr_item.quantity,
            "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
            "ordered": pr_item.ordered,
        })

    pr_attachments = Attachment.objects.filter(purchase_request=pr).all()
    print("checking 1....")
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
            "ordered": True,
        })
    print("current cs_item_list: ", cs_item_list)

    # copy cs_item_list to pr_item_list
    pr_item_list = copy.deepcopy(cs_item_list) if cs_item_list else []
    for pr_item in pr_items:
        pr_item_list.append({
            "id": pr_item.id,
            "item_required": pr_item.item_required,
            "quantity": pr_item.quantity,
            "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
            "ordered": pr_item.ordered,
        })

    context = {
        "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
        "cs_id": cs.cs_id,
        "cs_owner": cs_owner.username if cs_owner else "",
        "creator": cs_owner.first_name + " " + cs_owner.last_name if cs_owner else "",
        "pr_id": pr.id if pr else "",
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
        "additional_notes": cs.additional_notes,
        "ref_date": cs.ref_date,
        "cs_opened": cs.cs_opened,
        "tac_date": cs.tac_date,
        "show_site_visit": cs.show_site_visit,
        "show_samples_required": cs.show_sample_required,
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
        proc_plans = RBProcPlan.objects.all()
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
            "scope_of_work": purchase_request.scope_of_work,
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
    proc_plans = RBProcPlan.objects.all()
    username = request.user.username

    return render(request, 'finance/restricted_bidding/rb_create.html', {
        "proc_plans": proc_plans,
        "username": username,
        "pr_id": pr_id,
    })


@login_required
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

        for i in range(0, int(item_count)):
            item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name][' + str(i) + ']']
            quantity = request.POST['supplier[quantity][' + str(i) + ']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement][' + str(i) + ']']
            vat = request.POST['supplier[vat][' + str(i) + ']']
            unit_price = request.POST['supplier[unit_price][' + str(i) + ']']
            total_price = request.POST['supplier[total_price][' + str(i) + ']']

            item = RBItems(
                cd_id=tender_id,
                item_id=item_id,
                item=description,
                required_qty=quantity,
                unit_of_measurement=unit_of_measurement,
            )
            item.save()

            supplier_id = ""
            if supplier_key:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
            supplier_query = Supplier(
                sup_id=supplier_id,
                supplier=supplier_name
            )
            supplier_query.save()

            bid = RBBids(
                document_id=tender_id,
                item_id=item_id,
                sup_id=supplier_id,
                unit_price=unit_price,
                vat=vat,
                quoted_qty=quantity,
                bid_no=bid_no,
                quote_date=bid_date,
                rfq_no=rfq_no,
                total=total_price,
                bid_document=bid_document_path,
            )
            bid.save()

        cs_query = RistricedBiddings(
            document_id=tender_id,
            rfq_date=rfq_date,
            scope_of_work=scope,
            closing_date=closing_date,
            closing_time=closing_time,
            rfq_no=rfq,
            advert=advert_path,
            date_created=date_tender_opened,
            pr_number=pr_number,
            pr_date=pr_date,
            tender_opened=date_tender_opened,
            tac_date=tender_adjudication_committee_date,
            region="",
        )
        cs_query.save()

        # rfq_query = RFQUPDATE.objects.filter(document_id=rfq).first()
        # if rfq_query:
        #     rfq_query.tender_board = 'yes'
        #     rfq_query.save()

        if 'add_supplier' in request.POST:
            return redirect('add_supplier', tender_id=tender_id)

        return render(request, 'finance/restricted_bidding/rb_create.html', {
            "proc_plans": None,
        })


@login_required
def save_comparative_schedule(request):
    try:

        cs_id = "RB" + datetime.now().strftime("%Y%m%d%I%M%S")
        cs_exists = RistricedBiddings.objects.filter(cs_id=cs_id).first()
        # @TODO try random number if cs_id exists or return error
        if cs_exists:
            cs_id = "RB" + datetime.now().strftime("%Y%m%d%I%M%S")

        advert_files = request.FILES.getlist("advert", None)
        proc_ref = request.POST.get("proc_ref", "")
        print("proc plan: ", proc_ref)
        # check if proc ref has 'acc' prefix
        if not proc_ref.startswith("acc"):
            temp_proc_ref = "acc" + proc_ref
            proc_ref = temp_proc_ref

        proc_plan = RBProcPlan.objects.filter(proc_ref=proc_ref).first()
        print("proc_plan: ", proc_plan)
        scope_of_work = request.POST.get("scope_of_work", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        currency = request.POST.get("currency", "")
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
        _currency = Currency.objects.filter(id=currency).first()
        cs_query = RistricedBiddings(
            cs_id=cs_id,
            pr_id_id=pr.id,
            scope_of_work=scope_of_work,
            currency=_currency,
            closing_date=closing_date,
            closing_time=closing_time,
            advert=advert_path,
            pr_number=pr_number,
            pr_date=pr_date,
            ref_date=ref_date,
            proc_plan=proc_plan,
            cs_opened=date_tender_opened,
            tac_date=tender_adjudication_committee_date,
            created_by_id=user.id,
            section_id=None,
            region_id=None,
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
        proc_plan_ = RBProcPlan.objects.filter(proc_ref=plan_ref).first()
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
        cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()

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
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()

    if cs_query:
        pr_item_id = request.POST.get("pr_id", "")
        RBitems_data = json.loads(request.POST.get("json_data", "{}"))
        print("RBitems_data: ", RBitems_data)
        items = RBitems_data.get("cs_items", [])
        print("items ", items, type(items))
        print("pr_item_id: ", pr_item_id)
        purchase_request = PurchaseRequest.objects.filter(id=pr_item_id).first()
        print("purchase request: ", purchase_request)
        existing_items = RBRequiredItems.objects.filter(cs_id=cs_query).all()

        # Convert existing items to a list of dictionaries for easier comparison
        existing_items_list = [
            {
                "id": item.id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_of_measurement": item.unit_of_measurement,
                # Include other fields as necessary
            }
            for item in existing_items
        ]
        print("existing_items_list: ", existing_items_list)

        # Step 2: Identify items to add
        # Convert provided list to a set of IDs for faster lookup
        provided_ids = {item['item_required'] for item in items}
        print("provided_ids: ", provided_ids)

        # Find IDs in the provided list that are not in the existing items
        ids_to_add = provided_ids - {item['item_name'] for item in existing_items_list}
        print("ids_to_add: ", ids_to_add)

        # Filter the provided list to get the items to add
        items_to_add = [item for item in items if item['item_required'] in ids_to_add]
        print("items_to_add: ", items_to_add)

        # Step 3: Identify items to delete
        # Find IDs in the existing items that are not in the provided list
        ids_to_delete = {item['item_name'] for item in existing_items_list} - provided_ids
        print("ids_to_delete: ", ids_to_delete)

        # Step 4: Update the database
        # Add new items
        for item in items_to_add:
            print("item: ", item)
            pr_item = PrItem.objects.filter(item_required=item['item_required'],
                                            purchase_request=purchase_request).first()
            if pr_item:
                pr_item.ordered = True
                pr_item.save()
                print("item: ", item)
                cs_required_items = RBRequiredItems(
                    cs_id=cs_query,
                    item_id=item['id'],
                    item_name=item['item_required'],
                    quantity=item['quantity'],
                    unit_of_measurement=item['unit_of_measurement'],
                )
                cs_required_items.save()
                print("added ...")

        # Delete items that no longer exist
        for item in ids_to_delete:
            print("item: ", item)
            pr_item = PrItem.objects.filter(item_required=item, purchase_request=purchase_request).first()
            if pr_item:
                pr_item.ordered = False
                pr_item.save()
                RBRequiredItems.objects.filter(item_name=item, cs_id=cs_query).delete()

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

    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    supplier = Supplier.objects.filter(name=supplier_name).first()
    if not supplier:
        supplier_ = Supplier(
            name=supplier_name
        )
        supplier_.save()
        supplier = supplier_

        # check if bid exists
    bid_query = RBBids.objects.filter(cs_id=cs_query, sup_id=supplier, bid_no=bid_no).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = RBItems.objects.filter(item_id=bid.item_id).first()
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
        item_query = RBItems(
            cs_id=cs_query,
            item_id=item_id,
            item_name=item['item_required'],
            quantity=item['quantity'],
            unit_of_measurement=item['unit_of_measurement'],
        )
        item_query.save()

        print("bid_no", bid_no)
        bid = RBBids(
            cs_id=cs_query,
            item_id=item_query,
            sup_id=supplier,
            unit_price=item['unit_price'] if 'unit_price' in item else "",
            vat=item['vat'] if 'vat' in item else "",
            quoted_qty=item['quantity'] if 'quantity' in item else "",
            bid_no=bid_no,
            quote_date=bid_date,
            total=item['total_price'] if 'total_price' in item else "",
            bid_document=bid_doc_path,
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
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
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
    bid_query = RBBids.objects.filter(cs_id=cs_query, sup_id=supplier).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = RBItems.objects.filter(item_id=bid.item_id).first()
            if item:
                item.delete()

            compliance = RBCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier).first()
            if compliance:
                compliance.delete()
            bid.delete()

            complianceRemark = RBComplianceRemarks.objects.filter(cs_id=cs_query, supplier_id=supplier)
            if complianceRemark:
                complianceRemark.delete()

    return JsonResponse({
        "message": "Bid deleted successfully",
        "success": True,
    })


@login_required
def save_cs_compliance(request):
    cs_id = request.POST.get("cs_id", "")
    show_site_visit = request.POST.get("show_site_visit", "")
    show_sample_required = request.POST.get("show_sample_required", "")
    json_data = json.loads(request.POST.get("compliance", "{}"))
    print("json_data: ", json_data)
    compliances = json_data.get("compliance", [])
    print("items ", compliances, type(compliances))
    json_data_ = json.loads(request.POST.get("complianceRemarks", "{}"))
    print("json_data_: ", json_data_)
    compliance_remarks = json_data_.get("complianceRemarks", [])
    print("compliance_remarks ", compliance_remarks, type(compliance_remarks))

    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    cs_query.show_site_visit = True if show_site_visit == "yes" else False
    cs_query.show_sample_required = True if show_sample_required == "yes" else False
    cs_query.save()
    # check if compliance exists
    compliance_query = RBCompliance.objects.filter(cs_id=cs_query).all()
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
        compliance_query = RBCompliance(
            cs_id=cs_query,
            supplier_id=supplier,
            payment_terms=payment_terms,
            bid_validity=bid_validity,
            delivery_period=delivery_period,
            technical_specifications=technical_specifications,
            valid_tax_clearance=valid_tax_clearance,
            registered_with_praz=registered_with_praz,
            site_visit_done=site_visit_done,
            samples_delivered=samples_delivered,
            decision=decision,
            remarks=remarks,
        )
        compliance_query.save()

    # check if compliance remarks exists
    compliance_remarks_query = RBComplianceRemarks.objects.filter(cs_id=cs_query).all()
    if compliance_remarks_query:
        for remark in compliance_remarks_query:
            remark.delete()

    for remark in compliance_remarks:
        supplier_name = remark['supplier_name'] if 'supplier_name' in remark else ""
        print("supplier_name: ", supplier_name, cs_query)
        supplier = Supplier.objects.filter(name=supplier_name).first()
        print("supplier: ", supplier)
        _remark = RBComplianceRemarks(
            cs_id=cs_query,
            supplier_id=supplier,
            remarks=remark['remarks'] if 'remarks' in remark else "",
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
            name=supplier_name
        )
        supplier_query.save()

    return JsonResponse({
        "message": "Supplier saved successfully",
        "success": True,
    })


@login_required
def save_cs_ranking(request):
    cs_id = request.POST.get("cs_id", "")
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    # check if rankings exists
    ranking_query = RBRanking.objects.filter(cs_id=cs_query).all()
    if ranking_query:
        clear_approvals(cs_id)
        for ranking in ranking_query:
            ranking.delete()
    # get bids
    print("cs_query: ", cs_query)
    bids = RBBids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total'))
    print("bids: ", bids)
    compliant_bids = []
    for bid in bids:
        print("bid: ", bid)
        supplier = Supplier.objects.filter(id=bid['sup_id']).first()
        _compliance = RBCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier, decision=True).first()
        print("compliance: ", _compliance)
        if _compliance:
            compliant_bids.append(bid)
    print("compliant_bids: ", compliant_bids)
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
            decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(
                total) + " excluding VAT."
        ranking_query = RBRanking(
            cs_id=cs_query,
            supplier_id=supplier,
            rank=rank,
            remarks=remarks,
            decision=decision,
            total=total,
        )
        ranking_query.save()
        rank += 1

    # get rankings
    rankings = RBRanking.objects.filter(cs_id=cs_query).all()
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
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
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
            committee_query = RBCommittee.objects.filter(cs_id=cs_query, user=member_profile).first()
            if not committee_query:
                clear_approvals(cs_id)
                committee_query = RBCommittee(
                    cs_id=cs_query,
                    user=member_profile,
                    committee_name=member['memberUserName'],
                    committee_position=member['memberPosition'],
                    committee_date=datetime.now(),
                )
                msg = "You have been added to the committee for Restricted Bid " + cs_query.cs_id
                url = "/restricted_bidding/comperative_schedule/" + cs_query.cs_id
                notify_user(member_profile, msg, "Restricted Bid", url, cs_query.cs_id)
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
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = RBCommittee.objects.filter(cs_id=cs_query, user=member_profile).first()
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
    print("username: ", username)
    approval = request.POST.get("approval", "")
    justification = request.POST.get("justification", "")
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = RBCommittee.objects.filter(cs_id=cs_query, user=member_profile).first()
        if committee_query:
            committee_query.committee_approval = approval
            committee_query.justification = justification
            committee_query.committee_date = now()
            committee_query.save()
            notification_update(member_profile, cs_query.cs_id)

            committees = RBCommittee.objects.filter(cs_id=cs_query).all()
            committee_approved = all([c.committee_approval == "Approved" for c in committees])
            if committee_approved:
                fm_role = Roles.objects.filter(name="Finance Manager", application=APP_NAME).first()
                print("fm role: ", fm_role)
                fm_user = UserProfile.objects.filter(region=cs_query.region, roles=fm_role).first()
                print("fm user: ", fm_user.username, fm_user.id)
                msg = "Restricted is ready for your approval " + cs_query.cs_id
                url = "/restricted_bidding/comperative_schedule/" + cs_query.cs_id
                notify_user(fm_user, msg, "Restricted Bid", url, cs_query.cs_id)

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
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    user = UserProfile.objects.filter(region=cs_query.region, username=username).first()
    if user:
        if role == "general_manager":
            gm_approval = RBApproval(
                cs_id=cs_query,
                user=user,
                approver_role=role,
                approval=approval,
                justification=justification,
                approval_date=now(),
                created_at=now(),
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
            fm_approval = RBApproval(
                cs_id=cs_query,
                user=user,
                approver_role=role,
                approval=approval,
                justification=justification,
                approval_date=now(),
                created_at=now(),
            )
            fm_approval.save()
            notification_update(user, cs_query.cs_id)

            committees = RBCommittee.objects.filter(cs_id=cs_query).all()
            committee_approved = all([c.committee_approval == "Approved" for c in committees])
            if committee_approved and approval == "Approved":
                gm_role = Roles.objects.filter(name="General Manager", application=APP_NAME).first()
                print("gm role: ", gm_role)
                gm_user = UserProfile.objects.filter(roles=gm_role).first()
                print("gm user: ", gm_user.username, gm_user.id)
                notify_user(gm_user, "Restricted Bid is ready for your approval " + cs_query.cs_id, "Restricted Bid",
                            "/restricted_bidding/comperative_schedule/" + cs_query.cs_id, cs_query.cs_id)

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
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        }, safe=False)

    committee_query = RBCommittee.objects.filter(cs_id=cs_query, id=committee_id).first()
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


@login_required
def cs_add_supplier(request, cs_id):
    if request.method == 'GET':

        # tender_id = request.GET['tender_id']
        # get tender bids supplier items
        tender = RistricedBiddings.objects.filter(document_id=tender_id).first()
        proc_plan = RBProcPlan.objects.filter(proc_ref=tender.pr_number).first()
        bids = RBBids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})

        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Supplier.objects.filter(sup_id=bid.sup_id).first()
                    item = RBItems.objects.filter(item_id=bid.item_id).first()

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
        proc_plans = RBProcPlan.objects.all()
        suppliers = Suppliers.objects.all()
        supplier_list = {}
        for supplier in suppliers:
            supplier_list.update({supplier.sup_id: supplier.supplier})

        suppliers_json = json.dumps(supplier_list, default=str)

        return render(request, 'finance/tenders/tenders_add_supplier.html', {
            "proc_plans": proc_plans,
            "suppliers": suppliers_json,
            "tender": tender,
            "bids_items": bids_dict,
            "next_bid": len(bids_dict) + 1,
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

        for i in range(0, int(item_count)):
            item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name][' + str(i) + ']']
            quantity = request.POST['supplier[quantity][' + str(i) + ']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement][' + str(i) + ']']
            vat = request.POST['supplier[vat][' + str(i) + ']']
            unit_price = request.POST['supplier[unit_price][' + str(i) + ']']
            total_price = request.POST['supplier[total_price][' + str(i) + ']']

            item = RBItems(
                document_id=tender_id,
                item_id=item_id,
                item=description,
                required_qty=quantity,
                unit_of_measurement=unit_of_measurement,
                rfq_no=rfq_no,
            )
            item.save()

            supplier_id = ""
            if supplier_id:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
            supplier_query = Suppliers(
                sup_id=supplier_id,
                supplier=supplier_name
            )
            supplier_query.save()

            bid = RBBids(
                document_id=tender_id,
                item_id=item_id,
                sup_id=supplier_id,
                unit_price=unit_price,
                vat=vat,
                quoted_qty=quantity,
                bid_no=bid_no,
                quote_date=bid_date,
                rfq_no=rfq_no,
                total=total_price,
                bid_document=bid_document_path,
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
        tender = RistricedBiddings.objects.filter(document_id=tender_id).first()
        bids = RBBids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})

        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Suppliers.objects.filter(sup_id=bid.sup_id).first()
                    item = RBItems.objects.filter(item_id=bid.item_id).first()

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
        for i in range(1, bid_count):
            supplier_id = request.POST['supplier_id' + i + '']
            payment_terms = request.POST['payment_terms' + i + '']
            bid_validity = request.POST['bid_validity' + i + '']
            delivery_period = request.POST['delivery_period' + i + '']
            technical_specifications = request.POST['technical_specifications' + i + '']
            valid_tax_clearance = request.POST['valid_tax_clearance' + i + '']
            registered_with_praz = request.POST['registered_with_praz' + i + '']
            site_visit_done = request.POST['site_visit_done' + i + '']
            samples_delivered = request.POST['samples_delivered' + i + '']
            decision = request.POST['decision' + i + '']
            remarks = request.POST['remarks' + i + '']

            # insert into compliance table
            tender_compliance = RBCompliance(
                document_id=document_id,
                supplier_id=supplier_id,
                rfq_no=rfq_no,
                payment_terms=payment_terms,
                bid_validity=bid_validity,
                delivery_period=delivery_period,
                technical_specifications=technical_specifications,
                valid_tax_clearance=valid_tax_clearance,
                registered_with_praz=registered_with_praz,
                site_visit_done=site_visit_done,
                samples_delivered=samples_delivered,
                decision=decision,
                remarks=remarks,
            )
            tender_compliance.save()

        return redirect('tender_compliance', tender_id=document_id)

    return render(request, 'finance/restricted_bidding/cs_compliance_table.html', {"bids_items": bids_dict})


def save_additional_notes(request):
    cs_id = request.POST.get("cs_id", "")
    additional_notes = request.POST.get("additional_notes", "")
    print("cs_id: ", cs_id, "additional_notes: ", additional_notes)
    cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
    if cs_query:
        cs_query.additional_notes = additional_notes
        cs_query.save()
        return JsonResponse({
            "message": "Additional notes saved successfully",
            "success": True,
        })
    else:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        })


@login_required
def cancel_schedule(request, cs_id):
    print("cs_id: ", cs_id)
    try:
        cs_query = RistricedBiddings.objects.filter(cs_id=cs_id).first()
        if cs_query:
            cs_query.cancelled = True
            cs_query.scope_of_work = "Cancelled Schedule: " + cs_query.scope_of_work
            cs_query.save()
            print("cs_query: ", cs_query, cs_query.cancelled, "scope: ", cs_query.scope_of_work, cs_query.pr_number)
            required_items = RBRequiredItems.objects.filter(cs_id=cs_query).all()
            pr_query = PurchaseRequest.objects.filter(id=cs_query.pr_number).first()
            for item in required_items:
                pr_item = PrItem.objects.filter(id=item.item_id, purchase_request=pr_query).first()
                pr_item.ordered = False
                pr_item.save()
                item.delete()

    except Exception as ex:
        print("Error: ", ex)
        messages.error(request, "Error cancelling Comparative Schedule", str(ex))

    messages.success(request, "Comparative Schedule cancelled successfully")
    return redirect('/restricted_bidding/comperative_schedules')
