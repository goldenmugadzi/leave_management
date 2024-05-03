# users/views.py

import json
import csv
from django.contrib.auth import login
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.sites import requests
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from openpyxl.reader.excel import load_workbook
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser

from it.users.models import Application, Roles, UserProfile, Depots, Districts, Regions, Designations, Sections
from it.users.forms import CustomUserCreationForm
# from scr import csvfile

from utils.helper_functions import group_user_roles
from django.contrib.auth.models import Group
from .helpers import DESIGNATIONS, REGIONS, DISTRICTS, DEPOTS, ROLES, SECTIONS

BASE_URL = "http://172.16.8.98:9300"


def add_centers(request):
    
    # for region in REGIONS:
    #     _region = Regions(
    #         region=region['name'],
    #         code=region['code'],
    #     )
    #     _region.save()
    #
    # for district in DISTRICTS:
    #     region_id = Regions.objects.filter(code=district['parent_code']).first()
    #     _district = Districts(
    #         district=district['name'],
    #         code=district['code'],
    #         region_id=region_id.id
    #     )
    #     _district.save()
    #
    # for depot in DEPOTS:
    #     district_id=Districts.objects.filter(code=depot['district_code']).first()
    #     region_id = Regions.objects.filter(code=depot['parent_code']).first()
    #     _depot = Depots(
    #         depot=depot['name'],
    #         code=depot['code'],
    #         district_id=district_id.id,
    #         region_id=region_id.id
    #     )
    #     _depot.save()
    #
    # for designation in DESIGNATIONS:
    #     _designation = Designations(
    #         description=designation['description']
    #     )
    #     _designation.save()
    #
    # for role in ROLES:
    #     application_ = role['application']
    #     app_id = Application.objects.filter(name=application_).first()
    #     if app_id:
    #         _role = Roles(
    #             role=role['role'],
    #             name=role['name'],
    #             description=role['description'],
    #             application=role['application'],
    #             app_id=app_id
    #         )
    #         _role.save()
    #     else:
    #         new_app = Application(
    #             name=application_
    #         )
    #         new_app.save()
    #         _role = Roles(
    #             role=role['name'],
    #             name=role['name'],
    #             description=role['description'],
    #             application=role['application'],
    #             app_id=new_app
    #         )
    #         _role.save()
            
    # for section in SECTIONS:
    #     _section = Sections(
    #         section=section['section'],
    #         code=section['code']
    #     )
    #     _section.save()
        
    return redirect('/users/users-index')


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
        districts = Districts.objects.all()
        regions = Regions.objects.all()

        return render(
            request,
            "users/add_user.html",
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
            depots_ = request.POST['depot']
            district_ = request.POST['district']
            region_ = request.POST['region']
            password1 = request.POST['password1']
            password2 = request.POST['password2']
            
            region = Regions.objects.filter(id=region_).first()
            district = Districts.objects.filter(code=district_).first()
            depot = Depots.objects.filter(code=depots_).first()
            section = Sections.objects.filter(code=section_).first()
            designation = Designations.objects.filter(id=designation_).first()
            print("section: ", section)
            
            if password1 == password2:
                user = UserProfile(
                    username=username,
                    first_name=firstnames,
                    last_name=lastnames,
                    email=email,
                    designation=designation,
                    section=section,
                    depot=depot,
                    district=district,
                    region=region,
                    status="active"
                )

                user.save()

                # Get actual Role objects:
                user_applications = Application.objects.all()
                roles = [role for role in [request.POST.get(app.name) for app in user_applications if request.POST.get(app.name) != ""] if role and role != ""]  
                print("roles: ", roles)    
                role_objects = Roles.objects.filter(id__in=roles)  # Example of retrieving roles
                user.roles.add(*role_objects)
                user.set_password(password1)
                user.save()

        except Exception as ex:
            print("save user error", ex)

        return redirect("/users/users-index")


def get_user_records(request):
    records = UserProfile.objects.order_by('-date_joined').all()

    records_list = []
    for record in records:
        o = {
            "id": record.pk,
            "username": record.username,
            "firstname": record.first_name,
            "lastname": record.last_name,
            "email": record.email,
            "date_created": record.date_joined.date()
        }

        records_list.append(o)

    context = json.dumps(records_list, default=str)
    user_page = 'users/user_index.html'
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)

    return render(
        request,
        user_page,
        {
            "title": "All Records",
            "context": context,
            "user_title": user_title,
            "user_groups": user_groups

        })

def update_user(request):
    if request.method == "GET":
        user_profile = UserProfile.objects.get(id=request.GET['i'])
        active_roles = {role.app_id.name: role for role in user_profile.roles.all() if role.app_id}

        new_user = {
            "id": user_profile.pk,
            "username": user_profile.username,
            "firstname": user_profile.first_name,
            "lastname": user_profile.last_name,
            "email": user_profile.email,
            "section": Sections.objects.filter(id=user_profile.section.id).first() if user_profile.section else None,
            "depot": Depots.objects.filter(id=user_profile.depot.id).first() if user_profile.depot else None,
            "district": Districts.objects.filter(id=user_profile.district.id).first() if user_profile.district else None,
            "region": Regions.objects.filter(id=user_profile.region.id).first() if user_profile.region else None,
            "roles": active_roles,
            "designation": Designations.objects.filter(id=user_profile.designation.id).first() if user_profile.designation else None,
        }

        all_roles = {app.name: Roles.objects.filter(app_id=app.id).all() for app in Application.objects.all()}

        return render(
            request,
            "users/user_update.html",
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
    elif request.method == "POST":
        user_profile = UserProfile.objects.filter(id=request.POST['user_id']).first()
        user_data = {
            'first_name': request.POST['firstname'],
            'last_name': request.POST['lastname'],
            'username': request.POST['username'],
            'email': request.POST['email'],
            'region': Regions.objects.filter(id=request.POST['region']).first(),
            'district': Districts.objects.filter(id=request.POST['district']).first() if request.POST['district'] not in ["Select District", ""] else None,
            'depot': Depots.objects.filter(id=request.POST['depot']).first() if request.POST['depot'] not in ["Select Depot", ""] else None,
            'section': Sections.objects.filter(code=request.POST['section']).first(),
            'designation': Designations.objects.filter(id=request.POST['designation']).first() if request.POST['designation'] not in ["Select Designation", ""] else None
        }

        for field, value in user_data.items():
            if value:
                setattr(user_profile, field, value)

        user_profile.save()

        roles = [role for role in [request.POST.get(app.name) for app in Application.objects.all() if request.POST.get(app.name) != 'Select Role'] if role and role != ""]
        user_profile.roles.clear()
        user_profile.roles.add(*Roles.objects.filter(id__in=roles))

        return redirect("/users/users-index")
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
            print("depot",request.POST['depot'] or None)
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
            roles = [role for role in [request.POST.get(app.name) for app in user_applications if request.POST.get(app.name) != 'Select Role'] if role and role != ""]  
            print("roles: ", roles)
            
            role_objects = Roles.objects.filter(id__in=roles)  # Example of retrieving roles
            user_profile.roles.clear()
            user_profile.roles.add(*role_objects)

        # except Exception as ex:
        #     print("save user error", ex)

            return redirect("/users/users-index")


def reset_user_password(request):
    if request.method == "POST":

        id = request.POST['item']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            user_profile = UserProfile.objects.filter(id=id).first()
            user_profile.set_password(password1)
            user_profile.save()
            print("saving done ....")

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


def change_user_password(request):
    if request.method == "POST":

        user_id = request.user.id
        current_password = request.POST['current_password']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            user_profile = UserProfile.objects.filter(id=user_id).first()
            if user_profile.check_password(current_password):
                user_profile.set_password(password1)
                user_profile.save()
                print("Password changed successfully")
            else:
                print("Current password is incorrect. Password not changed.")

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


def delete_user(request):
    if request.method == "GET":
        id = request.GET['i']
        user_profile = UserProfile.objects.filter(id=id).first()
        user_profile.delete()

    return redirect('/users/users-index')


def get_filtered_districts(request, region_id):
    
    districts = Districts.objects.filter(region_id=region_id).all()

    return JsonResponse(list(districts.values('id', 'district')), safe=False)

def get_filtered_depots(request, district_id):
        
    depots = Depots.objects.filter(district_id=district_id).all()

    return JsonResponse(list(depots.values('id', 'depot')), safe=False)

# Manage groups
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
def import_users(request):
    if request.method == "POST":
        file = request.FILES['file']
        if file:
            file_name = file.name
            if file_name.endswith('.csv'):
                decoded_file = file.read().decode('cp1252').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    # (username, Designation, centre, descr, surname, firstname, initials, status, section, email, phone,
                    #  extension, section_code, createdon, region) = row
                    username = row['username'].replace(" ", "")
                    Designation = row['Designation'].replace(" ", "")
                    centre = row['centre'].replace(" ", "")
                    descr = row['descr'].replace(" ", "")
                    surname = row['surname'].replace(" ", "")
                    firstname = row['firstname'].replace(" ", "")
                    initials = row['initials'].replace(" ", "")
                    status = row['status'].replace(" ", "")
                    section = row['section'].replace(" ", "")
                    email = row['email'].replace(" ", "")
                    phone = row['phone'].replace(" ", "")
                    extension = row['extension'].replace(" ", "")
                    section_code = row['section_code'].replace(" ", "")
                    createdon = row['createdon'].replace(" ", "")
                    region = row['region'].replace(" ", "")

                    section = Sections.objects.filter(code=section).first()
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
                    if region!="":
                        Region = Regions.objects.filter(region=region).first()
                        if not Region:
                            Region = Regions(
                                region=region,
                                code=region
                            )
                            Region.save()
                            print("Created new region")
                    # check if user exists if not create a new one
                    check_user = UserProfile.objects.filter(username=username).first()
                    if check_user:
                        print("User already exists")
                    else:
                        userprof = UserProfile(
                            username=username,
                            first_name=firstname,
                            last_name=surname,
                            designation=designation,
                            section=section if section!="" else None,
                            region=Region if region!="" else None,
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


# @csrf_exempt
# @api_view(['POST'])
# @parser_classes([JSONParser])
# def create_user(request):
#     print(request.data)
#     serializer = UserSerializer(request.data)
#     area = serializer.create(serializer.data)
#     area.save()
#
#     return Response({
#         "status": "success",
#         "message": "Successfully created area",
#         "code": 201,
#         "data": serializer.data
#     })
