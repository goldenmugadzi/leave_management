import os
from datetime import datetime
from random import randrange

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render, redirect

from it.users.models import Roles

UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
from .models import Pettycash, Quotation
from django.core import serializers


# Create your views here.
@login_required(login_url='/accounts/login/')
def index(request):
    user_title = request.user.get_full_name()

    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)

    if "pettycash_section_head" in user_groups:
        return redirect('/pettycash/list_section_head')
    if "pettycash_requester" in user_groups:
        return redirect('/pettycash/list_requester')
    if "pettycash_cashier" in user_groups:
        return redirect('/pettycash/list_disburser')
    if "pettycash_authoriser" in user_groups:
        return redirect('/pettycash/list_section_head')
    else:
        return redirect("/")

    return redirect("/")

@login_required(login_url='/accounts/login/')
def create_pettycash(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_groups = list(l)

    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section

    if request.method == "POST":
        Department = request.POST['department']
        location = request.POST['location']
        section = secction
        allocation_code_of_expenditure = request.POST['allocation_code_of_expenditure']
        details_of_expenditure = request.POST['details_of_expenditure']
        amount = request.POST['amount']
        # form = UploadFileForm(request.POST, request.FILES)
        quotation1 = request.FILES['quotation1']
        quotation2 = request.FILES['quotation2']
        quotation3 = request.FILES['quotation3']
        payment_mode = request.POST['payment_mode']
        requested_by = request.user.username

        # last_petty = Pettycash.objects.last()
        rand = randrange(1, 99)
        rand2 = str(rand)

        date = datetime.now()
        date = date.strftime("%Y%m%d")

        petty_id = "PC" + date + rand2

        objectify = Pettycash(
            Department=Department,
            location=location,
            section=section,
            allocation_code_of_expenditure=allocation_code_of_expenditure,
            details_of_expenditure=details_of_expenditure,
            amount=amount,
            payment_mode=payment_mode,
            requested_by=requested_by,
            petty_id=petty_id,
        )
        objectify.save()

        quotation1 = Quotation(
            pettycash=objectify,
            quotation_file=quotation1
        )
        quotation2 = Quotation(
            pettycash=objectify,
            quotation_file=quotation2
        )
        quotation3 = Quotation(
            pettycash=objectify,
            quotation_file=quotation3
        )
        quotation1.save()
        quotation2.save()
        quotation3.save()

        return redirect('/pettycash')

    return render(request, 'pettycash/pettycash_create.html', {"title": "Create",
                                                               "user_title": user_title,
                                                               "user_groups": user_groups})
@login_required(login_url='/accounts/login/')
def get_pettycash_records_requester(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    records = Pettycash.objects.filter(section=secction).all()
    context = serializers.serialize('json', records)

    user_page = 'pettycash/index_requester.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})



@login_required(login_url='/accounts/login/')
def get_pettycash_records_section_head(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    records = Pettycash.objects.filter(section=secction).all()
    context = serializers.serialize('json', records)

    user_page = 'pettycash/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def get_pettycash_records_pettyauthoriser(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    records = Pettycash.objects.order_by('date_created').all()
    context = serializers.serialize('json', records)

    user_page = 'pettycash/index_requester.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

@login_required(login_url='/accounts/login/')
def get_pettycash_records_disburser(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    # user = UserProfile.objects.filter(user_id=user_id).first()
    # secction = user.section

    records = Pettycash.objects.filter(approval_status="approved").all()
    context = serializers.serialize('json', records)

    user_page = 'pettycash/index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
                                       "user_title": user_title,
                                       "user_groups": user_groups})



@login_required(login_url='/accounts/login/')
def get_to_approve_pettycash(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    if request.method == "GET":
        pettycash_id = request.GET['f']
        pettycash_id = str(pettycash_id)
        pettyc = Pettycash.objects.filter(petty_id=pettycash_id).first()
        pettyc1 = Pettycash.objects.filter(petty_id=pettycash_id).first()
        pettyc.save()
        # print(pettyc)

        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)

        # QuerySet Object
        user_groups = list(l)
        user_id = request.user.id
        user = UserProfile.objects.filter(user_id=user_id).first()
        # secction = user.section
        # records = Pettycash.objects.filter(section=secction).all()
        # context = serializers.serialize('json', pettyc1)

    user_page = 'pettycash/pettycash_approve.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required(login_url='/accounts/login/')
def approval(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()

    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    user_groups = user.groups.values_list('name', flat=True)

    custom_user_roles = {
        "pettycash": {},
    }

    user_group_ids = user_profile.roles
    user_group_ids = user_group_ids.split(",") if user_group_ids else []
    for id in user_group_ids:

        role = Roles.objects.filter(id=id).first()
        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role


    pettycash_role=str(custom_user_roles["pettycash"].role)
    if request.method == "POST":
        pettycash_id = request.POST['petty_id']

        pettyc1 = Pettycash.objects.filter(petty_id=pettycash_id).first()

        if pettycash_role == "approve" and pettyc1.section_head_approval != "approved by section head":
            approval_status = "approved by section head"
            pettyc1.approval_status = approval_status
            pettyc1.section_head = user_title
            date_approved = datetime.now()
            pettyc1.section_head_approval_date = date_approved
            pettyc1.section_head_approval = approval_status
            pettyc1.section_head_comment = request.POST['comment']
            pettyc1.save()

        elif pettycash_role == "authoriser" and pettyc1.petty_authoriser_approval != "approved by pettycash authoriser":
            approval_status = "approved by pettycash authoriser"
            pettyc1.approval_status = approval_status
            pettyc1.petty_authoriser = user_title
            date_approved = datetime.now()
            pettyc1.petty_authoriser_approval_date = date_approved
            pettyc1.petty_authoriser_approval = approval_status
            pettyc1.petty_authoriser_comment = request.POST['comment']
            pettyc1.save()

        elif pettycash_role == "disburser" and pettyc1.disburser_approval != "disbursed":
            approval_status = "disbursed"
            pettyc1.approval_status = approval_status
            pettyc1.disbursed_by = user_title
            date_approved = datetime.now()
            pettyc1.disbursal_date = date_approved
            pettyc1.disbursed = approval_status
            pettyc1.disburser_comment = request.POST['comment']
            pettyc1.save()

    user_page = 'pettycash/pettycash_approve.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
                                       "user_title": user_title,
                                       "user_groups": user_groups})

def rejection(request):
    global pettyc1
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object
    user_groups = list(l)
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()

    user_profile = UserProfile.objects.filter(user_id=user.pk).first()

    user_groups = user.groups.values_list('name', flat=True)

    custom_user_roles = {
        "pettycash": {},
    }

    user_group_ids = user_profile.roles
    user_group_ids = user_group_ids.split(",") if user_group_ids else []
    for id in user_group_ids:

        role = Roles.objects.filter(id=id).first()
        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role


    pettycash_role=str(custom_user_roles["pettycash"].role)
    if request.method == "POST":
        pettycash_id = request.POST['petty_id']

        pettyc1 = Pettycash.objects.filter(petty_id=pettycash_id).first()

        if pettycash_role == "approve" and pettyc1.section_head_approval != "rejected by section head":
            approval_status = "rejected by section head"
            pettyc1.approval_status = approval_status
            pettyc1.section_head = user_title
            date_approved = datetime.now()
            pettyc1.section_head_approval_date = date_approved
            pettyc1.section_head_approval = approval_status
            pettyc1.section_head_comment = request.POST['comment']
            pettyc1.save()

        elif pettycash_role == "authoriser" and pettyc1.petty_authoriser_approval != "rejected by pettycash authoriser":
            approval_status = "rejected by pettycash authoriser"
            pettyc1.approval_status = approval_status
            pettyc1.petty_authoriser = user_title
            date_approved = datetime.now()
            pettyc1.petty_authoriser_approval_date = date_approved
            pettyc1.petty_authoriser_approval = approval_status
            pettyc1.petty_authoriser_comment = request.POST['comment']
            pettyc1.save()

        elif pettycash_role == "disburser" and pettyc1.disburser_approval != "rejected by disburser":
            approval_status = "rejected by disburser"
            pettyc1.approval_status = approval_status
            pettyc1.disbursed_by = user_title
            date_approved = datetime.now()
            pettyc1.disbursal_date = date_approved
            pettyc1.disbursed = approval_status
            pettyc1.disburser_comment = request.POST['comment']
            pettyc1.save()

    user_page = 'pettycash/pettycash_reject.html'

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
        pettycash_id = request.GET['f']

        pettyc1 = Pettycash.objects.filter(petty_id=pettycash_id).first()
        approval_status = "rejected"
        pettyc1.approval_status = approval_status
        pettyc1.rejected_by = user_title
        date_rejected = datetime.datetime.now()
        pettyc1.date_rejected = date_rejected
        pettyc1.save()
        # print(pettyc1)

    user_page = 'pettycash/pettycash_approve.html'

    return render(request, user_page, {"title": "All Records",
                                       "context": pettyc1,
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
        pettycash_id = request.GET['f']

        pettyc1 = Pettycash.objects.filter(petty_id=pettycash_id).first()
        # print(pettyc1)

    user_page = 'pettycash/disburse.html'

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
        pettycash_id = request.GET['f']

        pettyc1 = Pettycash.objects.filter(petty_id=pettycash_id).first()
        disbursal_status = "disbursed"
        pettyc1.disbursal_status = disbursal_status
        pettyc1.disbursed_by = user_title
        date_disbursed = datetime.now()
        pettyc1.disbursal_date = date_disbursed
        pettyc1.save()
        # print(pettyc1)

    user_page = 'pettycash/disburse.html'

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

    return redirect('/pettycash/index/')


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

    records = Pettycash.objects.filter(section=secction).all()
    context = serializers.serialize('json', records)

    user_page = 'pettycash/pettty_reports.html'
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
        records = Pettycash.objects.filter(section=secction, date_created__range=[start_date, end_date]).all()
        context = serializers.serialize('json', records)
        print(context)
        user_page = 'pettycash/pettty_reports.html'
        return render(request, user_page, {"title": "All Records",
                                           "context": context,
                                           "user_title": user_title,
                                           "user_groups": user_groups})
    else:
        return redirect('/pettycash/petty_reports/')