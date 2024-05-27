from django.shortcuts import render, redirect
from django.contrib.auth import logout

# from utils.helper_functions import get_dashboard_reports


from it.users.models import UserProfile, Depots, Districts, Regions, Designations, Sections, Roles

APPLICATIONS = [
    {
        "name": "users",
        "title": "Users",
        "iconUrl": "assets/images/management.png",
        "url": "/users/users-index"
    },
    {
        "name": "non_conformity",
        "title": "Non-Conformity",
        "iconUrl": "assets/images/non-conforming.png",
        "url": "/nonconformities/"
    },
    {
        "name": "ace",
        "title": "ACE",
        "iconUrl": "assets/images/capital.png",
        "url": "/acee/aces"
    },
    {
        "name": "Token",
        "title": "Tokens",
        "iconUrl": "assets/images/token.png",
        "url": "/tokens/"
    },
    {
        "name": "petty_cash",
        "title": "Petty Cash",
        "iconUrl": "assets/images/pettycash.png",
        "url": "/pettycash/pettycashs_awaiting_my_action"
    },
    {
        "name": "purchase_request",
        "title": "Purchase Request",
        "iconUrl": "assets/images/quotation.png",
        "url": "/purchase_requests"
    },
    {
        "name": "comperative_schedule",
        "title": "RFQ",
        "iconUrl": "assets/images/ristricted_bid.png",
        "url": "/comperative_schedule/comperative_schedules"
    },
    {
        "name": "ristricted_bidding",
        "title": "Restricted Biddings",
        "iconUrl": "assets/images/direct_bid.png",
        "url": "/ristricted_bidding/comperative_schedules"
    },
    {
        "name": "direct_purchases",
        "title": "Direct Purchases",
        "iconUrl": "assets/images/bid.png",
        "url": "/direct_purchase/comperative_schedules"
    }
]

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

    custom_user = {
        "id": user.pk,
        "username": user.username,
        "firstname": user.first_name,
        "lastname": user.last_name,
        "designation": user_designation,
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
    custom_user_roles = {
        "users": {},
    }
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "users":
            custom_user_roles["users"] = role
    users_role = str(custom_user_roles["users"])

    print("users_role: ", users_role)
    applications = APPLICATIONS
    if users_role == "standard":
        print("creating standard list ..")
        applications = [app for app in applications if app['name'] != 'users']
        
    url_path = request.path.split("/")
    return render(
        request, 
        user_page, 
        {
            "user_title": user_title,
            "url_path": url_path,
            "page_title": "Business Applications", 
            "user_groups": user_groups,
            "apps": applications
        })

def app_logout(request):

    logout(request)
    return redirect('/accounts/login')

def get_dashboard_reports(section_code):
    
    report = {}
    
    
    return report
