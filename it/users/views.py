# users/views.py

import json
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import UserProfile
from users.forms import CustomUserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from django.apps import apps
Sections = apps.get_model(app_label='users', model_name='Sections')
Districts = apps.get_model(app_label='users', model_name='Districts')
Depots = apps.get_model(app_label='users', model_name='Depots')
Regions = apps.get_model(app_label='users', model_name='Regions')
Roles = apps.get_model(app_label='users', model_name='Roles')
Designations = apps.get_model(app_label='users', model_name='Designations')

from utils.helper_functions import get_user_groups, group_user_roles

def add_user(request):
    if request.method == "GET":

        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)
        
        # get roles
        user_roles = Roles.objects.all()
        grouped_user_roles = group_user_roles(user_roles)
        
        # get designations
        user_designations = Designations.objects.all()

        return render(
            request,
            "users/add_user.html",
            {
                "form": CustomUserCreationForm,
                "user_roles": grouped_user_roles,
                "user_designations": user_designations,
                "user_title": user_title,
                "user_groups": user_groups,
            }
        )
    elif request.method == "POST":
        try:
            firstnames = request.POST['firstname']
            lastnames = request.POST['lastname']
            username = request.POST['username']
            designation = request.POST['designation']
            email = request.POST['email']
            section = request.POST['section']
            region = request.POST['region']
            password1 = request.POST['password1']
            password2 = request.POST['password2']
            
            remittance_role = request.POST['remittance_role']
            pettycash = request.POST['petty_cash_role']
            tenders = request.POST['tenders_role']
            adjudication = request.POST['direct_purchase_role']
            tokens = request.POST['tokens_role']
            ace = request.POST['ace_role']
            non_conformity = request.POST['non_conformity_role']
            users_role = request.POST['users_role']
            
            roles = []
            if remittance_role:
                roles.append(remittance_role)
            if pettycash:
                roles.append(pettycash)
            if tenders:
                roles.append(tenders)
            if tokens:
                roles.append(tokens)
            if ace:
                roles.append(ace)
            if non_conformity:
                roles.append(non_conformity)
            if users_role:
                roles.append(users_role)
            if adjudication:
                roles.append(adjudication)
            
            str_roles = ','.join(str(x) for x in roles)
            
            if password1 == password2:
                user = User.objects.create_user(
                    username,
                    email,
                    password1
                )

                profile = UserProfile(
                    None,
                    user.pk,
                    designation=designation,
                    section=section,
                    region=region,
                    roles=str_roles,
                    status="active")

                profile.save()

                user.first_name = firstnames
                user.last_name = lastnames

                user.save()
        except Exception as ex:
            print("save user error", ex)

        return redirect("/users/users-index")

def get_user_records(request):
    records = User.objects.order_by('-date_joined').all()

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

        id = request.GET['i']
        user = User.objects.filter(id=id).first()
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

        new_user = None
        region = None
        district = None
        depot = None
        section = None
        user_designation = None
        if user_profile:
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
            section = Sections.objects.filter(code=user_profile.section).first()
            user_designation = Designations.objects.filter(id=user_profile.designation).first() if user_profile.designation else None

        new_user = {
            "id": user.pk,
            "username": user.username,
            "firstname": user.first_name,
            "lastname": user.last_name,
            "email": user.email,
            "section": section,
            "depot": depot,
            "district": district,
            "region": region,
            "roles": custom_user_roles,
            "designation": user_designation,
        }
        
        # print("new_user: ", new_user)

        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)
        
        # get roles
        user_roles = Roles.objects.all()
        grouped_user_roles = group_user_roles(user_roles)
        
        # get designations
        user_designations = Designations.objects.all()

        return render(
            request,
            "users/user_update.html",
            {
                "form": CustomUserCreationForm,
                "user_roles": grouped_user_roles,
                "user_designations": user_designations,
                "user_title": user_title,
                "user_groups": user_groups,
                "user": new_user
            }
        )
    elif request.method == "POST":
        try:
            id = request.POST['user_id']
            firstnames = request.POST['firstname']
            lastnames = request.POST['lastname']
            username = request.POST['username']
            email = request.POST['email']
            section = request.POST['section']
            region = request.POST['region']
            designation = request.POST['designation']
            
            remittance_role = request.POST['remittance_role']
            pettycash = request.POST['petty_cash_role']
            tenders = request.POST['tenders_role']
            adjudication = request.POST['direct_purchase_role']
            tokens = request.POST['tokens_role']
            ace = request.POST['ace_role']
            non_conformity = request.POST['non_conformity_role']
            users_role = request.POST['users_role']

            user = User.objects.filter(id=id).first()
            if firstnames:
                user.first_name = firstnames
            if lastnames:
                user.last_name = lastnames
            if username:
                user.username = username
            if email:
                user.email = email

            user.save()
            
            user_profile = UserProfile.objects.filter(user_id=id).first()
            if user_profile:
                if region:
                    user_profile.region = region
                if section:
                    user_profile.section = section
                if designation:
                    user_profile.designation = designation
                    
                roles = []
                if remittance_role:
                    roles.append(remittance_role)
                if pettycash:
                    roles.append(pettycash)
                if tenders:
                    roles.append(tenders)
                if tokens:
                    roles.append(tokens)
                if ace:
                    roles.append(ace)
                if non_conformity:
                    roles.append(non_conformity)
                if users_role:
                    roles.append(users_role)
                if adjudication:
                    roles.append(adjudication)
                
                str_roles = ','.join(str(x) for x in roles)
                
                user_profile.roles = str_roles
                user_profile.save()
                
        except Exception as ex:
            print("save user error", ex)

        return redirect("/users/users-index")

def change_user_password(request):
    if request.method == "POST":

        id = request.POST['item']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            user = User.objects.filter(id=id).first()
            user.set_password(password1)
            user.save()
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

def delete_user(request):
    if request.method == "GET":
        id = request.GET['i']
        user = User.objects.filter(id=id).first()
        user.delete()

    return redirect('/users/users-index')

# Manage groups
def get_user_all_groups(request):
    
    if request.method == "GET":
        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
        user_groups = list(l)
        
        user_id = request.GET['i']
        user = User.objects.filter(id=user_id).first()
        
        user = User.objects.filter(id=user_id).first()
        from django.contrib.auth.models import Group
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

def add_user_to_group(request, user_id, group_name):
    user = User.objects.filter(id=user_id).first()
    if user:
        group = Group.objects.get(name=group_name)
        group.user_set.add(user)
    else:
        print("User not found")
        
def add_user_to_groups(request, user_id, group_names):
    user = User.objects.filter(id=user_id).first()
    if user:
        
        for group_name in group_names:
            group = Group.objects.get(name=group_name)
            group.user_set.add(user)
            
    else:
        print("User not found")

def remove_user_from_group(request, user_id, group_name):
    user = User.objects.filter(id=user_id).first()
    if user:
        group = Group.objects.get(name=group_name)
        group.user_set.remove(user)
    else:
        print("User not found")
        
def remove_user_from_groups(request, user_id, group_names):
    user = User.objects.filter(id=user_id).first()
    if user:
        
        for group_name in group_names:
            group = Group.objects.get(name=group_name)
            group.user_set.remove(user)
    else:
        print("User not found")





        




