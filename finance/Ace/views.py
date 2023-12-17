import os
from datetime import datetime
from random import randrange

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render, redirect

UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
from .models import *
from django.core import serializers
from django.apps import apps
Sections = apps.get_model(app_label='users', model_name='Sections')
Districts = apps.get_model(app_label='users', model_name='Districts')
Depots = apps.get_model(app_label='users', model_name='Depots')
Regions = apps.get_model(app_label='users', model_name='Regions')
Roles = apps.get_model(app_label='users', model_name='Roles')
Designations = apps.get_model(app_label='users', model_name='Designations')
from django.contrib.auth.models import User


# Create your views here.
@login_required(login_url='/accounts/login/')
def index(request):
    user_title = request.user.get_full_name()

    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)

    if "Ace_section_head" in user_groups:
        return redirect('/Ace/list_section_head')
    if "Ace_requester" in user_groups:
        return redirect('/Ace/list_requester')
    if "Ace_cashier" in user_groups:
        return redirect('/Ace/list_disburser')
    if "Ace_authoriser" in user_groups:
        return redirect('/Ace/list_section_head')
    else:
        return redirect("/")

    return redirect("/")


@login_required(login_url='/accounts/login/')
def create_Ace(request):
    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    user_groups = user.groups.values_list('name', flat=True)

    custom_user_roles = {
        "non_conformity": {},
        "remittance_advice": {},
        "pettycash": {},
        "adjudication": {},
        "tokens": {},
        "tenders": {},
        "ace": {},
        "users": {},
    }

    user_group_ids = user_profile.roles
    user_group_ids = user_group_ids.split(",") if user_group_ids else []
    for id in user_group_ids:

        role = Roles.objects.filter(id=id).first()

        if role.application == "users":
            custom_user_roles["users"] = role

        if role.application == "non_conformity":
            custom_user_roles["non_conformity"] = role

        if role.application == "remittance_advice":
            custom_user_roles["remittance_advice"] = role

        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role

        if role.application == "adjudication":
            custom_user_roles["adjudication"] = role

        if role.application == "tokens":
            custom_user_roles["tokens"] = role

        if role.application == "tenders":
            custom_user_roles["tenders"] = role

        if role.application == "ace":
            custom_user_roles["ace"] = role

    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None

    new_user = {
        "id": user.pk,
        "username": user.username,
        "firstname": user.first_name,
        "lastname": user.last_name,
        "email": user.email,
        "section": section_used,
        "depot": depot,
        "district": district,
        "region": region,
        "roles": custom_user_roles,
        "designation": user_designation,
    }
    user_title = request.user.get_full_name()
    section_budget = Budget.objects.filter(section = section_used).all()
    print(section_budget)
    # l = request.user.groups.values_list('name', flat=True)
    # # QuerySet Object
    # user_groups = list(l)
    #
    # user_id = request.user.id
    # user = UserProfile.objects.filter(user_id=user_id).first()
    # secction = user.section

    if request.method == "POST":
        Department = request.POST['department']
        location = request.POST['location']
        # section = secction
        allocation_code_of_expenditure = request.POST['allocation_code_of_expenditure']
        details_of_expenditure = request.POST['details_of_expenditure']
        amount = request.POST['amount']
        # form = UploadFileForm(request.POST, request.FILES)
        quotation1 = request.FILES['quotation1']
        quotation2 = request.FILES['quotation2']
        quotation3 = request.FILES['quotation3']
        payment_mode = request.POST['payment_mode']
        requested_by = request.user.username

        # last_petty = Ace.objects.last()
        rand = randrange(1, 99)
        rand2 = str(rand)

        date = datetime.now()
        date = date.strftime("%Y%m%d")

        petty_id = "PC" + date + rand2

        objectify = Ace(
            Department=Department,
            location=location,
            section=section_used,
            allocation_code_of_expenditure=allocation_code_of_expenditure,
            details_of_expenditure=details_of_expenditure,
            amount=amount,
            quotation1=quotation1,
            quotation2=quotation2,
            quotation3=quotation3,
            payment_mode=payment_mode,
            requested_by=requested_by,
            petty_id=petty_id,
        )

        objectify.save()

        return redirect('/Ace')

    return render(request, 'Ace/Ace_create.html', {"title": "Create",
                                                   "user_title": user_title,
                                                   "section_budget": section_budget})


@login_required(login_url='/accounts/login/')
def get_Ace_records_section_head(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    records = Ace.objects.filter(section=secction).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def get_Ace_records_requester(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    records = Ace.objects.filter(section=secction).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index_requester.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def get_Ace_records_pettyauthoriser(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    records = Ace.objects.order_by('date_created').all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index_requester.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def get_to_approve_Ace(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    if request.method == "GET":
        Ace_id = request.GET['f']
        Ace_id = str(Ace_id)
        pettyc = Ace.objects.filter(petty_id=Ace_id).first()
        pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        pettyc.save()
        # print(pettyc)

        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)

        # QuerySet Object
        user_groups = list(l)
        user_id = request.user.id
        user = UserProfile.objects.filter(user_id=user_id).first()
        # secction = user.section
        # records = Ace.objects.filter(section=secction).all()
        # context = serializers.serialize('json', pettyc1)

    user_page = 'Ace/Ace_approve.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def final_approval(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()

    if request.method == "POST":
        Ace_id = request.POST['petty_id']

        pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()

        approval_status = "approved"
        pettyc1.approval_status = approval_status
        pettyc1.approved_by = user_title
        date_approved = datetime.now()
        pettyc1.date_rejected = date_approved
        pettyc1.save()

    user_page = 'Ace/Ace_approve.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def final_reject(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()

    if request.method == "GET":
        Ace_id = request.GET['f']

        pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        approval_status = "rejected"
        pettyc1.approval_status = approval_status
        pettyc1.rejected_by = user_title
        date_rejected = datetime.datetime.now()
        pettyc1.date_rejected = date_rejected
        pettyc1.save()
        # print(pettyc1)

    user_page = 'Ace/Ace_approve.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def get_Ace_records_disburser(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    # user = UserProfile.objects.filter(user_id=user_id).first()
    # secction = user.section

    records = Ace.objects.filter(approval_status="approved").all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def disburse(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()

    if request.method == "GET":
        Ace_id = request.GET['f']

        pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        # print(pettyc1)

    user_page = 'Ace/disburse.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def disburse_final(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()

    if request.method == "GET":
        Ace_id = request.GET['f']

        pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        disbursal_status = "disbursed"
        pettyc1.disbursal_status = disbursal_status
        pettyc1.disbursed_by = user_title
        date_disbursed = datetime.now()
        pettyc1.disbursal_date = date_disbursed
        pettyc1.save()
        # print(pettyc1)

    user_page = 'Ace/disburse.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def quotation_download(request):
    filename = request.GET['f']

    try:
        filepath = os.path.join(settings.BASE_DIR, filename)
        print("file path", filepath)
        return FileResponse(open(filepath, 'rb'), content_type='application/pdf')

    except FileNotFoundError:
        print("File not found")

    return redirect('/Ace/index/')


# requester,section_head,cashier,petty_cash_authoriser

@login_required(login_url='/accounts/login/')
def petty_reports(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section

    records = Ace.objects.filter(section=secction).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/pettty_reports.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

@login_required(login_url='/accounts/login/')
def generate_report(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    if request.method == "POST":
        start_date = request.POST['start_date']
        start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        end_date = request.POST['end_date']
        end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        print(start_date)
        print(end_date)
        records = Ace.objects.filter(section=secction, date_created__range=[start_date, end_date]).all()
        context = serializers.serialize('json', records)
        print(context)
        user_page = 'Ace/pettty_reports.html'
        return render(request, user_page, {"title": "All Records",
                                           "context": context,
                                           "user_title": user_title,
                                           "user_groups": user_groups})
    else:
        return redirect('/Ace/petty_reports/')

@login_required(login_url='/accounts/login/')
def create_budget(request):
    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    user_groups = user.groups.values_list('name', flat=True)

    custom_user_roles = {
        "non_conformity": {},
        "remittance_advice": {},
        "pettycash": {},
        "adjudication": {},
        "tokens": {},
        "tenders": {},
        "ace": {},
        "users": {},
    }

    user_group_ids = user_profile.roles
    user_group_ids = user_group_ids.split(",") if user_group_ids else []
    for id in user_group_ids:

        role = Roles.objects.filter(id=id).first()

        if role.application == "users":
            custom_user_roles["users"] = role

        if role.application == "non_conformity":
            custom_user_roles["non_conformity"] = role

        if role.application == "remittance_advice":
            custom_user_roles["remittance_advice"] = role

        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role

        if role.application == "adjudication":
            custom_user_roles["adjudication"] = role

        if role.application == "tokens":
            custom_user_roles["tokens"] = role

        if role.application == "tenders":
            custom_user_roles["tenders"] = role

        if role.application == "ace":
            custom_user_roles["ace"] = role

    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None

    if request.method == "POST":
        section_code =  section_used
        section = request.POST["section"]
        budget_name = request.POST["budget_name"]
        allocated = request.POST["allocated"]
        period = request.POST["Period"]
        region = request.POST["region"]
        created_date = datetime.now()
        balance = allocated
        withdrawn = 0
        budget_note = request.FILES["budget_note"]
        period=period.strip().split("-")[0]

        objectify = Budget (
            section_code = section_code,
            section = section,
            budget_name = budget_name,
            allocated = allocated,
            period = period,
            region = region,
            created_date = created_date,
            balance = balance,
            withdrawn = withdrawn,
            budget_note = budget_note

        )
        # print(objectify)
        objectify.save()

        return redirect('/Ace/budgets')

    else:
        user_title = request.user.get_full_name()
        section_budget = Budget.objects.filter(section = section_used).all()
        return render(request, 'Ace/budget_create.html', {"title": "Create budget",
                                                          "user_title": user_title,
                                                          "section_budget": section_budget})


def list_budgets():
    return None