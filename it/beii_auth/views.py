from datetime import datetime, timedelta
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from decouple import config
from django.utils import timezone
from ipware import get_client_ip
from django.http import HttpResponseRedirect, JsonResponse

from django.contrib.auth.decorators import login_required
from it.beii_auth.models import Question, SecurityQuestionAttempt, SecurityQuestions, LoginAttempt, PasswordResetAttempt, PasswordResetToken, PasswordHistory, SecurityVerificationToken
from it.beii_auth.models import check_password_history
# from utils.helper_functions import get_dashboard_reports

from it.beii_auth.models import Question, SecurityQuestions
from it.users.models import UserProfile, Depots, Districts, Regions, Designations, Sections, Roles
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from it.users.views import ms_exhange_reset_password_html, ms_exhange_send_html

# Configure security logger
logger = logging.getLogger('security')
if not logger.handlers:
    # Set up handler if not already configured
    handler = logging.FileHandler('security.log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
    },
    {
        "name": "appraisal",
        "title": "Appraisal",
        "iconUrl": "assets/images/performance-appraisal-employee.png",
        "url": "/appraisal"
    },
    {
        "name": "hardware_faults",
        "title": "IT Hardware Management",
        "iconUrl": "assets/images/hardware.png",
        "url": "/show_fault/"
    },
     {
        "name": "asset_register",
        "title": "IT Asset Register",
        "iconUrl": "assets/images/register.png",
        "url": "/tab/"
    },
    #   {
    #     "name": "leave_management",
    #     "title": "Leave Management System",
    #     "iconUrl": "assets/images/leave.png",
    #     "url": "/leave_dashboard/"
    # },
    #   {
    #     "name": "Safety",
    #     "title": "Safety",
    #     "iconUrl": "assets/images/leave.png",
    #     "url": "/accident_report_dashboard/"
    # }, 
      
      
]

REPORTS = [
    {
        "name": "ace reports",
        "title": "ACE Reports",
        "iconUrl": "assets/images/reports.png",
        "url": "/ace/reports"
    },
    {
        "name": "petty_cash_reports",
        "title": "Petty Cash Reports",
        "iconUrl": "assets/images/pettyreports.png",
        "url": "/pettycash/create_pettycash_report"
    },
    {
        "name": "petty_cash_monthly_totals",
        "title": "Petty Cash Monthly Totals",
        "iconUrl": "assets/images/pettyreports.png",
        "url": "/pettycash/monthly_totals"
    },
    {
        "name": "comperative_schedule",
        "title": "RFQ",
        "iconUrl": "assets/images/ristricted_bid.png",
        "url": "/comperative_schedule/reports"
    },
    {
        "name": "direct_purchases",
        "title": "Direct Purchases",
        "iconUrl": "assets/images/bid.png",
        "url": "/direct_purchase/reports"
    },
    {
        "name": "change_requests",
        "title": "Change Requests",
        "iconUrl": "assets/images/change.png",
        "url": "/change_requests/change_request_reports"
    },
    #   {
    #     "name": "asset reports",
    #     "title": "Asset Reports",
    #     "iconUrl": "assets/images/reports.png",
    #     "url": "/asset_report/"
    # }, 
      {
        "name": "Token",
        "title": "Tokens",
        "iconUrl": "assets/images/token.png",
        "url": "/tokens_reports/"
    },{
        "name": "non_conformity",
        "title": "Non-Conformity",
        "iconUrl": "assets/images/non-conforming.png",
        "url": "/nonconformity_repots/"
    },
    # {
    #     "name": "sanction_for_test_reports",
    #     "title": "Sanction For Test Reports",
    #     "iconUrl": "assets/images/sanction_for_test.png",
    #     "url": "/sanction_for_test/reports/"
    # }
]


# Create your views here.
# @TODO: @login_required
def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Get IP address for tracking
        client_ip, is_routable = get_client_ip(request)
        if client_ip is None:
            client_ip = '0.0.0.0'
            
        # Log attempt
        logger.info(f"Login attempt for user: {username} from IP: {client_ip}")
            


        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # # Record successful login
                # LoginAttempt.objects.create(
                #     username=username,
                #     ip_address=client_ip,
                #     user_agent=request.META.get('HTTP_USER_AGENT', ''),
                #     successful=True
                # )
                
                # Log successful login
                logger.info(f"Successful login for user: {username} from IP: {client_ip}")
                
                # Continue with normal login process
                if user.password_expiry_date and user.password_expiry_date <= datetime.now().date():
                    logger.info(f"Password expired for user: {username}, redirecting to change password")
                    login(request, user)
                    return redirect('/auth/change-password')
                if user.change_password:
                    logger.info(f"Change password required for user: {username}")
                    login(request, user)
                    return redirect('/auth/change-password')
                
                login(request, user)
                next_url = request.GET.get('next')
                
                if next_url:
                    return redirect(next_url)
                last_page = request.session.get('logout_page')
                
                if last_page:
                    return redirect(last_page)
                return redirect('/dashboards/overview')
            else:
                # Record failed login attempt
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    successful=False
                )
                
                # Log failed login
                logger.warning(f"Failed login attempt for user: {username} from IP: {client_ip}")
                
                return render(request, 'registration/login.html', {
                    "error_msg": "Invalid username or password"
                })
        except Exception as e:
            # Record failed login attempt
            # LoginAttempt.objects.create(
            #     username=username,
            #     ip_address=client_ip,
            #     user_agent=request.META.get('HTTP_USER_AGENT', ''),
            #     successful=False
            # )
            
            # Log the exception
            logger.error(f"Login error for user: {username} from IP: {client_ip} - Error: {str(e)}")
            
            return render(request, 'registration/login.html', {
                "error_msg": "Invalid username or password"
            })

    return render(request, 'registration/login.html', {})



def index(request):
    if request.user.is_authenticated:
        # For authenticated users, redirect to dashboard
        return redirect('/dashboards/overview')
    else:
        # For unauthenticated users, show login page
        return redirect('/accounts/login')


@login_required(login_url='/accounts/login')
def dashboard(request):
    user_page = 'dashboard.html'
    user_title = request.user.get_full_name()
    user = request.user
    user_profile = UserProfile.objects.filter(user_id=user.id).first()
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
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
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
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
        user_designation = Designations.objects.filter(
            id=user_profile.designation).first() if user_profile.designation else None

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

    # print("custom_user: ", custom_user)

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
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)

    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    roles_ = user_profile.roles.all()

    users_role = user_profile.get_user_roles_for_application("users")

    # print("users_role: ", users_role)
    applications = APPLICATIONS
    if users_role == "standard" or users_role == "" or users_role == None:
        # print("creating standard list ..")
        applications = [app for app in applications if app['name'] != 'users']

    user = request.user
    if config('HOST') == "172.16.8.20":
        applications = applications
    else:
        if user.region:
            # Relaxed: show all report modules regardless of region (including T&D)
            applications = applications
                
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


@login_required(login_url='/accounts/login')
def application_reports(request):
    user_page = 'applications_reports.html'
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)  # QuerySet Object
    user_groups = list(l)

    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    roles_ = user_profile.roles.all()

    users_role = user_profile.get_user_roles_for_application("users")

    # print("users_role: ", users_role)
    applications = REPORTS
    if users_role == "standard" or users_role == "" or users_role == None:
        # print("creating standard list ..")
        applications = [app for app in applications if app['name'] != 'users']

    # Add users report module
    if 'users' not in [app['name'] for app in applications]:
        applications.insert(0, {
            "name": "users",
            "title": "User Reports",
            "iconUrl": "assets/images/management.png",
            "url": "/users/user-reports"
        })

    user = request.user
    if config('HOST') == "172.16.8.20":
        applications = applications
    else:
        if user.region:
            # Relaxed: show all report modules regardless of region (including T&D)
            applications = applications
                
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
            "page_title": "Application Reports",
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


def security_questions(request):
    if request.method == "POST":
        username = request.POST.get('username')
        client_ip, is_routable = get_client_ip(request)
        if client_ip is None:
            client_ip = '0.0.0.0'
            
        # Add better logging at the start of the function
        logger.info(f"Security question verification attempt for username: {username} from IP: {client_ip}")
        logger.info(f"POST data: {request.POST}")
        
        try:
            # Check for rate limiting - max 5 attempts per 30 minutes
            half_hour_ago = timezone.now() - timezone.timedelta(minutes=30)
            recent_attempts = SecurityQuestionAttempt.objects.filter(
                username=username,
                ip_address=client_ip,
                timestamp__gte=half_hour_ago
            ).count()
            
            if recent_attempts >= 5:
                logger.warning(f"Security question rate limit exceeded for username: {username} from IP: {client_ip}")
                messages.error(request, "Too many verification attempts. Please try again later or use email reset.")
                return redirect('/password-reset/')
            
            # Get the user profile
            user_profile = UserProfile.objects.filter(username=username).first()
            if not user_profile:
                # Don't reveal if username exists - record the attempt
                SecurityQuestionAttempt.objects.create(
                    username=username,
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    successful=False,
                    question_id=0
                )
                logger.warning(f"Security question attempt for non-existent username: {username} from IP: {client_ip}")
                messages.error(request, "Invalid information provided. Please try again or use email reset.")
                return redirect('/auth/answer-security-questions')
                
            # Process all submitted questions (supports multiple questions)
            # We'll require at least 2 correct answers
            question_1_id = request.POST.get('security_question1')
            answer_1 = request.POST.get('security_answer1')
            
            question_2_id = request.POST.get('security_question2', None)
            answer_2 = request.POST.get('security_answer2', None)
            
            question_3_id = request.POST.get('security_question3', None)
            answer_3 = request.POST.get('security_answer3', None)
            
            logger.info(f"Questions received: Q1: {question_1_id}, Q2: {question_2_id}, Q3: {question_3_id}")
            
            # Count correct answers
            correct_answers = 0
            total_questions = 0
            
            # Process Question 1
            if question_1_id:
                total_questions += 1
                question_1 = Question.objects.filter(id=question_1_id).first()
                if question_1:
                    logger.info(f"Found question 1: {question_1}")
                    user_security_question = SecurityQuestions.objects.filter(
                        user=user_profile,
                        security_question=question_1
                    ).first()
                    
                    if user_security_question:
                        if check_password(answer_1, user_security_question.security_answer):
                            logger.info(f"Question 1 answer correct")
                            correct_answers += 1
                        else:
                            logger.info(f"Question 1 answer incorrect")
                    else:
                        logger.warning(f"User has not set up question 1 (ID: {question_1_id})")
                else:
                    logger.warning(f"Question 1 (ID: {question_1_id}) not found in database")
            
            # Process Question 2
            if question_2_id:
                total_questions += 1
                question_2 = Question.objects.filter(id=question_2_id).first()
                if question_2:
                    logger.info(f"Found question 2: {question_2}")
                    user_security_question = SecurityQuestions.objects.filter(
                        user=user_profile,
                        security_question=question_2
                    ).first()
                    
                    if user_security_question:
                        if check_password(answer_2, user_security_question.security_answer):
                            logger.info(f"Question 2 answer correct")
                            correct_answers += 1
                        else:
                            logger.info(f"Question 2 answer incorrect")
                    else:
                        logger.warning(f"User has not set up question 2 (ID: {question_2_id})")
                else:
                    logger.warning(f"Question 2 (ID: {question_2_id}) not found in database")
            
            # Process Question 3
            if question_3_id:
                total_questions += 1
                question_3 = Question.objects.filter(id=question_3_id).first()
                if question_3:
                    logger.info(f"Found question 3: {question_3}")
                    user_security_question = SecurityQuestions.objects.filter(
                        user=user_profile,
                        security_question=question_3
                    ).first()
                    
                    if user_security_question:
                        if check_password(answer_3, user_security_question.security_answer):
                            logger.info(f"Question 3 answer correct")
                            correct_answers += 1
                        else:
                            logger.info(f"Question 3 answer incorrect")
                    else:
                        logger.warning(f"User has not set up question 3 (ID: {question_3_id})")
                else:
                    logger.warning(f"Question 3 (ID: {question_3_id}) not found in database")
            
            # Log summary of verification attempt
            logger.info(f"Security question verification summary: {correct_answers}/{total_questions} correct answers")
            
            # Record the attempt with the first question ID (for tracking)
            SecurityQuestionAttempt.objects.create(
                username=username,
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                successful=(correct_answers >= 2),  # Require at least 2 correct answers
                question_id=int(question_1_id) if question_1_id and question_1_id.isdigit() else 0
            )
            
            # Check if enough correct answers were provided (at least 2)
            if correct_answers >= 2:
                logger.info(f"Successful security question verification for user: {username} - {correct_answers}/{total_questions} correct answers")
                
                # Generate verification token
                verification_token = default_token_generator.make_token(user_profile)
                
                # Store the token with expiry
                SecurityVerificationToken.objects.create(
                    user=user_profile,
                    token=verification_token,
                    expiry=timezone.now() + timezone.timedelta(minutes=15)
                )
                
                # Get questions for the password change form
                questions = Question.objects.all()
                questions_json = json.dumps([{"id": q.id, "question": q.question} for q in questions])
                
                messages.success(request, "Security questions verified successfully")
                
                return render(request, "registration/change_password.html", {
                    "questions": questions_json,
                    "username": username,
                    "verification_token": verification_token
                })
            else:
                logger.warning(f"Failed security question verification for user: {username} - {correct_answers}/{total_questions} correct answers")
                messages.error(request, "Incorrect answers provided. Please try again or use email reset.")
                return redirect('/auth/answer-security-questions')
        except Exception as e:
            # Log any unexpected exceptions
            logger.error(f"Error in security questions verification: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred during verification. Please try again or use email reset.")
            return redirect('/auth/answer-security-questions')
    else:
        # GET request - show the form
        questions = Question.objects.all()
        questions_json = json.dumps([{"id": q.id, "question": q.question} for q in questions])
        
        return render(request, "registration/answer_questions.html", {
            "questions": questions_json,
            "security_questions": questions  # This provides the questions to the template
        })
        
# Add this function to reset password after security question verification
def reset_password_after_verification(request):
    if request.method == "POST":
        username = request.POST.get('username')
        verification_token = request.POST.get('verification_token')
        
        logger.info(f"Password reset after verification attempt for username: {username}")
        logger.info(f"POST data: {request.POST}")
        
        try:
            # Get user profile
            user_profile = UserProfile.objects.filter(username=username).first()
            if not user_profile:
                logger.warning(f"User not found for reset after verification: {username}")
                messages.error(request, "User not found")
                return redirect('/accounts/login')
                
            # Verify the token is valid
            token_record = SecurityVerificationToken.objects.filter(
                user=user_profile,
                token=verification_token,
                used=False,
                expiry__gt=timezone.now()
            ).first()
            
            if not token_record:
                logger.warning(f"Invalid or expired verification token for user: {username}")
                messages.error(request, "Verification expired or invalid. Please try again.")
                return redirect('/auth/answer-security-questions')
            
            # Now handle the password reset
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            if not password or not password_confirm:
                logger.warning(f"Missing password or confirmation for user: {username}")
                messages.error(request, "Please provide both password and confirmation")
                return render(request, "registration/change_password.html", {
                    "username": username,
                    "verification_token": verification_token
                })
            
            if password != password_confirm:
                logger.warning(f"Passwords do not match for user: {username}")
                messages.error(request, "Passwords do not match")
                return render(request, "registration/change_password.html", {
                    "username": username,
                    "verification_token": verification_token
                })
                
            try:
                # Check password history to prevent reuse
                if check_password_history(user_profile, password):
                    logger.warning(f"Password reuse detected for user: {username}")
                    messages.error(request, "Cannot reuse previous passwords")
                    return render(request, "registration/change_password.html", {
                        "username": username,
                        "verification_token": verification_token
                    })
                    
                # Validate password complexity
                validate_password(password, user=user_profile)
                
                # Store the previous password in history
                PasswordHistory.objects.create(
                    user=user_profile,
                    password_hash=user_profile.password
                )
                
                # Update the password
                user_profile.set_password(password)
                
                # Mark token as used
                token_record.used = True
                token_record.save()
                
                # Update password expiry date (90 days)
                user_profile.password_expiry_date = timezone.now().date() + timezone.timedelta(days=90)
                user_profile.change_password = False
                user_profile.save()
                
                # Log the successful password change
                logger.info(f"Password reset completed via security questions for user: {username}")
                
                messages.success(request, "Password changed successfully")
                return redirect('/accounts/login')
            except ValidationError as e:
                error_messages = '; '.join(e.messages) if isinstance(e.messages, list) else str(e)
                logger.warning(f"Password validation error for user {username}: {error_messages}")
                messages.error(request, error_messages)
                return render(request, "registration/change_password.html", {
                    "username": username,
                    "verification_token": verification_token,
                    "questions": json.dumps([]) # Empty questions as we don't need them for this page
                })
            except Exception as e:
                logger.error(f"Password reset error for user {username}: {str(e)}", exc_info=True)
                messages.error(request, "An error occurred. Please try again.")
                return render(request, "registration/change_password.html", {
                    "username": username,
                    "verification_token": verification_token,
                    "questions": json.dumps([]) # Empty questions as we don't need them for this page
                })
        except Exception as e:
            logger.error(f"Unexpected error in reset_password_after_verification: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred during password reset. Please try again.")
            return redirect('/auth/answer-security-questions')
    else:
        logger.warning("GET request to reset_password_after_verification, redirecting to security questions")
        return redirect('/auth/answer-security-questions')

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

def password_reset_request(request):
    """Handle password reset requests via email"""
    if request.method == "POST":
        # Add rate limiting for password reset attempts
        email = request.POST.get('email', '')
        client_ip, is_routable = get_client_ip(request)
        if client_ip is None:
            client_ip = '0.0.0.0'
        
        logger.info(f"Password reset request initiated for email: {email} from IP: {client_ip}")
        
        # Check for rate limiting - max 3 reset requests per hour
        hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_resets = PasswordResetAttempt.objects.filter(
            ip_address=client_ip,
            timestamp__gte=hour_ago
        ).count()
        
        if recent_resets >= 3:
            logger.warning(f"Password reset rate limit exceeded for IP: {client_ip}")
            messages.error(request, "Too many password reset attempts. Please try again later.")
            return redirect('/password-reset/')
        
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['email']
            # Check if email exists to reduce email enumeration risk
            associated_users = get_user_model().objects.filter(email=data)
            
            # Record the attempt regardless of whether user exists
            PasswordResetAttempt.objects.create(
                email=data,
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                successful=associated_users.exists()
            )
            
            if associated_users.exists():
                try:
                    user = associated_users.first()
                    subject = "Password Reset Request - ZETDC Business Excellence"
                    email_template_name = 'registration/email_template.html'
                    
                    # Generate one-time reset token
                    token = default_token_generator.make_token(user)
                    
                    # Invalidate any previous unused tokens
                    PasswordResetToken.objects.filter(
                        user=user,
                        used=False
                    ).update(used=True)
                    
                    # Log the token with expiry time for auditing
                    PasswordResetToken.objects.create(
                        user=user,
                        token=token,
                        expiry=timezone.now() + timezone.timedelta(hours=24)
                    )
                    
                    # Build the reset URL with domain from request
                    reset_url = f"{request.scheme}://{request.get_host()}/password-reset-confirm/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}/"
                    
                    # Context for email template
                    c = {
                        "email": user.email,
                        "user_name": f"{user.first_name} {user.last_name}",
                        "message": "You are receiving this email because you requested a password reset for your account.",
                        "type": "Password Reset Request",
                        "reset_url": reset_url,
                        "domain": request.get_host(),
                        "site_name": "ZETDC Business Excellence",
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": token,
                        "protocol": request.scheme,
                        "expiry_time": "24 hours",
                        "contact_email": "it@zetdc.co.zw",  # Add contact email for support
                    }
                    
                    # Render email content from template
                    email_content = render_to_string(email_template_name, c, request=request)
                    logger.info(f"Email template rendered successfully, length: {len(email_content)}")
                    
                    # Send email
                    try:
                        response = ms_exhange_reset_password_html(
                            subject=subject,
                            to_recipients=[user.email],
                            cc_recipients=[],
                            template=email_content,
                            kwargs={"kwargs": c}
                        )
                        
                        if isinstance(response, JsonResponse):
                            response_data = json.loads(response.content.decode('utf-8'))
                            if response_data.get("status") == "error":
                                raise Exception(response_data.get("message", "Unknown email error"))
                            else:
                                logger.info(f"Password reset email sent successfully to: {data}")
                        else:
                            logger.info(f"Password reset email sent successfully to: {data}")
                    except Exception as e:
                        logger.error(f"Failed to send password reset email to {data}: {str(e)}", exc_info=True)
                        messages.error(request, "Failed to send password reset email. Please try again later or contact support.")
                        return redirect('/password-reset/')
                        
                except Exception as e:
                    logger.error(f"Error processing password reset for {data}: {str(e)}", exc_info=True)
            
            # Always show the same message whether the email exists or not
            # This prevents user enumeration attacks
            messages.success(request, "If your email address exists in our database, you will receive a password recovery link at your email address in a few minutes.")
            return redirect('password_reset_done')
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'registration/password_reset_email.html', {'form': form})
    else:
        # For GET requests, just display the form
        form = PasswordResetForm()
        return render(request, 'registration/password_reset_email.html', {'form': form})

def password_reset_done_view(request):
    """Display confirmation page after password reset request"""
    return render(request, 'registration/email_reset_done.html', {
        'title': 'Password Reset Sent',
        'wait_time': '15 minutes',  # Indicate expected wait time
    })

def password_reset_confirm_view(request, uidb64, token):
    """Handle password reset confirmation from email link"""
    try:
        # Decode the user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
        client_ip, _ = get_client_ip(request)
        
        logger.info(f"Password reset confirmation attempt for user ID: {uid} from IP: {client_ip if client_ip else 'unknown'}")
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None
        logger.warning(f"Invalid password reset confirmation attempt with uidb64: {uidb64}")

    # Verify the token is still valid
    if user is not None:
        token_record = PasswordResetToken.objects.filter(
            user=user,
            token=token,
            used=False,
            expiry__gt=timezone.now()
        ).first()
        
        if not token_record:
            logger.warning(f"Invalid or expired token used for user: {user.username}")
            return render(request, 'registration/password_reset_confirm.html', {
                'invalid': True,
                'error_message': 'The password reset link has expired or already been used.',
                'title': 'Password Reset Failed',
                'support_email': 'it@zetdc.co.zw'  # Provide contact information for support
            })
            
        if request.method == "POST":
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Validate form data
            if not password or not password_confirm:
                messages.error(request, "Please fill in all required fields.")
                return render(request, 'registration/password_reset_confirm.html', {'form': SetPasswordForm(user)})
                
            if password != password_confirm:
                messages.error(request, "Passwords do not match")
                return render(request, 'registration/password_reset_confirm.html', {'form': SetPasswordForm(user)})
            
            try:
                # Check password history to prevent reuse
                if check_password_history(user, password):
                    messages.error(request, "Cannot reuse previous passwords. Please choose a different password.")
                    return render(request, 'registration/password_reset_confirm.html', {'form': SetPasswordForm(user)})
                    
                # Validate password complexity
                validate_password(password, user=user)
                
                # Store the previous password in history
                PasswordHistory.objects.create(
                    user=user,
                    password_hash=user.password
                )
                
                # Update the password
                user.set_password(password)
                
                # Mark token as used
                token_record.used = True
                token_record.save()
                
                # Update password expiry date (90 days)
                user.password_expiry_date = timezone.now().date() + timezone.timedelta(days=90)
                user.change_password = False
                user.save()
                
                # Log the successful password change
                logger.info(f"Password reset completed successfully for user: {user.username}")
                
                messages.success(request, "Your password has been changed successfully! You can now log in with your new password.")
                return redirect('password_reset_complete')
            except ValidationError as e:
                error_messages = '; '.join(e.messages) if isinstance(e.messages, list) else str(e)
                logger.warning(f"Password validation error for user {user.username}: {error_messages}")
                messages.error(request, error_messages)
                return render(request, 'registration/password_reset_confirm.html', {'form': SetPasswordForm(user)})
            except Exception as e:
                logger.error(f"Password reset error for user {user.username}: {str(e)}", exc_info=True)
                messages.error(request, "An error occurred. Please try again or contact support.")
                return render(request, 'registration/password_reset_confirm.html', {'form': SetPasswordForm(user)})
        else:
            # Display the password reset form for GET requests
            form = SetPasswordForm(user)
            return render(request, 'registration/password_reset_confirm.html', {
                'form': form,
                'title': 'Reset Your Password',
                'validlink': True
            })
    else:
        # Invalid user ID
        return render(request, 'registration/password_reset_confirm.html', {
            'invalid': True,
            'title': 'Password Reset Failed',
            'error_message': 'The password reset link is invalid or has expired.',
            'support_email': 'it@zetdc.co.zw'
        })

def password_reset_complete_view(request):
    """Display confirmation of successful password reset"""
    return render(request, 'registration/password_reset_complete.html', {
        'title': 'Password Reset Complete',
        'login_url': '/accounts/login/'
    })

def test_email(request):
    """Test view for sending a test email to diagnose email server issues"""
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)
        
    try:
        test_email = request.GET.get('email', 'it@zetdc.co.zw')
        logger.info(f"Attempting to send test email to: {test_email}")
        
        response = ms_exhange_reset_password_html(
            subject="Test Email - ZETDC Business Excellence",
            to_recipients=[test_email],
            cc_recipients=[],
            template="<html><body><h1>Test Email</h1><p>This is a test email from ZETDC Business Excellence system.</p><p>If you received this, the email system is working correctly.</p></body></html>",
            kwargs={"kwargs": {}}
        )
        
        if isinstance(response, JsonResponse):
            response_data = json.loads(response.content.decode('utf-8'))
            return HttpResponse(f"<h1>Email Test Result</h1><pre>{json.dumps(response_data, indent=2)}</pre>")
        else:
            return HttpResponse(f"<h1>Email Test Result</h1><p>Response: {response}</p>")
            
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}", exc_info=True)
        return HttpResponse(f"<h1>Email Test Failed</h1><p>Error: {str(e)}</p>")
