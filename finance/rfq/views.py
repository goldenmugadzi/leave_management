from django.shortcuts import render, redirect

from utils.helper_functions import group_user_roles
from utils.save_file import save_file
from .models import RFQ, Quotation
from django.shortcuts import render, redirect, get_object_or_404
from .models import RFQ, Quotation,Process,Application
from django.contrib.auth.decorators import login_required
from .forms import RFQForm, QuotationFormSet

from datetime import datetime, date
from random import randrange
import json

from django.contrib import messages

from django.apps import apps
from sweetify import sweetify

from finance.rfq.models import *
from finance.Ace.models import Ace, Transactions, Budget
from it.users.models import *

from it.users.models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.urls import reverse

@login_required
def rfq_detail(request, rfq_id):
    rfq = RFQ.objects.get(id=rfq_id)
    approvalForm=None
    to=None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute
    
    try:
        last_approved = rfq.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    
    next_step = last_approved + 1
    
    try:
        newStep= Step.objects.get(step=next_step, workflow=rfq.process.workflow, approver__in=user_roles)
        if newStep and request.user.section==rfq.section and next_step==1:
            approvalForm = ApprovalForm 
            to=newStep.to
        elif newStep:
            approvalForm = ApprovalForm
            to=newStep.to
    except Step.DoesNotExist:
        pass
    approved_steps = rfq.process.approval_set.all().values_list('step__step', flat=True)
    print(approved_steps)
    return render(request, 'finance/rfq/rfq_detail.html', {'rfq': rfq, 'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})
    
@login_required
def create_rfq(request):
    if request.method == 'POST':
        form = RFQForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        app= Application.objects.get(name='rfq')
        if form.is_valid() and formset.is_valid():
            rfq = form.save(commit=False)
            rfq.process = intiate(request, 'rfq')
            rfq.requested_by = request.user
            rfq.save()

            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.rfq = rfq
                quotation.save()

            url = reverse('rfq:rfq_detail', args=[rfq.id])
            return redirect(url)
    else:
        form = RFQForm()
        formset = QuotationFormSet()

    return render(request, 'finance/rfq/create_rfq.html', {'form': form, 'formset': formset})
@login_required
def rfqs_awaiting_my_action(request):
    """
    for each rfq.process in the rfqs,  let curent_step = the last rfq.process.approval if any else 0 and let next_step =curent_step+1
    then check if  next_step=step.step for rfq.process.workflow.step_set filtered by approcer = user.roles.all.
    """
    rfqs_to_process = []
    user_roles = request.user.roles.all()
    for rfq in RFQ.objects.all():
        process = rfq.process

        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1

        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
        
        if step:
            rfqs_to_process.append(rfq)

    return render(request, 'finance/rfq/view_all_rfqs.html', {'rfqs': rfqs_to_process})

def rfq_create(request):
    
    if request.method == "GET":
        return render(
            request, 
            'finance/rfq/rfq_create.html', 
            {
                "title": "All Records",
                "user_title": "requested_by"
            })
        
    elif request.method == "POST":
        rand = randrange(1, 99)
        rand2 = str(rand)

        date = datetime.now()
        date = date.strftime("%Y%m%d")

        rfq_id = "RFQ" + date + rand2
        rfq_type = request.POST.get("rfq_type")
        allocation_code_of_expenditure = request.POST.get("allocation_code_of_expenditure")
        scope_of_work = request.POST.get("scope_of_work")
        quantity = request.POST.get("quantity")
        proc_ref = request.POST.get("proc_ref")
        amount = request.POST.get("amount")
        quotation1 = request.FILES.get("quotation1")
        quotation2 = request.FILES.get("quotation2")
        quotation3 = request.FILES.get("quotation3")
        payment_mode = request.POST.get("payment_mode")
        requested_by = request.user.username
        section = request.user.section.code
        designation = request.user.designation.id
        date_created = date
        
        file_paths = []
        try:
            if quotation1:
                file_path1 = 'uploads/rfq/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + quotation1.name 
                save_file(quotation1,file_path1)
                file_paths.append(file_path1)
            if quotation2:
                file_path2 = 'uploads/rfq/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + quotation2.name 
                save_file(quotation2,file_path2)
                file_paths.append(file_path2)
            if quotation3:
                file_path3 = 'uploads/rfq/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + quotation3.name 
                save_file(quotation3,file_path3)
                file_paths.append(file_path3)
            
        except Exception as ex:
            print("Error:",ex)

        rfq = RFQ(
            rfq_id=rfq_id,
            rfq_type=rfq_type,
            section_code=section,
            designation=designation,
            allocation_code_of_expenditure=allocation_code_of_expenditure,
            scope_of_work=scope_of_work,
            quantity=quantity,
            proc_ref=proc_ref,
            amount=amount,
            payment_mode=payment_mode,
            requested_by=requested_by,
            date_created=date_created,
        )
        rfq.save()
        
        # save the file paths
        for file_path in file_paths:
            print("file_path: ", file_path)
            quotation = Quotation(
                rfq=rfq,
                quotation_file=file_path
            )
            quotation.save()
            
        messages.error(request, 'you have successfully created an RFQ', extra_tags="success")
    return redirect("/rfq")
    
# Create your views here.
def index(request):
    # QuerySet Object
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    custom_user_roles = {
        "non_conformity": {},
        "remittance_advice": {},
        "pettycash": {},
        "adjudication": {},
        "tokens": {},
        "tenders": {},
        "ace": {},
        "users": {},
        "rfq": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()
        if role.application == "rfq":
            custom_user_roles["rfq"] = role

    Rfq_role = custom_user_roles["rfq"].role if custom_user_roles["rfq"] else None
    section_code = user_profile.section.code
    print(Rfq_role)
    print(section_code)

    if Rfq_role == "request":
        context = get_user_rfq(request.user.username, section_code)
    if Rfq_role == "create":
        context = get_procuremtn_rfq(request.user.username)
    elif Rfq_role == "authenticate":
        context = get_section_head_rfq(request.user.username, section_code)
    elif Rfq_role == "check":
        context = get_finance_manager_rfq()
    elif Rfq_role == "approve":
        context = get_general_manager_rfq()
    else:
        messages.error(request, 'you need to contact it to get a role in the RFQ')
        sweetify.success(request, 'you need to contact it to get a role in the RFQ')
        return redirect("/")

    user_page = 'finance/rfq/index.html'
    user_title = request.user.get_full_name()
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "Rfq_role": Rfq_role})


def get_user_rfq(username, section):
    rfq = RFQ.objects.filter(requested_by=username, section_code=section).order_by('-date_created')
    return rfq


def get_procuremtn_rfq(username):
    rfqs=RFQ.objects.filter(requested_by=username).order_by('-date_created')
    
    record_list = []
    for record in rfqs:
        o = {
            "document_id": record.pk,
            "proc ref": record.proc_ref,
            "quantity": record.quantity,
            "amount":record.amount,
            "scope_of_work": record.scope_of_work,
            "decision":record.approval_status

        }
        record_list.append(o)
    rfq = json.dumps(record_list, default=str)
    return rfq


def get_section_head_rfq(username, section):
    rfq = RFQ.objects.filter(requested_by=username, section_code=section, approval_status="pending").order_by(
        '-date_created')
    return rfq


def get_finance_manager_rfq():
    rfq = RFQ.objects.filter(approval_status="approved by section head").order_by('-date_created')
    return rfq


def get_general_manager_rfq():
    rfq = RFQ.objects.filter(approval_status="approved by finance manager").order_by('-date_created')
    return rfq
    
def create_rfq_from_ace(request):
    requested_by = request.user.username
    user_id = request.user.id

    user_profile = UserProfile.objects.filter(id=user_id).first()
    user_designation = Designations.objects.filter(
        id=user_profile.designation.id).first() if user_profile.designation else None
    # acee = Ace.objects.all()

    if request.method == "GET":
        Ace_id = request.GET['i']
        Ace_id = str(Ace_id)
        ace_id = Ace_id
        acee = Ace.objects.filter(Ace_id2=ace_id).first()

        ace = acee.Ace_id2

        amount = acee.amount
        cost_center = str(acee.section)
        quantity = acee.quantity
        description = acee.details_of_expenditure
        print(cost_center)
        user_page = "finance/rfq/create_rfq_from_ace.html"

        return render(request, user_page, {"title": "All Records",
                                           "ace": ace,
                                           "amount": amount,
                                           "cost_center": cost_center,
                                           "user_title": requested_by,
                                           "quantity": quantity,
                                           'description': description
                                           })


    elif request.method == "POST":
        rand = randrange(1, 99)
        rand2 = str(rand)

        date1 = datetime.now()
        date = date1.strftime("%Y%m%d")

        rfq_id = "RFQ" + date + rand2
        rfq_type = str('ACE')
        section = request.POST.get("section")
        allocation_code_of_expenditure = section
        scope_of_work = request.POST.get("scope_of_work")
        quantity = request.POST.get("quantity")
        proc_ref = request.POST.get("proc_ref")
        amount = request.POST.get("amount")
        # quotation1 = request.FILES('quotation1')
        # quotation2 = request.FILES('quotation2')
        # quotation3 = request.FILES('quotation3')

        # check if qoutation1, qoutation2, qoutation3 are in the request.FILES
        if 'quotation1' in request.FILES:
            quotation1 = request.FILES['quotation1']
        else:
            quotation1 = None
        if 'quotation2' in request.FILES:
            quotation2 = request.FILES['quotation2']
        else:
            quotation2 = None
        if 'quotation3' in request.FILES:
            quotation3 = request.FILES['quotation3']
        else:
            quotation3 = None


        payment_mode = request.POST.get("payment_mode")
        requested_by = requested_by
        date_created = datetime.now()
        ace = request.POST.get("ace")
        ace = Ace.objects.filter(Ace_id2=ace).first()

        print(quotation1, quotation2, quotation3)

        rfq = RFQ(
            rfq_id=rfq_id,
            rfq_type=rfq_type,
            section_code=section,
            allocation_code_of_expenditure=allocation_code_of_expenditure,
            scope_of_work=scope_of_work,
            quantity=quantity,
            proc_ref=proc_ref,
            amount=amount,
            payment_mode=payment_mode,
            requested_by=requested_by,
            date_created=date_created,
            ace=ace,
            designation=user_designation.description
        )

        rfq.save()
        rfq = RFQ.objects.filter(rfq_id=rfq_id).first()
        quotation1 = Quotation(quotation_file=quotation1, rfq=rfq)
        quotation2 = Quotation(quotation_file=quotation2, rfq=rfq)
        quotation3 = Quotation(quotation_file=quotation3, rfq=rfq)

        print(quotation1, quotation2, quotation3)
        # quotation1.save()
        # quotation2.save()
        # quotation3.save()
        messages.error(request, 'you have successfully created an RFQ', extra_tags="success")
    return redirect("/rfq")


def get_to_approve_rfq(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    custom_user_roles = group_user_roles(user_profile.roles)

    Rfq_role = custom_user_roles["rfq"].role
    print(Rfq_role)
    if request.method == "POST":
        rfq_id = request.POST.get("rfq_id")
        rfq = RFQ.objects.filter(rfq_id=rfq_id).first()
        # if rfq role is section head
        if Rfq_role == "authenticate" and rfq.section_head_approval_status != "approved by section head":
            rfq.approval_status = "approved by section head"
            rfq.section_head = user_id
            rfq.date_approved = date.today()

            rfq.section_head_approval_status = "approved by section head"
            rfq.section_head_approval_date = date.today()
            rfq.save()
            messages.error(request, 'you have approved ace', rfq_id)
            sweetify.success(request, 'you have approved ace' + rfq_id)
            return render(request, "rfq/rfq_authoriser.html")
        # if rfq role is finance manager
        elif Rfq_role == "check" and rfq.finance_manager_approval_status != "approved by finance manager":
            rfq.approval_status = "approved by finance manager"
            rfq.finance_manager = user_id
            rfq.date_approved = date.today()
            rfq.finance_manager_approval_status = "approved by finance manager"
            rfq.finance_manager_approval_date = date.today()
            rfq.save()
            messages.error(request, 'you have approved ace', rfq_id)
            sweetify.success(request, 'you have approved ace' + rfq_id)
            # return render(request, "rfq/rfq_fm.html")
        # if rfq role is general manager
        elif Rfq_role == "approve" and rfq.general_manager_approval_status != "approved by general manager":
            rfq.approval_status = "approved by general manager"
            rfq.general_manager = user_id
            rfq.date_approved = date.today()
            rfq.general_manager_approval_status = "approved by general manager"
            rfq.general_manager_approval_date = date.today()
            rfq.save()
            messages.error(request, 'you have approved ace', rfq_id)
            sweetify.success(request, 'you have approved ace' + rfq_id)
            # return render(request, "rfq/rfq_gm.html")
        else:
            messages.error(request, 'you need to contact IT to get a role in the RFQ')
            sweetify.success(request, 'you need to contact IT to get a role in the RFQ')

        return redirect("/")

    return redirect("/")


def get_to_reject_rfq(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    custom_user_roles = {
        "non_conformity": {},
        "remittance_advice": {},
        "pettycash": {},
        "adjudication": {},
        "tokens": {},
        "tenders": {},
        "ace": {},
        "users": {},
        "rfq": {},
    }

    user_group_ids = user_profile.roles
    user_group_ids = user_group_ids.split(",") if user_group_ids else []
    for id in user_group_ids:

        role = Roles.objects.filter(id=id).first()

        if role.application == "rfq":
            custom_user_roles["rfq"] = role

    Rfq_role = custom_user_roles["rfq"].role
    print(Rfq_role)
    if request.method == "POST":
        rfq_id = request.POST.get("rfq_id")
        rfq = RFQ.objects.filter(rfq_id=rfq_id).first()
        # if rfq role is section head
        if Rfq_role == "authenticate" and rfq.section_head_approval_status != "rejected by section head":
            rfq.approval_status = "rejected by section head"
            rfq.section_head = user_id
            rfq.date_rejected = date.today()

            rfq.section_head_approval_status = "rejected by section head"
            rfq.section_head_approval_date = date.today()
            rfq.save()
            messages.error(request, 'you have rejected rfq', rfq_id)
            sweetify.success(request, 'you have rejected rfq' + rfq_id)
            return render(request, "rfq/rfq_authoriser.html")
        # if rfq role is finance manager
        elif Rfq_role == "check" and rfq.finance_manager_approval_status != "rejected by finance manager":
            rfq.approval_status = "rejected by finance manager"
            rfq.finance_manager = user_id
            rfq.date_rejected = date.today()
            rfq.finance_manager_approval_status = "rejected by finance manager"
            rfq.finance_manager_approval_date = date.today()
            rfq.save()
            messages.error(request, 'you have rejected rfq', rfq_id)
            sweetify.success(request, 'you have rejected rfq' + rfq_id)
            # return render(request, "rfq/rfq_fm.html")
        # if rfq role is general manager
        elif Rfq_role == "approve" and rfq.general_manager_approval_status != "rejected by general manager":
            rfq.approval_status = "rejected by general manager"
            rfq.general_manager = user_id
            rfq.date_rejected = date.today()
            rfq.general_manager_approval_status = "rejected by general manager"
            rfq.general_manager_approval_date = date.today()
            rfq.save()
            messages.error(request, 'you have rejected rfq', rfq_id)
            sweetify.success(request, 'you have rejected rfq' + rfq_id)
            # return render(request, "rfq/rfq_gm.html")
        else:
            messages.error(request, 'you need to contact IT to get a role in the RFQ')
            sweetify.success(request, 'you need to contact IT to get a role in the RFQ')

        return redirect("/")

    return redirect("/")
@login_required
def view_all_rfqs(request):
    rfqs = RFQ.objects.all()
    return render(request, 'finance/rfq/view_all_rfqs.html', {'rfqs': rfqs})
