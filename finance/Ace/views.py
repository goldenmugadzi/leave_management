import os
import csv
Notification = apps.get_model(app_label='users', model_name='Notification')


# import self as self
import sweetify
from datetime import datetime
from random import randrange

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date

# from openpyxl.reader.excel import load_workbook

# from numpy.distutils.fcompiler import none

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


    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
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

    Ace_role=custom_user_roles["ace"].role
    print(Ace_role)

    if str(Ace_role)=="pass":
        return redirect('/ace/list_section_head')
    if str(Ace_role)=="create":
        return redirect('/ace/list_requester')
    if str(Ace_role)=="process":
        return redirect('/ace/list_accounting_officer')
    if str(Ace_role)=="sanction":
        return redirect('/ace/list_fm')
    if str(Ace_role)=="approve":
        return redirect('/ace/list_gm')
    else:
        messages.error(request, 'you need to contact it to get a role in the ACE')
        sweetify.success(request,'you need to contact it to get a role in the ACE')
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

    # print(user_profile.designation)
    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None
    # print(user_designation)

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
    section_budgets = Budget.objects.all()

    section_budgets=list(section_budgets)
    print(section_budgets)


    # print(section_budgets)
    # l = request.user.groups.values_list('name', flat=True)
    # # QuerySet Object
    # user_groups = list(l)
    #
    # user_id = request.user.id
    # user = UserProfile.objects.filter(user_id=user_id).first()
    # secction = user.section

    if request.method == "POST":
        department = request.POST['department']
        print("now in post brackets")
        location = district
        section = request.POST['section']
        # section = secction
        Details_of_Expenditure = request.POST['details_of_exp']
        # Designation = request.POST['designation']
        amount = request.POST['amount']
        # payment_mode = request.POST['payment_mode']
        # region = request.POST['region']
        # form = UploadFileForm(request.POST, request.FILES)
        if 'quotation1' in request.FILES:
            # File exists, do something with it
            quotation1 = request.FILES['quotation1']
        else:
            # File doesn't exist, handle the empty case
            quotation1 = None

        if 'quotation2' in request.FILES:
            # File exists, do something with it
            quotation2 = request.FILES['quotation2']
        else:
            # File doesn't exist, handle the empty case
            quotation2 = None

        if 'quotation3' in request.FILES:
            # File exists, do something with it
            quotation3 = request.FILES['quotation3']
        else:
            # File doesn't exist, handle the empty case
            quotation3 = None
        # quotation1 = request.FILES['quotation1']
        # quotation2 = request.FILES['quotation2']
        # quotation3 = request.FILES['quotation3']

        requested_by = request.user.username
        classification= request.POST['classification1']
        budget_id = request.POST['budget']
        print(budget_id + "  budget id")
        budget_id = Budget.objects.filter(budget_id=budget_id).first()
        print(budget_id.to_be_withdrawn)
        amount=float(amount)
        to_be_withdrawn= float(budget_id.balance)
        sweetify.success(request, 'The pending aces have drawn more than the budget can handle!')
        balance= float(budget_id.balance)
        quantity = request.POST['quantity']

        if to_be_withdrawn<balance or amount<balance:
            if classification=="project":

                present_tariff = request.POST['present_tariff']
                present_fmc = request.POST['present_fmc']
                capital_contribution = request.POST['capital_contribution']
                materials = request.POST['materials']
                connection_fee = request.POST['connection_fee']
                labour = request.POST['labour']
                transport = request.POST['transport']
                total_connection_fee = present_tariff + materials + connection_fee + labour + transport

            elif classification=="internal":

                present_tariff = ""
                present_fmc = ""
                capital_contribution = ""
                materials = ""
                connection_fee = ""
                labour = ""
                transport = ""
                total_connection_fee = ""

            # last_petty = Ace.objects.last()
            rand = randrange(1, 99)
            rand2 = str(rand)

            date = datetime.now()
            date_created = date
            date = date.strftime("%Y%m%d")
            print(budget_id)

            ace_id = "ACE" + date + rand2
            print(region)

            objectify = Ace(
                Department=department,
                location=location,
                section=section_used,
                allocation_code_of_expenditure=section,
                details_of_expenditure=Details_of_Expenditure,
                amount=amount,
                quotation1=quotation1 or None,
                quotation2=quotation2 or None,
                quotation3=quotation3 or None,
                # payment_mode=payment_mode,
                requested_by=requested_by,
                Ace_id2=ace_id,
                date_created=date_created,
                approval_status="created by " + requested_by,
                budget_id =budget_id,
                designation = user_designation,
                region=region,
                classification=classification,
                present_tariff=present_tariff or None,
                present_fmc=present_fmc or None,
                capital_contribution=capital_contribution or None,
                materials=materials or None,
                connection_fee=connection_fee or None,
                labour=labour or None,
                transport=transport or None,
                total_connection_fee=total_connection_fee or None,
                quantity=quantity,
            )
            objectify.save()
            # ace instance
            ace = ace_id
            ace_id=Ace.objects.filter(Ace_id2=ace_id).first()
            # transacctions
            objectify2 = Transactions(
                Ace_id2=ace_id,
                details_of_expenditure=Details_of_Expenditure,
                approval_status="created",
                region=region,
                amount=amount,
                ace2= ace,
                budget=budget_id,
            )
            objectify2.save()

            # Notification.objects.create(
            #     user=requested_by,
            #     message=f"Response from {request.user.username} on nonconformity: {Details_of_Expenditure}",
            #     url=nonconformity.get_absolute_url()
            # )

            # budgets calculations
            amount=float(amount)
            budget_id.to_be_withdrawn=to_be_withdrawn+amount
            budget_id.withdrawal_date=date_created

            budget_id.save()
            sweetify.success(request, 'You successfully created an ACE ')


        elif budget_id.to_be_withdrawn>=budget_id.balance:
            messages.error(request, 'The pending aces ave drawn more than the budget can handle!')
            sweetify.success(request, 'The pending aces ave drawn more than the budget can handle!')
            return redirect('/ace/create')

        elif amount>=budget_id.balance:
            messages.error(request, 'The pending aces ave drawn more than the budget can handle!')
            sweetify.success(request, 'The pending aces have drawn more than the budget can handle!')
            return redirect('/ace/create')

        else:
            messages.error(request, 'please redo the ace')
            sweetify.success(request, 'please redo the ace')
            return redirect('/ace/create')



        # new_transaction = new_transaction-amount

        messages.error(request, 'ace succesfully created',ace_id)
        sweetify.success(request, 'ace succesfully created')

        return redirect('/ace')
    user_page = 'ace/Ace_Create.html'

    return render(request, user_page, {"title": "Create",
                                                   "user_title": user_title,
                                                   "section_budget": section_budgets})


@login_required(login_url='/accounts/login/')
def get_Ace_records_section_head(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()

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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")

    # QuerySet Object
    user_groups = list(l)

    # secction = user.section
    print(section_used)

    records = Ace.objects.filter(section=section_used).all()
    context = serializers.serialize('json', records)

    user_page = 'ace/index.html'
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "ace_role": Ace_role})

def get_Ace_records_accounting_officer(request):

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")

    # QuerySet Object
    user_groups = list(l)
    approval_status = "approved by section head"

    records: object = Ace.objects.filter(approval_status=approval_status).all()
    context = serializers.serialize('json', records)

    user_page = 'ace/index.html'
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "ace_role": Ace_role})

def get_Ace_records_fm(request):

    # print(user_designation)

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()

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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")

    # secction = user.section
    print(section_used)
    approval_status = "approved by Accounting officer"

    records: object = Ace.objects.filter(approval_status=approval_status).all()
    context = serializers.serialize('json', records)

    user_page = 'ace/index.html'
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "ace_role": Ace_role})

def get_Ace_records_gm(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()

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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")

    # QuerySet Object
    user_groups = list(l)

    # secction = user.section
    # print(section_used)
    approval_status = "approved by Finance Manager"

    records: object = Ace.objects.filter(approval_status=approval_status).all()
    context = serializers.serialize('json', records)

    user_page = 'ace/index.html'
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "ace_role": Ace_role})

@login_required(login_url='/accounts/login/')
def get_Ace_records_requester(request):

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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    requested_by = request.user.username

# QuerySet Object
    user_groups = list(l)
    # user_id = request.user.id
    # user = UserProfile.objects.filter(user_id=user_id).first()
    # secction = user.section
    records = Ace.objects.filter(requested_by=requested_by).all()
    context = serializers.serialize('json', records)

    user_page = 'ace/index_requester.html'
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "ace_role": Ace_role})


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

    user_page = 'ace/index_requester.html'
    # print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def get_to_approve_Ace(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    section_budgets = Budget.objects.all()

    section_budgets=list(section_budgets)

    # print(section_budgets)

    if request.method == "GET":
        Ace_id = request.GET['i']
        # print(Ace_id)
        Ace_id = str(Ace_id)
        ace_id = Ace_id
        pettyc = Ace.objects.filter(Ace_id2=Ace_id).first()
        budget = pettyc.budget_id
        # print(budget)
        budget = Budget.objects.filter(budget_name=budget).first()
        # pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        # print(pettyc)
        context = pettyc
        # print(context)
        # print(context.quotation1)
        # print("after context")
        user_id = request.user.id


    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    # print(user)
    user_id = str(user)
    print(user_id)
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
    Ace_role=str(custom_user_roles["ace"])
    # print(Ace_role,"ace role")
    if request.method=="POST":
        ace_id=request.POST["Ace_id2"]
        
        ace=Ace.objects.filter(Ace_id2=ace_id).first()
        budget=ace.budget_id
        budget = Budget.objects.filter(budget_name=budget).first()

        # if Ace_role=="check" and str(ace.approval_status)!="approved by foreperson":
        #
        #     ace.approval_status="approved by foreperson"
        #     ace.date_approved=date.today()
        #     ace.save()
        #     messages.error(request, 'you have approved ace',ace_id)
        #     sweetify.success(request,'you have approved ace'+ ace_id)
        #     return redirect("/ace")
        if Ace_role=="pass" and str(ace.approval_status)!="approved by section head":

            ace.approval_status="approved by section head"
            ace.approved_by=user_id
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_name=budget).first()
            ace.date_approved=date.today()

            ace.section_head_approval_status="approved by section head"
            ace.section_head_approval_date = date.today()
            ace.save()
            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="process" and str(ace.approval_status)!="approved by Accounting officer":
            asset_number: object=request.POST.getlist('asset_number[]')
            joined_asset_numbers = ','.join(item.strip() for item in asset_number)
            print(joined_asset_numbers)
            ace.approval_status="approved by Accounting officer"
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_name=budget).first()
            ace.approved_by=user_id
            ace.date_approved=date.today()
            ace.accounting_officer_approval_date=date.today()
            ace.accounting_officer_approval_status="approved by accounting officer"
            ace.asset_number=joined_asset_numbers
            ace.accounting_officer=user_id
            ace.save()
            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            print(date.today())
            return redirect("/ace")

        if Ace_role=="sanction" and str(ace.approval_status)!="approved by Finance Manager":

            ace.approval_status="approved by Finance Manager"
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_name=budget).first()
            ace.date_approved=date.today()
            ace.approved_by=user_id
            ace.fm_approval_status="approved by Finance Manager"
            ace.fm_date_approved=date.today()
            ace.finance_manager=user_id
            ace.save()
            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="approve" and str(ace.approval_status)=="approved by Finance Manager":

            print("You are a gm")
            budget=ace.budget_id
            amount=ace.amount
            budget = Budget.objects.filter(budget_name=budget).first()
            if float(budget.balance)>=amount:
                print("now in approval bracket")
                ace.approval_status="approved by General Manager"
                ace.date_approved=date.today()
                ace.approved_by=user_id
                ace.general_manager=user_id
                ace.gm_approval_status="approved by General Manager"
                ace.gm_date_approved=date.today()

                ace.save()
                Transaction = Transactions.objects.filter(Ace_id2=ace.Ace_id2).first()
                Transaction.approval_status="approved by General Manager"
                Transaction.save()
                budget.balance = budget.balance - amount
                budget.to_be_withdrawn = budget.to_be_withdrawn - amount
                budget.withdrawn = budget.withdrawn + amount
                budget.withdrawal_date = date.today
                budget.save()
                print("approved")
                return redirect("/ace")
            
            else:
                sweetify.error(request, 'you have insufficient funds to approve')
                return redirect("/ace")



            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            return redirect("/ace")
        if str(ace.approval_status)=="approved by General Manager":
            messages.error(request, 'The approval process for ace is complete',ace_id)
            sweetify.success(request,'The approval process for ace is complete'+ ace_id)

        else:
            messages.error(request, 'you have no rights to approve aces')
            sweetify.success(request, 'you have no rights to approve aces')
            return redirect("/ace")


    user_title = request.user.get_full_name()

        # secction = user.section
        # records = Ace.objects.filter(section=secction).all()
        # context = serializers.serialize('json', pettyc1)


    pettyc = Ace.objects.filter(Ace_id2=ace_id).first()
    budget = pettyc.budget_id
    # print(budget)
    budget = Budget.objects.filter(budget_name=budget).first()
    # pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
    quantity = range(pettyc.quantity)
    # print(pettyc)
    context = pettyc

    # print(context.classification)
    if str(Ace_role)=="process":
        if str(context.classification)=="internal":
            user_page = 'ace/Ace_approve_accounting_officer_internal.html'
        else:
            user_page = 'ace/Ace_approve_accounting_officer_project.html'


    else:
        if str(context.classification)=="internal":
            user_page = 'ace/Ace_approve_internal.html'
        if str(context.classification)=="project":
            user_page = 'ace/Ace_approve_project.html'

    # print(user_page)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "budgets": section_budgets,
                                       "budget": budget,
                                       "quantity": quantity})

def get_to_reject_Ace(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    if request.method == "GET":
        Ace_id = request.GET['i']
        print(Ace_id)
        Ace_id = str(Ace_id)
        pettyc = Ace.objects.filter(Ace_id2=Ace_id).first()
        # pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        # print(pettyc)
        context = pettyc
        # print(context)
        # print(context.quotation1)
        # print("after context")
        user_id = request.user.id


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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")
    if request.method=="POST":
        ace_id=request.POST["Ace_id2"]
        rejection_reason=request.POST["rejection_reason"]
        # asset_number=request.POST["asset_number"]
        ace=Ace.objects.filter(Ace_id2=ace_id).first()
        budget=ace.budget_id
        budget = Budget.objects.filter(budget_id=budget).first()

        # if Ace_role=="check" and str(ace.approval_status)!="approved by foreperson":
        #
        #     ace.approval_status="approved by foreperson"
        #     ace.date_approved=date.today()
        #     ace.save()
        #     messages.error(request, 'you have approved ace',ace_id)
        #     sweetify.success(request,'you have approved ace'+ ace_id)
        #     return redirect("/ace")
        if Ace_role=="pass" and str(ace.approval_status)!="approved by section head":

            ace.approval_status="rejected by section head"
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_id=budget).first()
            ace.date_rejected=date.today()
            ace.rejected_by=user_title
            ace.section_head_approval_status="rejected by section head"
            ace.accounting_officer_approval_date=date.today()
            ace.rejection_reason=rejection_reason
            ace.section_head_rejection_reason=rejection_reason
            ace.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="process" and str(ace.approval_status)!="approved by Accounting officer":

            ace.approval_status="rejected by Accounting officer"
            ace.date_rejected=date.today()
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_id=budget).first()
            ace.rejected_by=user_title
            ace.accounting_officer_approval_date=date.today()
            ace.accounting_officer_approval_status="rejected by accounting officer"
            ace.rejection_reason=rejection_reason
            ace.accounting_officer_rejection_reason=rejection_reason
            # ace.asset_number=asset_number
            ace.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="sanction" and str(ace.approval_status)!="approved by Finance Manager":

            ace.approval_status="rejected Finance Manager"
            ace.date_approved=date.today()
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_id=budget).first()
            ace.fm_approval_status="rejected Finance Manager"
            ace.fm_date_approved=date.today()
            ace.finance_manager=user_title
            ace.rejection_reason=rejection_reason
            ace.fm_rejection_reason=rejection_reason
            ace.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="approve" and str(ace.approval_status)!="approved by Finance Manager":

            ace.approval_status="rejected by General Manager"
            ace.date_approved=date.today()
            budget=ace.budget_id
            budget = Budget.objects.filter(budget_id=budget).first()
            ace.gm_approval_status="approved by General Manager"
            ace.gm_date_approved=date.today()
            ace.general_manager=user_title
            ace.rejection_reason=rejection_reason
            ace.gm_rejection_reason=rejection_reason
            ace.save()
            Transaction = Transactions.objects.filter(Ace2=ace.Ace_id2).first()
            Transaction.approval_status="Rejected by General Manager"
            Transaction.save()

            budget=ace.budget_id
            amount=ace.amount
            budget = Budget.objects.filter(budget_id=budget).first()
            # budget.balance = budget.balance - amount
            budget.to_be_withdrawn = budget.to_be_withdrawn - amount
            # budget.withdrawn = budget.withdrawn + amount
            # budget.withdrawal_date = date.today
            budget.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if str(ace.approval_status)=="approved by General Manager":
            messages.error(request, 'The approval process for ace is complete',ace_id)
            sweetify.success(request,'The approval process for ace is complete'+ ace_id)

        else:
            messages.error(request, 'you have no rights to reject aces')
            sweetify.success(request, 'you have no rights to reject aces')
            return redirect("/ace")


    user_title = request.user.get_full_name()

    # secction = user.section
    # records = Ace.objects.filter(section=secction).all()
    # context = serializers.serialize('json', pettyc1)
    print(context.classification)
    if str(Ace_role)=="process":
        if str(context.classification)=="internal":
            user_page = 'ace/Ace_reject_accounting_officer_internal.html'
        else:
            user_page = 'ace/Ace_reject_accounting_officer_project.html'

    else:
        if str(context.classification)=="internal":
            user_page = 'ace/Ace_reject_internal.html'
        if str(context.classification)=="project":
            user_page = 'ace/Ace_reject_project.html'
    print(context)



    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups,
                                       "budget": budget})

@login_required(login_url='/accounts/login/')
def final_approval(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
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

    Ace_role=custom_user_roles["ace"].role
    print(Ace_role)

    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None


    if request.method == "POST":
        Ace_id = request.POST['Ace_id2']
        # budget=ace.budget_id
        # budget = Budget.objects.filter(budget_id=budget).first()

        Ace_1 = Ace.objects.filter(Ace_id2=Ace_id).first()
        # if r

        approval_status = "approved"
        Ace_1.approval_status = approval_status
        Ace_1.approved_by = user_title
        date_approved = datetime.now()
        Ace_1.date_rejected = date_approved
        Ace_1.save()

    user_page = 'ace/Ace_approve_project.html'

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

    user_page = 'ace/Ace_approve_project.html'

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

    user_page = 'ace/index.html'
    # print(context)

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

    user_page = 'ace/disburse.html'

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

    user_page = 'ace/disburse.html'

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
        # return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
        return FileResponse(open(filepath, 'rb'))
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

    records = Ace.objects.all()
    context = serializers.serialize('json', records)

    user_page = 'ace/index.html'
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
        user_page = 'ace/index.html'
        return render(request, user_page, {"title": "All Records",
                                           "context": context,
                                           "user_title": user_title,
                                           "user_groups": user_groups})
    else:
        return redirect('/Ace/reports/')

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
    sections = Sections.objects.filter(code=user_profile.section).first()

    if request.method == "POST":
        section =  request.POST["section"]
        section_code = section
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

        return redirect('/ace/budgets')

    else:
        user_title = request.user.get_full_name()
        section_budget = Budget.objects.filter(section = section_used).all()
        return render(request, 'Ace/budget_create.html', {"title": "Create budget",
                                                          "user_title": user_title,
                                                          "section_budget": section_budget,
                                                          "sections":sections})


@login_required(login_url='/accounts/login/')
def list_budgets(request):
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
    print(section_used)
    section_budget = Budget.objects.all()
    # print(section_budget)
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    context = serializers.serialize('json', section_budget)

    user_page = 'ace/budgets_index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

def upload_budgets(request):
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = User.objects.filter(id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    print("in view upload")

    user_groups = user.groups.values_list('name', flat=True)
    if request.method == 'POST':
        csvfile = request.FILES['file'] # file as key

        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            print("row: ", row)
            section_code = row['section_code']
            section = row['section']
            budget_name = row['budget']
            allocated = row['allocated']
            withdrawn = row['withdrawn']
            balance = row['balance']

            withdrawal_date = row['withdrawal_date']
            withdrawal_date = withdrawal_date.strip().split(" ")[0]
            if withdrawal_date!="null":

                withdrawal_date = datetime.strptime(withdrawal_date, "%Y-%m-%d")
            else:
                withdrawal_date = None


            awaiting_sanctioning = row['awaiting_sanctioning']
            period = int(row['period'])
            region = row['region']
            created_date = date.today()


            # withdrawal_date = datetime.strptime(row['withdrawal_date'], "%Y/%m/%d").strftime("%Y-%m-%d")
            # areas = row['area'].split(',')
            check_budget = Budget.objects.filter(budget_name=budget_name,period=period).first()
            budget_note = csvfile


            if check_budget:
                print("duplicate record ....")
            else:
                Budget.objects.create(section_code=section_code,
                                      section=section,
                                      budget_name=budget_name,
                                      allocated=allocated,
                                      withdrawn=withdrawn,
                                      balance=balance,
                                      withdrawal_date=withdrawal_date,
                                      awaiting_sanctioning=awaiting_sanctioning,
                                      period=period,
                                      region=region,
                                      created_date=created_date,
                                      budget_note=budget_note),
                print("record created")
        redirect("/ace/budgets")
        try:
            # ... view logic ...
            return HttpResponse("Budget uploaded successfully")
        except Exception as e:
            return HttpResponse("Error: {}".format(e))
        redirect("/ace/budgets")

    else:
        return render(request, 'ace/upload_budget.html',
                      {"title": "Upload budgets",
                      "user_title": user_title,
                    "user_groups": user_groups}
                      )


def view_ace(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    if request.method == "GET":
        Ace_id = request.GET['i']
        print(Ace_id)
        Ace_id = str(Ace_id)
        pettyc = Ace.objects.filter(Ace_id2=Ace_id).first()
        # pettyc1 = Ace.objects.filter(petty_id=Ace_id).first()
        # print(pettyc)
        context = pettyc
        # print(context)
        # print(context.quotation1)
        # print("after context")
        user_id = request.user.id


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
    Ace_role=str(custom_user_roles["ace"])
    print(Ace_role,"ace role")
    user_title = request.user.get_full_name()

    # secction = user.section
    # records = Ace.objects.filter(section=secction).all()
    # context = serializers.serialize('json', pettyc1)


    print(context.classification)
    if str(Ace_role)=="process":
        if str(context.classification)=="internal":
            user_page = 'ace/Ace_approve_accounting_officer_internal.html'
        else:
            user_page = 'ace/Ace_approve_accounting_officer_project.html'


    else:
        if str(context.classification)=="internal":
            user_page = 'ace/Ace_view_internal.html'
        if str(context.classification)=="project":
            user_page = 'ace/Ace_view_project.html'

    print(user_page)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})
