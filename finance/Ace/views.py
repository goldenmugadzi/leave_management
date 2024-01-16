import os


# import self as self
import sweetify
from datetime import datetime
from random import randrange

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date

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
    if str(Ace_role)=="process":
        return redirect('/ace/list_disburser')
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
        quotation1 = request.FILES['quotation1'] or ""
        quotation2 = request.FILES['quotation2'] or ""
        quotation3 = request.FILES['quotation3'] or ""

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

    return render(request, 'Ace/Ace_create.html', {"title": "Create",
                                                   "user_title": user_title,
                                                   "section_budget": section_budgets})


@login_required(login_url='/accounts/login/')
def get_Ace_records_section_head(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None
    # print(user_designation)

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)

    # secction = user.section
    print(section_used)

    records = Ace.objects.filter(section=section_used).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

def get_Ace_records_accounting_officer(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None
    # print(user_designation)

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)

    # secction = user.section
    print(section_used)
    approval_status = "approved by section head"

    records: object = Ace.objects.filter(approval_status=approval_status).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

def get_Ace_records_fm(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None
    # print(user_designation)

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)

    # secction = user.section
    print(section_used)
    approval_status = "approved by Accounting officer"

    records: object = Ace.objects.filter(approval_status=approval_status).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

def get_Ace_records_gm(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None
    # print(user_designation)

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)

    # secction = user.section
    # print(section_used)
    approval_status = "approved by Finance Manager"

    records: object = Ace.objects.filter(approval_status=approval_status).all()
    context = serializers.serialize('json', records)

    user_page = 'Ace/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

@login_required(login_url='/accounts/login/')
def get_Ace_records_requester(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    user_profile = UserProfile.objects.filter(user_id=user.pk).first()
    region = Regions.objects.filter(id=user_profile.region).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None
    # print(user_designation)

    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    requested_by = request.user.username

# QuerySet Object
    user_groups = list(l)
    # user_id = request.user.id
    # user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    records = Ace.objects.filter(requested_by=requested_by).all()
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
        asset_number=request.POST["asset_number"]
        ace=Ace.objects.filter(Ace_id2=ace_id).first()

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
            ace.date_approved=date.today()
            ace.section_head_approval_status="approved by section head"
            ace.accounting_officer_approval_date=date.today()
            ace.save()
            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="process" and str(ace.approval_status)!="approved by Accounting officer":

            ace.approval_status="approved by Accounting officer"
            ace.date_approved=date.today()
            ace.accounting_officer_approval_date=date.today()
            ace.accounting_officer_approval_status="approved by accounting officer"
            ace.asset_number=asset_number
            ace.save()
            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="sanction" and str(ace.approval_status)!="approved by Finance Manager":

            ace.approval_status="approved by Finance Manager"
            ace.date_approved=date.today()
            ace.fm_approval_status="approved by Finance Manager"
            ace.fm_date_approved=date.today()
            ace.save()
            messages.error(request, 'you have approved ace',ace_id)
            sweetify.success(request,'you have approved ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="approve" and str(ace.approval_status)!="approved by Finance Manager":


            budget=ace.budget_id
            amount=ace.amount
            budget = Budget.objects.filter(budget_id=budget).first()
            if float(budget.amount)<=amount:
                ace.approval_status="approved by General Manager"
                ace.date_approved=date.today()
                ace.gm_approval_status="approved by General Manager"
                ace.gm_date_approved=date.today()

                ace.save()
                Transaction = Transactions.objects.filter(Ace2=ace.Ace_id2).first()
                Transaction.approval_status="approved by General Manager"
                Transaction.save()
                budget.balance = budget.balance - amount
                budget.to_be_withdrawn = budget.to_be_withdrawn - amount
                budget.withdrawn = budget.withdrawn + amount
                budget.withdrawal_date = date.today
                budget.save()

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


    print(context.classification)
    if str(Ace_role)=="process":
        if str(context.classification)=="internal":
            user_page = 'Ace/Ace_approve_accounting_officer_internal.html'
        else:
            user_page = 'Ace/Ace_approve_accounting_officer_project.html'

    else:
        if str(context.classification)=="internal":
            user_page = 'Ace/Ace_approve_internal.html'
        if str(context.classification)=="project":
            user_page = 'Ace/Ace_approve_project.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

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
        asset_number=request.POST["asset_number"]
        ace=Ace.objects.filter(Ace_id2=ace_id).first()

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
            ace.date_approved=date.today()
            ace.section_head_approval_status="rejected by section head"
            ace.accounting_officer_approval_date=date.today()
            ace.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="process" and str(ace.approval_status)!="approved by Accounting officer":

            ace.approval_status="rejected by Accounting officer"
            ace.date_approved=date.today()
            ace.accounting_officer_approval_date=date.today()
            ace.accounting_officer_approval_status="rejected by accounting officer"
            ace.asset_number=asset_number
            ace.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="sanction" and str(ace.approval_status)!="approved by Finance Manager":

            ace.approval_status="rejected Finance Manager"
            ace.date_approved=date.today()
            ace.fm_approval_status="rejected Finance Manager"
            ace.fm_date_approved=date.today()
            ace.save()
            messages.error(request, 'you have rejected ace',ace_id)
            sweetify.success(request,'you have rejected ace'+ ace_id)
            return redirect("/ace")
        if Ace_role=="approve" and str(ace.approval_status)!="approved by Finance Manager":

            ace.approval_status="rejected by General Manager"
            ace.date_approved=date.today()
            ace.gm_approval_status="approved by General Manager"
            ace.gm_date_approved=date.today()
            ace.save()
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
            user_page = 'Ace/Ace_approve_accounting_officer_internal.html'
        else:
            user_page = 'Ace/Ace_approve_accounting_officer_project.html'

    else:
        if str(context.classification)=="internal":
            user_page = 'Ace/Ace_approve_internal.html'
        if str(context.classification)=="project":
            user_page = 'Ace/Ace_approve_project.html'



    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

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

        Ace_1 = Ace.objects.filter(Ace_id2=Ace_id).first()
        # if r

        approval_status = "approved"
        Ace_1.approval_status = approval_status
        Ace_1.approved_by = user_title
        date_approved = datetime.now()
        Ace_1.date_rejected = date_approved
        Ace_1.save()

    user_page = 'Ace/Ace_approve_project.html'

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

    user_page = 'Ace/Ace_approve_project.html'

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

    user_page = 'Ace/budgets_index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})