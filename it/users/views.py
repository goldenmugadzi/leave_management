# users/views.py

from datetime import timedelta
import json
import csv
from django.contrib.auth import login
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.sites import requests
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from openpyxl.reader.excel import load_workbook
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from django.contrib.auth.decorators import login_required
from approve.decorators import allowed_roles
from django.db.models import Q, Exists, OuterRef, Count, F
from exchangelib import Credentials, Account, Configuration, Message, Mailbox, HTMLBody
from django.conf import settings
import pandas as pd
from it.users.models import *
from it.users.forms import CustomUserCreationForm

from django.contrib.auth.models import Group
from .helpers import DESIGNATIONS, REGIONS, DISTRICTS, DEPOTS, ROLES, SECTIONS
from django.contrib import messages
from approve.decorators import allowed_roles
from django.core.paginator import Paginator
from decouple import config
from django.forms import inlineformset_factory
from .forms import ResponsibilitiesForm
from django.template.loader import get_template

BASE_URL = "http://" + config('HOST') + ":" + config('PORT')
APP_NAME = "users"


def getUserFMGMRoles(user):
    print("user: ", user.username, user.id)
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


def user_centers(request):
    users = UserProfile.objects.all()
    for user in users:
        section = user.section
        if section:
            cost_center = CostCenter.objects.filter(Q(id=section.code) | Q(id="CC" + section.code)).first()
            user.cost_center = cost_center
            user.save()
    return JsonResponse({"status": "success", "message": "Centers added successfully"})


def get_exchange_account():
    from decouple import config as cnf
    print(cnf)
    credentials = Credentials(
        username=cnf('MS_EMAIL'),
        password=cnf('MS_PASS')
    )
    print("Credentials: ", credentials)
    config = Configuration(
        server=cnf('MS_SERVER'),
        credentials=credentials,
    )
    print("Config: ", config)
    account = Account(
        primary_smtp_address=cnf('MS_PRIMARY_SMTP_ADDRESS'),
        config=config,
        autodiscover=False,
        access_type='delegate'
    )
    print("Successfully connected to Exchange server.")
    return account


@login_required
def ms_exhange_test(request, template, kwargs):
    account = get_exchange_account()
    message = get_template(f"{template}").render(kwargs["kwargs"])
    message = Message(
        account=account,
        folder=account.sent,
        subject="Test Email",
        body=message,
        to_recipients=[Mailbox(email_address='kcbosha@zetdc.co.zw'), Mailbox(email_address='mchivinge@zetdc.co.zw'),
                       Mailbox(email_address='amugwambi@zetdc.co.zw'), Mailbox(email_address='akwaramba@zetdc.co.zw')]
    )
    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})


def ms_exhange_send(subject, body, to_recipients, cc_recipients):
    try:
        account = get_exchange_account()
        message = Message(
            account=account,
            folder=account.sent,
            subject=subject,
            body=body,
            to_recipients=[Mailbox(email_address=recipient) for recipient in to_recipients],
            cc_recipients=[Mailbox(email_address=recipient) for recipient in cc_recipients]
        )
        message.send()
        return JsonResponse({"status": "success", "message": "Email sent successfully"})
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({"status": "error", "message": "An error occurred while sending the email: " + str(ex)})


def ms_exhange_send_html(subject, to_recipients, cc_recipients, template, kwargs):
    account = get_exchange_account()
    message_body = get_template(f"{template}").render(kwargs["kwargs"])
    message = Message(
        account=account,
        folder=account.sent,
        subject=subject,
        body=HTMLBody(message_body),
        to_recipients=[Mailbox(email_address=recipient) for recipient in to_recipients],
        cc_recipients=[Mailbox(email_address=recipient) for recipient in cc_recipients]
    )

    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})

def ms_exhange_reset_password_html(subject, to_recipients, cc_recipients, template, kwargs):
    account = get_exchange_account()
    # message_body = get_template(f"{template}").render(kwargs["kwargs"])
    message = Message(
        account=account,
        folder=account.sent,
        subject=subject,
        body=HTMLBody(template),
        to_recipients=[Mailbox(email_address=recipient) for recipient in to_recipients],
        cc_recipients=[Mailbox(email_address=recipient) for recipient in cc_recipients]
    )

    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})


@login_required
@allowed_roles(['Administrator'], ['users'])
def deactivate_user(request):
    if request.method == "GET":
        try:
            user = UserProfile.objects.get(id=request.GET['i'])
            user.is_active = False
            user.save()
            messages.success(request, "User deactivated successfully")
            return redirect('/users/users-index')
        except Exception as ex:
            print("Error: ", ex)
            messages.error(request, "An error occurred while deactivating the user: " + str(ex))
            return redirect('/users/users-index')
    else:
        return redirect('/users/users-index')
    
@login_required
@allowed_roles(['Administrator'], ['users'])
def activate_user(request):
    if request.method == "GET":
        try:    
            user = UserProfile.objects.get(id=request.GET['i'])
            user.is_active = True
            user.save()
            messages.success(request, "User activated successfully")
            return redirect('/users/users-index')
        except Exception as ex:
            print("Error: ", ex)
            messages.error(request, "An error occurred while activating the user: " + str(ex))
            return redirect('/users/users-index')
    else:
        return redirect('/users/users-index')


@login_required
@allowed_roles(['Administrator'], ['users'])
def add_centers(request):
    for region in REGIONS:
        _region = Regions(
            region=region['name'],
            code=region['code'],
        )
        _region.save()

    for district in DISTRICTS:
        region_id = Regions.objects.filter(code=district['parent_code']).first()
        _district = Districts(
            district=district['name'],
            code=district['code'],
            region_id=region_id.id
        )
        _district.save()

    for depot in DEPOTS:
        district_id = Districts.objects.filter(code=depot['district_code']).first()
        region_id = Regions.objects.filter(code=depot['parent_code']).first()
        _depot = Depots(
            depot=depot['name'],
            code=depot['code'],
            district_id=district_id.id,
            region_id=region_id.id
        )
        _depot.save()

    for designation in DESIGNATIONS:
        _designation = Designations(
            description=designation['description']
        )
        _designation.save()

    for role in ROLES:
        application_ = role['application']
        app_id = Application.objects.filter(name=application_).first()
        if app_id:
            _role = Roles(
                role=role['role'],
                name=role['name'],
                description=role['description'],
                application=role['application'],
                app_id=app_id
            )
            _role.save()
        else:
            new_app = Application(
                name=application_
            )
            new_app.save()
            _role = Roles(
                role=role['name'],
                name=role['name'],
                description=role['description'],
                application=role['application'],
                app_id=new_app
            )
            _role.save()

    for section in SECTIONS:
        _section = Sections(
            section=section['section'],
            code=section['code']
        )
        _section.save()

    return redirect('/users/users-index')


@login_required
@allowed_roles(['Administrator'], ['users'])
def add_user(request):
    if request.method == "GET":

        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)

        # get roles
        all_roles = {}
        user_applications = Application.objects.all()
        for app in user_applications:
            app_roles = Roles.objects.filter(app_id=app.id).all()
            all_roles[app.name] = app_roles

        # get designations
        user_designations = Designations.objects.all()
        sections = Sections.objects.all()
        cost_centers = CostCenter.objects.all()
        regions = Regions.objects.all()

        return render(
            request,
            "users/add_user.html",
            {
                "form": CustomUserCreationForm,
                "user_roles": all_roles,
                "user_applications": user_applications,
                "user_designations": user_designations,
                "cost_centers": cost_centers,
                "sections": sections,
                "regions": regions,
                "user_title": user_title,
                "user_groups": user_groups,
            }
        )
    elif request.method == "POST":
        try:
            firstnames = request.POST['firstname']
            lastnames = request.POST['lastname']
            username = request.POST['username']
            designation_ = request.POST['designation']
            email = request.POST['email']
            section_ = request.POST['section']
            cost_center = request.POST['cost_center']
            region_ = request.POST['region']
            password1 = request.POST['password1']
            password2 = request.POST['password2']

            region = None
            cost_center_ = None
            section = None
            designation = None
            try:
                region = Regions.objects.filter(id=region_).first() if region_ else None
                cost_center_ = CostCenter.objects.filter(id=cost_center).first() if cost_center else None
                section = Sections.objects.filter(code=section_).first() if section_ else None
                designation = Designations.objects.filter(id=designation_).first() if designation_ else None
            except Exception as ex:
                print("Error: ", ex)
                messages.error(request, "An error occurred while saving the user: " + ex.messages)

            if password1 == password2:
                user = UserProfile(
                    username=username,
                    first_name=firstnames,
                    last_name=lastnames,
                    email=email,
                    designation=designation,
                    cost_center=cost_center_,
                    section=section,
                    region=region,
                    status="active"
                )

                user.save()

                # Get actual Role objects:
                user_applications = Application.objects.all()
                roles = [role for role in
                         [request.POST.get(app.name) for app in user_applications if request.POST.get(app.name) != ""]
                         if role and role != ""]
                print("roles: ", roles)
                role_objects = Roles.objects.filter(id__in=roles)  # Example of retrieving roles
                user.roles.add(*role_objects)
                try:
                    validate_password(password1, user=user)
                    user.set_password(password1)
                    user.change_password = False
                    user.save()
                    # Password is valid
                except ValidationError as e:
                    # Password is not valid
                    print(e.messages)
                    messages.error(request, e.messages)
                    return redirect("/users/users-index")
            else:
                messages.error(request, "Passwords do not match")
                return redirect("/users/users-index")

            messages.success(request, "User created successfully")
        except Exception as ex:
            print("save user error", ex)
            messages.error(request, "An error occurred while saving the user: " + str(ex))

        return redirect("/users/users-index")

@login_required
@allowed_roles(['Administrator'], ['users'])
def get_user_records(request):
    user_page = 'users/user_index.html'
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)
    regions = Regions.objects.all()
    return render(
        request,
        user_page,
        {
            "title": "All Records",
            "user_title": user_title,
            "user_groups": user_groups,
            "regions": regions
        })


def datatable_data(request):
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    length = int(request.GET.get('length', default=10))
    search_value = request.GET.get('search[value]', default='')
    active = request.GET.get('active', default=True)
    region = request.GET.get('region', default='')
    print("active: ", active)
    user = request.user

    try:
        if user.region:
            if region:
                records = UserProfile.objects.filter(is_active=active, region=region).order_by('-id').all()
            else:
                records = UserProfile.objects.filter(is_active=active).order_by('-id').all()
            # Filter based on search value
            if search_value:
                records = records.filter(
                    Q(username__icontains=search_value) |
                    Q(first_name__icontains=search_value) |
                    Q(last_name__icontains=search_value) |
                    Q(email__icontains=search_value)
                )

            # Total number of records before filtering
            total = records.count()

            # Sorting
            order_column = request.GET.get('order[0][column]')
            order = request.GET.get('order[0][dir]')
            if order_column:
                column_name = request.GET.get(f'columns[{order_column}][data]')
                if order == 'desc':
                    column_name = f'-{column_name}'
                records = records.order_by(column_name)

            # Pagination
            paginator = Paginator(records, length)
            page_number = start // length + 1
            page_obj = paginator.get_page(page_number)

            # Prepare response
            data = []
            for obj in page_obj:
                try:
                    cost_center_name = obj.cost_center.name
                except Exception as ex:
                    print("Cost Center Error: ", ex)
                    cost_center_name = None

                data.append({
                    "id": obj.pk,
                    "username": obj.username,
                    "first_name": obj.first_name,
                    "last_name": obj.last_name,
                    "email": obj.email,
                    "cost_center": cost_center_name,
                    "region": obj.region.region if obj.region else None,
                    "active": obj.is_active,
                    "date_joined": obj.date_joined.date()
                })

            return JsonResponse({
                'draw': draw,
                'recordsTotal': total,
                'recordsFiltered': total,
                'data': data
                })
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({"status": "error", "message": "An error occurred while fetching the users"})

@login_required
@allowed_roles(['Administrator'], ['users'])
def update_user(request):
    if request.method == "GET":
        user_profile = UserProfile.objects.get(id=request.GET['i'])
        active_roles = {role.app_id.name: role for role in user_profile.roles.all() if role.app_id}

        section = None
        depot = None
        district = None
        region = None
        cost_center = None
        user_designation = None
        # cost_centers_ = CostCenter.objects.filter(Q(code=user_profile.region.code) | Q(code="CC" + user_profile.region.code)).all()
        cost_centers_ = []
        try:
            section = user_profile.section
            depot = user_profile.depot
            district = user_profile.district
            region = user_profile.region
            cost_center = user_profile.cost_center
            cost_centers_ = CostCenter.objects.filter(Q(parent=region.code) | Q(parent="CC" + region.code)).all()

            user_designation = user_profile.designation
        except Exception as ex:
            print("Error: ", ex)
        if not cost_center:
            try:
                cost_center = CostCenter.objects.filter(Q(code=region.code) | Q(code="CC" + region.code)).first()
            except:
                pass
        if not cost_center:
            try:
                cost_center = CostCenter.objects.filter(code='zesa').first()
            except:
                pass

        new_user = {
            "id": user_profile.pk,
            "username": user_profile.username,
            "firstname": user_profile.first_name,
            "lastname": user_profile.last_name,
            "email": user_profile.email,
            "section": section,
            "depot": depot,
            "district": district,
            "region": region,
            "cost_center": cost_center,
            "roles": active_roles,
            "designation": user_designation,
        }

        all_roles = {app.name: Roles.objects.filter(app_id=app.id).all() for app in Application.objects.all()}

        try:
            cost_center = user_profile.cost_center
            if not cost_center:
                try:
                    cost_center = CostCenter.objects.filter(code=depot.code).first()
                except:
                    pass
            if not cost_center:
                try:
                    cost_center = CostCenter.objects.filter(code=section.code).first()
                except:
                    pass
            if not cost_center:
                try:
                    cost_center = CostCenter.objects.filter(code=district.code).first()
                except:
                    pass
            if not cost_center:
                try:
                    cost_center = CostCenter.objects.filter(code=region.code).first()
                except:
                    pass
            if cost_center:
                cost_centers = cost_center.get_view()
            else:
                cost_centers = []
        except Exception as ex:
            print("Error: ", ex)
            cost_centers = []
        """for every application, initialize the responsibility formset for the user to be assigned roles and cost centers"""

        print("cost_centers: ", cost_centers)
        return render(
            request,
            "users/user_update.html",
            {"cost_centers": cost_centers,
             "cost_centers_": cost_centers_,
             "form": CustomUserCreationForm,
             "user_roles": all_roles,
             "user_applications": Application.objects.all(),
             "user_designations": Designations.objects.all(),
             "sections": Sections.objects.all(),
             "districts": Districts.objects.all(),
             "regions": Regions.objects.all(),
             "user_title": request.user.get_full_name(),
             "user_groups": list(request.user.groups.values_list('name', flat=True)),
             "user": new_user,
             "user_profile": user_profile
             }
        )
    elif request.method == "POST":
        try:

            user_profile = UserProfile.objects.filter(id=request.POST['user_id']).first()
            region = request.POST.get('region')
            # district = request.POST.get('district')
            # depot = request.POST.get('depot')
            section = request.POST.get('section')
            designation = request.POST.get('designation')
            cost_center = request.POST.get('cost_center')

            region_, section_, designation_, cost_center_ = None, None, None, None
            try:
                region_ = Regions.objects.filter(id=region).first() if region else None
                section_ = Sections.objects.filter(id=section).first() if section else None
                designation_ = Designations.objects.filter(id=designation).first() if designation else None
                cost_center_ = CostCenter.objects.filter(id=cost_center).first() if cost_center else None
            except Exception as ex:
                print("Error: ", ex)

            user_data = {
                'first_name': request.POST['firstname'],
                'last_name': request.POST['lastname'],
                'username': request.POST['username'],
                'email': request.POST['email'],
                'region': region_,
                'section': section_,
                'cost_center': cost_center_,
                'designation': designation_
            }

            for field, value in user_data.items():
                if value:
                    setattr(user_profile, field, value)

            user_profile.save()

            # roles = [role for role in [request.POST.get(app.name) for app in Application.objects.all() if request.POST.get(app.name) != 'Select Role'] if role and role != ""]
            # user_profile.roles.clear()
            # user_profile.roles.add(*Roles.objects.filter(id__in=roles))
            messages.success(request, "User updated successfully")
        except Exception as ex:
            print("save user error", ex)
            messages.error(request, "An error occurred while saving the user")

        return redirect("/users/users-index")


@login_required
@allowed_roles(['Administrator'], ['users'])
def set_requesters(request):
    if request.method == "GET":
        region = Regions.objects.filter(id=7).first()
        nc_app = Application.objects.filter(id=1).first()
        petty_app = Application.objects.filter(id=3).first()
        ace_app = Application.objects.filter(id=7).first()
        nc_requester = Roles.objects.filter(app_id=nc_app, role="recipient").first()
        petty_requester = Roles.objects.filter(app_id=petty_app, role="create").first()
        ace_requester = Roles.objects.filter(app_id=ace_app, role="create").first()
        ho_users = UserProfile.objects.filter(region=region).all()
        for user in ho_users:
            user.roles.clear()
            user.roles.add(ace_requester)
            user.roles.add(petty_requester)
            user.roles.add(nc_requester)
            user.save()
        
        return JsonResponse({"status": "success", "message": "Requesters set successfully"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"})
    
@login_required
def view_user(request):
    if request.method == "GET":
        user_profile = UserProfile.objects.get(id=request.user.id)
        active_roles = {role.app_id.name: role for role in user_profile.roles.all() if role.app_id}

        new_user = {
            "id": user_profile.pk,
            "username": user_profile.username,
            "firstname": user_profile.first_name,
            "lastname": user_profile.last_name,
            "email": user_profile.email,
            "section": Sections.objects.filter(id=user_profile.section.id).first() if user_profile.section else None,
            "depot": Depots.objects.filter(id=user_profile.depot.id).first() if user_profile.depot else None,
            "district": Districts.objects.filter(
                id=user_profile.district.id).first() if user_profile.district else None,
            "cost_center": CostCenter.objects.filter(
                id=user_profile.cost_center.id).first() if user_profile.cost_center else None,
            "region": Regions.objects.filter(id=user_profile.region.id).first() if user_profile.region else None,
            "roles": active_roles,
            "designation": Designations.objects.filter(
                id=user_profile.designation.id).first() if user_profile.designation else None,
        }

        all_roles = {app.name: Roles.objects.filter(app_id=app.id).all() for app in Application.objects.all()}

        return render(
            request,
            "users/view_user.html",
            {
                "form": CustomUserCreationForm,
                "user_roles": all_roles,
                "user_applications": Application.objects.all(),
                "user_designations": Designations.objects.all(),
                "sections": Sections.objects.all(),
                "districts": Districts.objects.all(),
                "regions": Regions.objects.all(),
                "user_title": request.user.get_full_name(),
                "user_groups": list(request.user.groups.values_list('name', flat=True)),
                "user": new_user
            }
        )


@login_required
@allowed_roles(['Administrator'], ['users'])
def update_userx(request):
    if request.method == "GET":

        id = request.GET['i']
        user_profile = UserProfile.objects.get(id=id)

        user_groups = user_profile.groups.values_list('name', flat=True)

        # get roles
        active_roles = {}

        new_user = None
        region = None
        district = None
        depot = None
        section = None
        user_designation = None
        if user_profile:
            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                app = _role.app_id
                if app:
                    active_roles[app.name] = role

            region = Regions.objects.filter(id=user_profile.region.id).first() if user_profile.region else None
            district = Districts.objects.filter(id=user_profile.district.id).first() if user_profile.district else None
            depot = Depots.objects.filter(id=user_profile.depot.id).first() if user_profile.depot else None
            section = Sections.objects.filter(id=user_profile.section.id).first() if user_profile.section else None
            user_designation = Designations.objects.filter(
                id=user_profile.designation.id).first() if user_profile.designation else None

        new_user = {
            "id": user_profile.pk,
            "username": user_profile.username,
            "firstname": user_profile.first_name,
            "lastname": user_profile.last_name,
            "email": user_profile.email,
            "section": section,
            "depot": depot,
            "district": district,
            "region": region,
            "roles": active_roles,
            "designation": user_designation,
        }

        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)

        # get roles
        all_roles = {}
        user_applications = Application.objects.all()
        for app in user_applications:
            app_roles = Roles.objects.filter(app_id=app.id).all()
            all_roles[app.name] = app_roles
        user_designations = Designations.objects.all()
        sections = Sections.objects.all()
        districts = Districts.objects.all()
        regions = Regions.objects.all()

        return render(
            request,
            "users/user_update.html",
            {
                "form": CustomUserCreationForm,
                "user_roles": all_roles,
                "user_applications": user_applications,
                "user_designations": user_designations,
                "sections": sections,
                "districts": districts,
                "regions": regions,
                "user_title": user_title,
                "user_groups": user_groups,
                "user": new_user
            }
        )
    elif request.method == "POST":
        # try:
        id = request.POST['user_id']
        firstnames = request.POST['firstname']
        lastnames = request.POST['lastname']
        username = request.POST['username']
        email = request.POST['email']
        section_ = request.POST['section']
        print("depot", request.POST['depot'] or None)
        depot_ = request.POST['depot'] or None
        district_ = request.POST['district']
        region_ = request.POST['region']
        designation_ = request.POST['designation']

        region = Regions.objects.filter(id=region_).first()
        district = Districts.objects.filter(id=district_).first() if (district_ != "Select District" or "") else None
        depot = Depots.objects.filter(id=depot_).first() if (depot_ != "Select Depot" or "") else None
        section = Sections.objects.filter(code=section_).first()
        designation = Designations.objects.filter(id=designation_).first() if (
                designation_ != "Select Designation" or "") else None

        user_profile = UserProfile.objects.filter(id=id).first()
        user_data = {
            'first_name': firstnames,
            'last_name': lastnames,
            'username': username,
            'email': email,
            'region': region,
            'district': district,
            'depot': depot,
            'section': section,
            'designation': designation
        }

        for field, value in user_data.items():
            if value:
                setattr(user_profile, field, value)

        user_profile.save()

        # Get actual Role objects:
        user_applications = Application.objects.all()
        roles = [role for role in [request.POST.get(app.name) for app in user_applications if
                                   request.POST.get(app.name) != 'Select Role'] if role and role != ""]
        print("roles: ", roles)

        role_objects = Roles.objects.filter(id__in=roles)  # Example of retrieving roles
        user_profile.roles.clear()
        user_profile.roles.add(*role_objects)

        # except Exception as ex:
        #     print("save user error", ex)

        return redirect("/users/users-index")


@login_required
@allowed_roles(['Administrator'], ['users'])
def reset_user_password(request):
    if request.method == "POST":

        id = request.POST['item']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            user_profile = UserProfile.objects.filter(id=id).first()
            try:
                validate_password(password1, user=user_profile)
                user_profile.change_password = True
                user_profile.password_expiry_date = date.today() + timedelta(days=user_profile.password_expiry_days)
                user_profile.save()
                user_profile.set_password(password1)
                user_profile.save()
                messages.success(request, "Password reset successfull")
                return redirect('/users/users-index')
            except ValidationError as e:
                # Password is not valid
                print(e.messages)
                messages.error(request, e.messages)
                return redirect('/users/users-index')

    elif request.method == "GET":

        id = request.GET['i']
        user_page = 'users/user_reset.html'
        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)

        return render(
            request,
            user_page,
            {
                "user_title": user_title,
                "user_groups": user_groups,
                "item": id
            })

    return redirect('/users/users-index')


@login_required
def change_user_password(request):
    if request.method == "POST":

        user_id = request.user.id
        current_password = request.POST['current_password']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            user_profile = UserProfile.objects.filter(id=user_id).first()
            if user_profile.check_password(current_password):
                try:
                    validate_password(password1, user=user_profile)
                    user_profile.set_password(password1)
                    user_profile.save()
                    print("Password changed successfully")
                except ValidationError as e:
                    # Password is not valid
                    print(e.messages)
                    messages.error(request, e.messages)
                    return redirect('/dashboards/overview/')
            else:
                print("Current password is incorrect. Password not changed.")

        messages.success(request, "Password changed successfully")
        return redirect('/accounts/login')

    elif request.method == "GET":

        user_page = 'users/user_change_password.html'
        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)

        return render(
            request,
            user_page,
            {
                "user_title": user_title,
                "user_groups": user_groups,
            })

    return redirect('/dashboards/overview')


def get_sections(request):
    sections = Sections.objects.all()
    return JsonResponse(list(sections.values('id', 'section')), safe=False)


def get_cost_centers(request):
    cost_centers = CostCenter.objects.all()
    return JsonResponse(list(cost_centers.values('id', 'name')), safe=False)


def get_regions(request):
    regions = Regions.objects.all()
    return JsonResponse(list(regions.values('id', 'region')), safe=False)


@login_required
def get_filtered_centers(request, region_id):
    region = Regions.objects.filter(id=region_id).first()
    filtered_centers = []
    if region:
        print("Region: ", region.code)
        cost_center = CostCenter.objects.filter(Q(code=region.code) | Q(code="CC" + region.code)).first()
        print("Cost Center: ", cost_center)
    filtered_centers = fetch_center_children(cost_center)
    filtered_centers = [center for center in filtered_centers if center['name'] != " >>> No valid master record"]

    return JsonResponse(filtered_centers, safe=False)


def get_center_parents(request, center_code):
    filtered_centers = []
    cost_center = CostCenter.objects.filter(Q(code=center_code) | Q(code="CC" + center_code)).first()
    print("Cost Center: ", cost_center)
    filtered_centers = fetch_center_parents(cost_center)

    return JsonResponse(filtered_centers, safe=False)


def fetch_center_children(cost_center):
    filtered_centers = []
    if cost_center:
        filtered_centers_1 = CostCenter.objects.filter(parent=cost_center.id).all().values('id', 'name')
        filtered_centers += filtered_centers_1
        for center in filtered_centers_1:
            print("Center 1: ", center)
            filtered_centers_2 = CostCenter.objects.filter(parent=center['id']).all().values('id', 'name')
            filtered_centers += filtered_centers_2
            for _center in filtered_centers_2:
                print("Center 2: ", _center)
                filtered_centers_3 = CostCenter.objects.filter(parent=_center['id']).all().values('id', 'name')
                filtered_centers += filtered_centers_3
                for _center2 in filtered_centers_3:
                    print("Center 3: ", _center2)
                    filtered_centers_4 = CostCenter.objects.filter(parent=_center2['id']).all().values('id', 'name')
                    filtered_centers += filtered_centers_4
    return filtered_centers


def fetch_center_parents(cost_center):
    filtered_centers = []
    if cost_center:
        filtered_centers_1 = CostCenter.objects.filter(id=cost_center.parent).all().values('id', 'name', 'parent')
        filtered_centers += filtered_centers_1
        for center in filtered_centers_1:
            print("Center 1: ", center)
            filtered_centers_2 = CostCenter.objects.filter(id=center['parent']).all().values('id', 'name', 'parent')
            filtered_centers += filtered_centers_2
            for _center in filtered_centers_2:
                print("Center 2: ", _center)
                filtered_centers_3 = CostCenter.objects.filter(id=_center['parent']).all().values('id', 'name',
                                                                                                  'parent')
                filtered_centers += filtered_centers_3
                for _center2 in filtered_centers_3:
                    print("Center 3: ", _center2)
                    filtered_centers_4 = CostCenter.objects.filter(id=_center2['parent']).all().values('id', 'name',
                                                                                                       'parent')
                    filtered_centers += filtered_centers_4
    return filtered_centers


@login_required
# @allowed_roles(['administrator'], ['users'])
def get_filtered_districts(request, region_id):
    print("Region ID: ", region_id)
    districts = Districts.objects.filter(region_id=region_id).all()
    print("Districts: ", districts)
    return JsonResponse(list(districts.values('id', 'district')), safe=False)


@login_required
# @allowed_roles(['administrator'], ['users'])
def get_filtered_depots(request, district_id):
    print("District ID: ", district_id)
    depots = Depots.objects.filter(district_id=district_id).all()
    print("Depots: ", depots)

    return JsonResponse(list(depots.values('id', 'depot')), safe=False)


@login_required
# @allowed_roles(['administrator'], ['users'])
def get_user_all_groups(request):
    if request.method == "GET":
        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)

        user_id = request.GET['i']
        user = UserProfile.objects.filter(id=user_id).first()

        user = UserProfile.objects.filter(id=user_id).first()
        all_groups = Group.objects.all()

        group_names = []
        if user:
            groups = user.groups.all()
            group_names = [group.name for group in groups]

            roles = {
                "engineering": [],
                "finance": [],
                "commercial": [],
                "ops": [],
                "it": [],
                "user_id": user_id
            }

            for group_name in group_names:

                if group_name and group_name.startswith("engineering"):
                    # Do something if the string starts with "engineering"
                    if group_name and group_name.startswith("engineering"):
                        # Do something if the string starts with "engineering"
                        roles["engineering"].append(group_name)

                if group_name and group_name.startswith("finance"):
                    # Do something if the string starts with "finance"
                    if group_name and group_name.startswith("finance"):
                        # Do something if the string starts with "finance"
                        roles["finance"].append(group_name)

                if group_name and group_name.startswith("commercial"):
                    # Do something if the string starts with "commercial"
                    if group_name and group_name.startswith("commercial"):
                        # Do something if the string starts with "commercial"
                        roles["commercial"].append(group_name)

                if group_name and group_name.startswith("ops"):
                    # Do something if the string starts with "ops"
                    if group_name and group_name.startswith("ops"):
                        # Do something if the string starts with "ops"
                        roles["ops"].append(group_name)

                if group_name and group_name.startswith("it"):
                    # Do something if the string starts with "it"
                    if group_name and group_name.startswith("it"):
                        # Do something if the string starts with "it"
                        roles["it"].append(group_name)

        print(roles)
        return render(
            request,
            "users/user_groups.html",
            {
                "user_title": user_title,
                "user_groups": user_groups,
                "roles": roles,
            }
        )


@login_required
# @allowed_roles(['Administrator'], ['users'])
def import_users(request):
    if request.method == "POST":
        file = request.FILES['file']
        if file:
            file_name = file.name
            if file_name.endswith('.csv'):
                decoded_file = file.read().decode('cp1252').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    # print("Row: ", row)
                    # (username, Designation, centre, descr, surname, firstname, initials, status, section, email, phone,
                    #  extension, section_code, createdon, region) = row
                    username = row['username'].replace(" ", "")
                    Designation = row['Designation'].replace(" ", "")
                    # centre = row['centre'].replace(" ", "")
                    # descr = row['descr'].replace(" ", "")
                    surname = row['surname'].replace(" ", "")
                    firstname = row['firstname'].replace(" ", "")
                    # initials = row['initials'].replace(" ", "")
                    # status = row['status'].replace(" ", "")
                    section = row['section'].replace(" ", "")
                    section1 = section
                    email = row['email'].replace(" ", "")
                    # phone = row['phone'].replace(" ", "")
                    # extension = row['extension'].replace(" ", "")
                    # section_code = row['section_code'].replace(" ", "")
                    # createdon = row['createdon'].replace(" ", "")
                    region = row['region']

                    # search designation by description if not found create a new one
                    designation = Designations.objects.filter(description=Designation).first()
                    if not designation:
                        designation = Designations(
                            identifier=Designation,
                            description=Designation,
                            chk=Designation
                        )
                        designation.save()
                        print("Created new designation")
                    # search region by name if not found create a new one
                    if region != "":
                        Region = Regions.objects.filter(region=region).first()
                        if not Region:
                            Region = Regions(
                                region=region,
                                code=region
                            )
                            Region.save()
                            print("Created new region")

                    if section != "":
                        section = "Western " + section

                        section, created = Sections.objects.get_or_create(
                            section=section,
                            region_id=5,
                            defaults={
                                'code': section1,
                            }

                        )

                        if created:
                            print("section created successfully!")
                        else:
                            print("section already exists!")
                    # check if user exists if not create a new one
                    username = "ze" + username
                    
                    # return JsonResponse({"status": "success", "message": "Users imported successfully"})
                    check_user = UserProfile.objects.filter(username=username).first()
                    if check_user:
                        print("User already exists")
                    else:
                        userprof = UserProfile(
                            username=username,
                            first_name=firstname,
                            last_name=surname,
                            designation=designation,
                            section=section,
                            region=Region if region != "" else None,
                            email=email,
                            password=make_password("password"),
                            # date_joined=createdon,
                            status="active"
                        )
                        # user.set_password("password")
                        userprof.save()
                        # user.save()
                        print("Users created")

                        # Get actual Role objects:
                        role_objects = Roles.objects.filter(name=Designation)

                    # scheduled_date = str(scheduled_date).split(" ")[0]
                return redirect('/users/users-index')
            elif file_name.endswith('.xls'):
                return render(request, 'users/import_users.html')

            elif file_name.endswith('.xlsx'):
                return render(request, 'users/import_users.html')
            else:
                print("Invalid file format")
                return render(request, 'users/import_users.html')
        else:
            print("No file uploaded")
            return render(request, 'users/import_users.html')
    else:
        return render(request, 'users/import_users.html')


@allowed_roles(['administrator'], ['users'])
def import_old_users(request):
    try:
        users_csv = 'execsys.csv'
        sections_csv = 'sections.csv'
        designations_csv = 'desig.csv'

        users_csv = pd.read_csv(users_csv)
        sections_csv = pd.read_csv(sections_csv)
        designations_csv = pd.read_csv(designations_csv)

        region = Regions.objects.filter(region='EASTERN REGION').first()
        # for _, row in designations_csv.iterrows():
        #     design = Designations.objects.filter(description=row['description'], region=region).first()
        #     if not design:
        #         designation = Designations(
        #             description=row['description'],
        #             chk=row['chk'],
        #             region=region
        #         )
        #         designation.save()

        # for _, row in sections_csv.iterrows():
        #     section = Sections.objects.filter(section=row['description'], region_id='2').first()
        #     if not section:
        #         section = Sections(
        #             section='Eastern ' + row['description'],
        #             code=row['section_code'],
        #             region_id='2'
        #         )
        #         section.save()

        for _, row in users_csv.iterrows():
            section = Sections.objects.filter(code=row['section'], region_id='2').first()
            cost_center = None
            if section:
                cost_center = CostCenter.objects.filter(code=section.section).first()
            designation = Designations.objects.filter(description=row['Designation']).first()
            region = Regions.objects.filter(region='EASTERN REGION').first()
            user_ = UserProfile.objects.filter(username=row['username']).first()
            if not user_:
                user = UserProfile(
                    username=row['username'],
                    first_name=row['firstname'],
                    last_name=row['surname'],
                    email=row['email'],
                    designation=designation,
                    section=section,
                    cost_center=cost_center,
                    status=row['status'],
                    region=region
                )
                user.set_password("Business@2024")
                user.save()
    except Exception as ex:
        print("Error: ", ex)

    return JsonResponse({"status": "success", "message": "Users imported successfully"})


def get_center_filter(request, id):
    cost_center = CostCenter.objects.filter(id=id).first()
    user = UserProfile.objects.get(id=request.GET['u'])
    cost_centers = cost_center.get_view()
    """set the cost center to the user"""
    user.cost_center = cost_center
    user.save()
    json_centers = []
    for cost_center in cost_centers:
        json_center = {
            "id": cost_center.id,
            "name": cost_center.name,
            "parent": cost_center.parent.id,
            "code": cost_center.code
        }

        json_centers.append(json_center)
    return JsonResponse(json_centers, safe=False)


def remove_duplicates():
    duplicates = (
        Roles.objects.values('role', 'app_id')
        .annotate(count_id=models.Count('id'))
        .filter(count_id__gt=1)
    )

    for duplicate in duplicates:
        roles = Roles.objects.filter(role=duplicate['role'], app_id=duplicate['app_id'])
        roles.exclude(id=roles.first().id).delete()


@login_required
def roles_modal(request):
    if request.method == "POST":
        user = UserProfile.objects.get(id=request.POST['user_id'])
        role = Roles.objects.none()
        try:
            role = Roles.objects.get(id=request.POST['role'])
        except:
            pass
        app_id = request.POST['selectedapp_id']
        user.add_role(role, app_id)
        responsibility = user.responsibilities.filter(user__id=user.id, role__app_id=app_id).first()
        responsibilityForm = ResponsibilitiesForm(request.POST, instance=responsibility)
        if responsibilityForm.is_valid():
            print("Saving responsibility")
            res = responsibilityForm.save()
            res.user = user
            res.save()
            for role in user.roles.filter(app_id=app_id):
                user.roles.remove(role)
            if res.role:
                user.roles.add(Roles.objects.get(id=res.role.id))
                print("Role added")
            if res.role and res.role.name:
                return JsonResponse({"status": "success", "appid": res.role.app_id.id, "role": res.role.name},
                                    safe=False)
            else:
                return JsonResponse({"status": "success", "appid": app_id, "role": None}, safe=False)
        else:
            print("Error: ", responsibilityForm.errors)
            user = UserProfile.objects.get(id=userid)
            regioncc = user.cost_center.get_region().get_decendance()
            regioncc_list = list(regioncc.values('id', 'code', 'name', 'parent'))
            return JsonResponse({"form": responsibilityForm.as_p(), "regioncc": regioncc_list,
                                 "app": Application.objects.get(id=appid).fullname}, safe=False)

    remove_duplicates()
    userid = request.GET['user_id']
    appid = request.GET['app_id']
    user = UserProfile.objects.get(id=userid)
    roles = Roles.objects.filter(app_id=appid)
    """use a model form to assign roles to the user"""
    regioncc = user.cost_center.get_region().get_decendance()
    responsibility = user.responsibilities.filter(role__app_id=appid).first()
    form = ResponsibilitiesForm(roles_queryset=roles, cost_centers_queryset=regioncc, instance=responsibility)
    regioncc_list = list(regioncc.values('id', 'code', 'name', 'parent'))
    return JsonResponse({"form": form.as_p(), "regioncc": regioncc_list,
                         "app": {'fullname': Application.objects.get(id=appid).fullname,
                                 'id': Application.objects.get(id=appid).id}}, safe=False)
