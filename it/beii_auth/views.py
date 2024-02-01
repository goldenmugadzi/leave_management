from django.shortcuts import render, redirect
from django.contrib.auth import logout

# from utils.helper_functions import get_dashboard_reports

from django.apps import apps
Sections = apps.get_model(app_label='users', model_name='Sections')
Districts = apps.get_model(app_label='users', model_name='Districts')
Depots = apps.get_model(app_label='users', model_name='Depots')
Regions = apps.get_model(app_label='users', model_name='Regions')
Roles = apps.get_model(app_label='users', model_name='Roles')
Designations = apps.get_model(app_label='users', model_name='Designations')
UserProfile = apps.get_model(app_label='users', model_name='UserProfile')

# Create your views here.
def index(request):
    
    if request.user.is_authenticated:
        
        user_title = request.user.get_full_name()
        l = request.user.groups.values_list('name',flat = True) # QuerySet Object
        user_groups = list(l)
        
        return redirect(
            '/dashboards/overview', 
            user_title, 
            request, 
            user_groups
            )
        
    return redirect('/accounts/login')

def dashboard(request):

    user_page = 'dashboard.html'
    user_title = request.user.get_full_name()
    user = request.user
    user_profile = UserProfile.objects.filter(user_id=user.id).first()
    l = request.user.groups.values_list('name',flat = True) # QuerySet Object
    user_groups = list(l) 
    
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
    section = Sections.objects.filter(code=user_profile.section).first()

    custom_user = {
        "id": user.pk,
        "username": user.username,
        "firstname": user.first_name,
        "lastname": user.last_name,
        "designation": user_profile.designation,
        "email": user.email,
        "section": section,
        "depot": depot,
        "district": district,
        "region": region,
        "roles": custom_user_roles,
    }
    
    dashboard_reports = get_dashboard_reports(user_profile.section)

    return render(
        request, 
        user_page, 
        {
            "user_title": user_title, 
            "user_groups": user_groups,
            "user": custom_user
        })

def home(request):

    user_page = 'home/dashboard.html'
    user_title = request.user.get_full_name()
    user = request.user
    user_profile = UserProfile.objects.filter(user_id=user.id).first()
    l = request.user.groups.values_list('name',flat = True) # QuerySet Object
    user_groups = list(l) 
    
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
    section = Sections.objects.filter(code=user_profile.section).first()

    custom_user = {
        "id": user.pk,
        "username": user.username,
        "firstname": user.first_name,
        "lastname": user.last_name,
        "designation": user_profile.designation,
        "email": user.email,
        "section": section,
        "depot": depot,
        "district": district,
        "region": region,
        "roles": custom_user_roles,
    }
    
    print("custom_user: ", custom_user)

    return render(
        request, 
        user_page, 
        {
            "user_title": user_title, 
            "user_groups": user_groups,
            "user": custom_user
        })
    
def business_applications(request):

    user_page = 'business_applications.html'
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name',flat = True) # QuerySet Object
    user_groups = list(l)  

    return render(
        request, 
        user_page, 
        {
            "user_title": user_title, 
            "user_groups": user_groups
        })

def app_logout(request):

    logout(request)
    return redirect('/accounts/login')

def get_dashboard_reports(section_code):
    
    report = {}
    
    
    return report
