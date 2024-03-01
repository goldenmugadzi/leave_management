from datetime import datetime, date
from random import randrange

from django.contrib import messages
from django.shortcuts import render, redirect

from django.apps import apps
from sweetify import sweetify

from finance.rfq.models import *
from finance.Ace.models import *

Sections = apps.get_model(app_label='users', model_name='Sections')
Districts = apps.get_model(app_label='users', model_name='Districts')
Depots = apps.get_model(app_label='users', model_name='Depots')
Regions = apps.get_model(app_label='users', model_name='Regions')
Roles = apps.get_model(app_label='users', model_name='Roles')
Designations = apps.get_model(app_label='users', model_name='Designations')
Notification = apps.get_model(app_label='users', model_name='Notification')
Ace = apps.get_model(app_label='Ace', model_name='Ace')
UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
from django.contrib.auth.models import User

# Create your views here.
def index(request):

    # QuerySet Object
    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
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

        if role.application =="rfq":
            custom_user_roles["rfq"]=role

    Rfq_role=custom_user_roles["rfq"].role
    print(Rfq_role)

    if Rfq_role == "RFQ Requester":
        return render(request, "rfq/rfq_requester.html")
    elif Rfq_role == "RFQ Section Head":
        return render(request, "rfq/rfq_authoriser.html")
    elif Rfq_role == "RFQ Finance Manager":
        return render(request, "rfq/rfq_fm.html")
    elif Rfq_role == "RFQ General Manager":
        return render(request, "rfq/rfq_gm.html")
    else:
        messages.error(request, 'you need to contact it to get a role in the ACE')
        sweetify.success(request,'you need to contact it to get a role in the ACE')
        return redirect("/")

    return redirect("/")

def create_rfq_from_ace(request):
    requested_by = request.user.username
    user_id = request.user.id

    user_profile = UserProfile.objects.filter(id=user_id).first()
    user_designation = Designations.objects.filter(id=user_profile.designation.id).first() if user_profile.designation else None


    if request.method == "GET":
        Ace_id = request.GET['i']
        Ace_id = str(Ace_id)
        ace_id = Ace_id
        Ace = Ace.objects.filter(ace_id=ace_id).first()
        context = Ace
        user_page = "rfq/create_rfq.html"

        return render(request, user_page, {"title": "All Records",
                                              "ace": context,
                                            "user_title": requested_by
                                           })


    elif request.method == "POST":
        rand = randrange(1, 99)
        rand2 = str(rand)

        date = datetime.now()
        date = date.strftime("%Y%m%d")

        rfq_id = "RFQ" + date + rand2
        rfq_type = request.POST.get("rfq_type")
        section = request.POST.get("section")
        allocation_code_of_expenditure = request.POST.get("allocation_code_of_expenditure")
        scope_of_work = request.POST.get("scope_of_work")
        quantity = request.POST.get("quantity")
        proc_ref = request.POST.get("proc_ref")
        amount = request.POST.get("amount")
        quotation1 = request.FILES.get("quotation1")
        quotation2 = request.FILES.get("quotation2")
        quotation3 = request.FILES.get("quotation3")
        payment_mode = request.POST.get("payment_mode")
        requested_by = requested_by
        date_created = date
        ace = request.POST.get("ace")



        rfq = RFQ(
            rfq_id=rfq_id,
            rfq_type=rfq_type,
            section=section,
            allocation_code_of_expenditure=allocation_code_of_expenditure,
            scope_of_work=scope_of_work,
            quantity=quantity,
            proc_ref=proc_ref,
            amount=amount,
            quotation1=quotation1,
            quotation2=quotation2,
            quotation3=quotation3,
            payment_mode=payment_mode,
            requested_by=requested_by,
            date_created=date_created,
            ace=ace,
            designation=user_designation
        )
        rfq.save()
        messages.error(request, 'you have successfully created an RFQ', extra_tags="success")
    return redirect("/rfq")

def get_to_approve_rfq(request):
    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
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

        if role.application =="rfq":
            custom_user_roles["rfq"]=role

    Rfq_role=custom_user_roles["rfq"].role
    print(Rfq_role)
    if request.method == "POST":
        rfq_id = request.POST.get("rfq_id")
        rfq = RFQ.objects.filter(rfq_id=rfq_id).first()
        #if rfq role is section head
        if Rfq_role == "authenticate" and rfq.section_head_approval_status != "approved by section head":
            rfq.approval_status="approved by section head"
            rfq.section_head=user_id
            rfq.date_approved=date.today()

            rfq.section_head_approval_status="approved by section head"
            rfq.section_head_approval_date = date.today()
            rfq.save()
            return render(request, "rfq/rfq_authoriser.html")
        #if rfq role is finance manager
        elif Rfq_role == "check" and rfq.finance_manager_approval_status != "approved by finance manager":
            rfq.approval_status="approved by finance manager"
            rfq.finance_manager=user_id
            rfq.date_approved=date.today()
            rfq.finance_manager_approval_status="approved by finance manager"
            rfq.finance_manager_approval_date = date.today()
            rfq.save()
            # return render(request, "rfq/rfq_fm.html")
        #if rfq role is general manager
        elif Rfq_role == "approve" and rfq.general_manager_approval_status != "approved by general manager":
            rfq.approval_status="approved by general manager"
            rfq.general_manager=user_id
            rfq.date_approved=date.today()
            rfq.general_manager_approval_status="approved by general manager"
            rfq.general_manager_approval_date = date.today()
            rfq.save()
            # return render(request, "rfq/rfq_gm.html")
        else:
            messages.error(request, 'you need to contact it to get a role in the RFQ')
            sweetify.success(request,'you need to contact it to get a role in the RFQ')


        return redirect("/")

    return redirect("/")
