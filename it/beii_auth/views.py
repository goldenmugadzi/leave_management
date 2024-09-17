from datetime import datetime, timedelta
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from decouple import config

from django.contrib.auth.decorators import login_required
from it.beii_auth.models import Question, SecurityQuestions
# from utils.helper_functions import get_dashboard_reports

from it.beii_auth.models import Question, SecurityQuestions
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
        "url": "/ace/aces_awaiting_my_action"
    },
    {
        "name": "ace reports",
        "title": "ACE Reports",
        "iconUrl": "assets/images/reports.png",
        "url": "/ace/create_ace_report"
    },
    {
        "name": "virament",
        "title": "Virement",
        "iconUrl": "assets/images/money.png",
        "url": "/ace/viraments_awaiting_my_action"
    },
    {
        "name": "Token",
        "title": "Tokens",
        "iconUrl": "assets/images/token.png",
        "url": "/tokens_awaiting_my_action/"
    },
    {
        "name": "petty_cash",
        "title": "Petty Cash",
        "iconUrl": "assets/images/pettycash.png",
        "url": "/pettycash/pettycashs_awaiting_my_action"
    },
    {
        "name": "petty_cash_reports",
        "title": "Petty Cash Reports",
        "iconUrl": "assets/images/pettyreports.png",
        "url": "/pettycash/create_pettycash_report"
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
        "url": "/restricted_bidding/comperative_schedules"
    },
    {
        "name": "direct_purchases",
        "title": "Direct Purchases",
        "iconUrl": "assets/images/bid.png",
        "url": "/direct_purchase/comperative_schedules"
    },
    {
        "name": "change_requests",
        "title": "Change Requests",
        "iconUrl": "assets/images/change.png",
        "url": "/change_requests/change_request_index"
    }
]

# Create your views here.
# @TODO: @login_required
def login_user(request):
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # print("user expiry: ", (user.password_expiry_date <= datetime.now().date()), user.password_expiry_date, datetime.now().date())
            if user.password_expiry_date and user.password_expiry_date <= datetime.now().date():
                login(request, user)
                return redirect('/auth/change-password')
            if user.change_password:
                login(request, user)
                return redirect('/auth/change-password')
            print("user ...")
            login(request, user)
            next_url = request.GET.get('next')
            print("next url: ", next_url)
            if next_url:
                return redirect(next_url)
            last_page = request.session.get('logout_page')
            print("last_page: ", last_page)
            if last_page:
                return redirect(last_page)
            return redirect('/dashboards/overview')
        else:
            return render(request, 'registration/login.html', {
                "error_msg": "Invalid username or password"
            })
    return render(request, 'registration/login.html', {})

@login_required(login_url='/accounts/login')
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

@login_required(login_url='/accounts/login')
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

@login_required(login_url='/accounts/login')
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
 
@login_required(login_url='/accounts/login')   
def business_applications(request):

    user_page = 'business_applications.html'
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name',flat = True) # QuerySet Object
    user_groups = list(l)  

    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    roles_ = user_profile.roles.all()

    users_role = user_profile.get_user_roles_for_application("users")

    print("users_role: ", users_role)
    applications = APPLICATIONS
    if users_role == "standard" or users_role == "" or users_role == None:
        print("creating standard list ..")
        applications = [app for app in applications if app['name'] != 'users']
    
    user = request.user
    if config('HOST') == "172.16.8.20":
        applications = applications
    else:
        if user.region:
            if user.region.region == "HARARE REGION" or user.region.region == "EASTERN REGION" or user.region.region == "NORTHERN REGION":
                applications = applications
            else:
                applications = [app for app in applications if app['name'] == 'users' or app['name'] == 'non_conformity']
        else:
            messages.error(request, "Your region is missing on your account profile, Please contact the administrator")
            applications = []
        
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

@login_required(login_url='/accounts/login')
def change_password(request):
    if request.method == "POST":
        print("request.POST: ", request.POST)
        
        username = request.user.username
        user_profile = UserProfile.objects.filter(username=username).first()
        questions = Question.objects.all()
        print("questions: ", questions)
        questions_json = json.dumps([{"id": q.id, "question": q.question} for q in questions])
        print("questions_json: ", questions_json)
        if user_profile:
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            if password != password_confirm:
                messages.error(request, "Passwords do not match")
                return render(request, "registration/change_password.html", {
                    "questions": questions_json,
                    "username": username
                })
            question1 = request.POST.get('security_question1')
            question2 = request.POST.get('security_question2')
            question3 = request.POST.get('security_question3')
            answer1 = request.POST.get('security_answer1')
            answer2 = request.POST.get('security_answer2')
            answer3 = request.POST.get('security_answer3')
            print('question1: ', question1)
            
            question1_ = Question.objects.filter(id=question1).first()
            question2_ = Question.objects.filter(id=question2).first()
            question3_ = Question.objects.filter(id=question3).first()
            print('question1_: ', question1_, question2_, question3_)
            
            user_security_questions = SecurityQuestions.objects.filter(user=user_profile)
            if user_security_questions:
                user_security_questions.delete()
            
            try:
                security_question1 = SecurityQuestions(
                    user=user_profile,
                    security_question=question1_,
                    security_answer=make_password(answer1)
                )
                security_question1.save()
                
                security_question2 = SecurityQuestions(
                    user=user_profile,
                    security_question=question2_,
                    security_answer=make_password(answer2)
                )
                security_question2.save()
                
                security_question3 = SecurityQuestions(
                    user=user_profile,
                    security_question=question3_,
                    security_answer=make_password(answer3)
                )
                security_question3.save()
            except Exception as e:
                print("Error: ", e)
                messages.error(request, "An error occurred. Please try again.")
                return render(request, "registration/change_password.html", {
                    "questions": questions_json,
                    "username": username
                })
            
            try:
                validate_password(password, user=user_profile)
                user_profile.set_password(password)
                user_profile.change_password = False
                user_profile.password_expiry_date = datetime.now().date() + timedelta(days=30)
                user_profile.save()
                messages.success(request, "Password changed successfully")
                return redirect('/accounts/login')
                # Password is valid
            except ValidationError as e:
                # Password is not valid
                print(e.messages)
                messages.error(request, e.messages)
                return render(request, "registration/change_password.html", {
                    "questions": questions_json,
                    "username": username
                })
        else:
            messages.error(request, "User not found")
            return redirect('/accounts/login')
    else:
        if not request.user:
            return redirect('/accounts/login')
        print("user : ", request.user.username)
        username = request.user.username
        questions = Question.objects.all()
        print("questions: ", questions)
        questions_json = json.dumps([{"id": q.id, "question": q.question} for q in questions])
        print("questions_json: ", questions_json)
        return render(request, "registration/change_password.html", {
            "questions": questions_json,
            "username": username
        })
            
# @login_required(login_url='/accounts/login')
def security_questions(request):
   if request.method == "POST":

       username = request.POST.get('username')
       user_profile = UserProfile.objects.filter(username=username).first()
       if user_profile:
            question = request.POST.get('security_question1')
            answer = request.POST.get('security_answer1')
            print('question1: ', question, answer)
            
            question1_ = Question.objects.filter(id=question).first()
            
            user_security_question = SecurityQuestions.objects.filter(user=user_profile, security_question=question1_).first()
            if user_security_question:
                # compare the answer
                print("user_security_question: ", user_security_question)
                if check_password(answer, user_security_question.security_answer):
                    print("Answer matched")
                    user_profile.change_password = True
                    user_profile.save()
                    messages.success(request, "Security questions answered successfully")
                    return render(request, "registration/reset_password.html", {
                        "username": username,
                    })
                else:
                    print("Invalid answer")
                    messages.error(request, "Invalid answer")
                    return redirect('/auth/answer-security-questions') 
            else:
                print("User has not set this security questions")
                messages.error(request, "User has not set this security questions")
                return redirect('/auth/answer-security-questions')
       messages.error(request, "User not found")
       return redirect('/auth/answer-security-questions')
   else:
       questions = Question.objects.all()
       print("questions: ", questions)
       questions_json = json.dumps([{"id": q.id, "question": q.question} for q in questions])
       print("questions_json: ", questions_json)
       return render(request, "registration/answer_questions.html", {
           "questions": questions_json
       }) 

# @login_required(login_url='/accounts/login')   
def reset_email(request):
    if request.method == "POST":
         
         return redirect('/accounts/login')
    else:
         return render(request, "registration/change_password_email.html", {})

# @login_required(login_url='/accounts/login')    
def reset_password(request):
    if request.method == "POST":
         
        username = request.POST.get('username')
        user_profile = UserProfile.objects.filter(username=username).first()
        
        if user_profile:
            password = request.POST.get('new_password')
            password_confirm = request.POST.get('password_confirm')
            print("password: ", password, password_confirm)
            if password != password_confirm:
                print("Passwords do not match")
                messages.error(request, "Passwords do not match")
                return redirect('/auth/reset-password', {
                    "username": username,
                })
            print("password matched")
            try:
                validate_password(password, user=user_profile)
                user_profile.set_password(password)
                user_profile.change_password = False
                user_profile.password_expiry_date = datetime.now().date() + timedelta(days=-1)
                user_profile.save()
                messages.success(request, "Password changed successfully")
                return redirect('/accounts/login')
                # Password is valid
            except ValidationError as e:
                # Password is not valid
                print(e.messages)
                messages.error(request, e.messages)
                return redirect('/accounts/login')
        else:
            print("User not found")
            return redirect('/auth/reset-password')
    else:
         return render(request, "registration/reset_password.html", {})

def get_dashboard_reports(section_code):
    
    report = {}
    
    
    return report
