import csv
from datetime import datetime
from django.template.loader import render_to_string
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from it.change_requests.models import CRApproval, ChangeRequest, NewProfile, ProfileChange, ProfileDeactivation
from it.users.forms import ResponsibilitiesForm
from it.users.models import Application, CostCenter, Depots, Designations, Districts, Regions, Responsibilities, Roles, Sections, UserProfile
from django.db.models import Q
from django.contrib import messages
import traceback
from django.core.paginator import Paginator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.contrib.auth.decorators import login_required

from it.users.views import ms_exhange_reset_password_html, ms_exhange_send_html
# Create your views here.

@login_required
def create_change_request(request):
    
    user_title = request.user.get_full_name()
    user = request.user
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
    parent = CostCenter.objects.filter(Q(code=user.region.code) | Q(code="CC"+user.region.code)).first()
    cost_centers = parent.get_decendance() #CostCenter.objects.filter(parent=parent.id).all() if parent else []
    users = UserProfile.objects.filter(region=user.region).all()
    
    return render(request, 'change_requests/create_change_request.html',
            {
                "user_roles": all_roles,
                "user_profiles": users,
                "user_applications": user_applications,
                "user_designations": user_designations,
                "cost_centers": cost_centers,
                "user_title": user_title,
                "user_groups": user_groups,
            })
    
@login_required
def create_new_profile(request):
    try:
        change_reason = request.POST.get('change_reason')
        change_description = request.POST.get('change_description')
        profile_username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        designation_ = request.POST.get('designation')
        cost_center = request.POST.get('cost_center')
        application = request.POST.get('for_application')
        roles_to_action = request.POST.get('roles_to_action')

        region = Regions.objects.filter(id=request.user.region.id).first() if request.user else None
        cost_center_ = CostCenter.objects.filter(id=cost_center).first() if cost_center else None
        designation = Designations.objects.filter(id=designation_).first() if designation_ else None

        user = NewProfile(
            username=profile_username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            designation=designation,
            cost_center= cost_center_,
            region=region,
            created_at=datetime.now(),
            roles_to_action=roles_to_action
        )

        user.save()

        cr_id = "CR-" + datetime.now().strftime("%Y%m%d%I%M%S")
        cr_cost_center = request.user.cost_center
        change_request = ChangeRequest(
            application=application,
            cr_id=cr_id,
            change_type="New Profile",
            new_profile=user,
            change_description=change_description,
            change_reason=change_reason,
            creator_designation=designation,
            created_by=request.user,
            region=region,
            cost_center=cr_cost_center,
            created_at=datetime.now()
        )
        change_request.save()
        messages.success(request, "Change request submitted successfully")
        try:
            # Get section head approver for this cost center
            application = Application.objects.filter(name="change_requests").first()
            section_head_role = Roles.objects.filter(role="section_head", app_id=application.id).first()
            approver_responsibilities = Responsibilities.objects.filter(
                role=section_head_role,
                cost_centers__in=[cr_cost_center]
            ).first()
            approver = approver_responsibilities.user if approver_responsibilities else None
            if not approver:
                messages.error(request, "No section head approver found for this cost center")
                return redirect("/change_requests/create_change_request")
            print("Sending email to: ", approver.email)

            email_template_name = 'registration/email.html'
            msg = "New profile request submitted successfully"
            type_ = "New Profile Request"
            app_base = "change_requests/new_profile_request?i="+change_request.cr_id
            c = {
                "email": approver.email if approver.email else "",
                "message": msg,
                "type": type_,
                "redirect_app_base": app_base,
                "id": change_request.cr_id,
                "domain": request.META['HTTP_HOST'],
                "site_name": "Zetdc Business Excellence",
                "protocol": 'https' if request.is_secure() else 'http',
            }
            email = render_to_string(email_template_name, c, request=request)
            ms_exhange_reset_password_html(subject=type_,to_recipients=[approver.email], cc_recipients=[],template=email,
                                            kwargs={"kwargs": c})
            if approver.section:
                messages.success(request, f"Section head approver {approver.first_name} {approver.last_name}, {approver.section.name} notified successfully")
            else:
                messages.success(request, f"Section head approver {approver.first_name} {approver.last_name} notified successfully")
        except Exception as ex:
            print("Error: ", str(ex))
            # messages.error(request, "An error occurred while sending the email: " + str(ex))
    except Exception as ex:
        print("error: ", ex)
        messages.error(request, "An error occurred while submitting the change request"+str(ex))
        
    return redirect("/change_requests/create_change_request")

@login_required
def profile_modification_request(request):

        change_reason = request.POST.get("change_reason")
        change_description = request.POST.get("change_description")
        profile_username = request.POST.get("user_profile")
        application = request.POST.get("for_application")
        roles_to_action = request.POST.get("roles_to_action")
        auth_user = request.user
        print("username: ", profile_username)
        user = UserProfile.objects.filter(username=profile_username).first()
        if user:
            region, cost_center = None, None
            try:
                region = auth_user.region
                cost_center = auth_user.cost_center
            except Exception as ex:
                print("error: ", ex)
                messages.error(request, "You does not have a region or cost center")
                return redirect("/change_requests/change_request_index")
            
            profile_mod = ProfileChange(
                user=user,
                change_date=datetime.now(),
                changed_by=user,
                roles_to_action=roles_to_action
            )
            profile_mod.save()
            
            cr_id = "CR-" + datetime.now().strftime("%Y%m%d%I%M%S")
            
            change_request = ChangeRequest(
                cr_id=cr_id,
                application=application,
                change_type="Profile Modification",
                profile_change=profile_mod,
                change_description=change_description,
                change_reason=change_reason,
                creator_designation=user.designation,
                created_by=request.user,
                region=region if region else None,
                cost_center= cost_center if cost_center else None,
                created_at=datetime.now()
            )
            change_request.save()
            
            messages.success(request, "Change request submitted successfully")
            
            try:
                # Get section head approver for this cost center
                application = Application.objects.filter(name="Change Requests").first()
                section_head_role = Roles.objects.filter(role="section_head", app_id=application.id).first()
                approver_responsibilities = Responsibilities.objects.filter(
                    role=section_head_role,
                cost_centers__in=[cost_center]
                ).first()
                approver = approver_responsibilities.user if approver_responsibilities else None
                if not approver:
                    messages.error(request, "No section head approver found for this cost center")
                    return redirect("/change_requests/create_change_request")
                print("Sending email to: ", approver.email)
                email_template_name = 'registration/email.html'
                msg = "Profile modification request submitted successfully"
                type_ = "Profile Modification Request"
                app_base = "change_requests/profile_modification_request?i="+change_request.cr_id
                c = {
                    "email": approver.email if approver.email else "",
                    "message": msg,
                    "type": type_,
                    "redirect_app_base": app_base,
                    "id": change_request.cr_id,
                    "domain": request.META['HTTP_HOST'],
                    "site_name": "Zetdc Business Excellence",
                    "protocol": 'https' if request.is_secure() else 'http',
                }
                email = render_to_string(email_template_name, c, request=request)
                ms_exhange_reset_password_html(subject=type_,to_recipients=[approver.email], cc_recipients=[],template=email,
                                                kwargs={"kwargs": c})
                
                if approver.section:
                    messages.success(request, f'Section head approver {approver.first_name} {approver.last_name}, {approver.section.name} notified successfully')
                else:
                    messages.success(request, f'Section head approver {approver.first_name} {approver.last_name} notified successfully')
                    
            except Exception as ex:
                print("Error: ", str(ex))
                # messages.error(request, "An error occurred while sending the email: " + str(ex))
        else:
            messages.error(request, "User not found")

    
        return redirect("/change_requests/change_request_index")

def remove_duplicates():
    duplicates = (
        Roles.objects.values('role', 'app_id')
        .annotate(count_id=Roles.Count('id'))
        .filter(count_id__gt=1)
    )

    for duplicate in duplicates:
        roles = Roles.objects.filter(role=duplicate['role'], app_id=duplicate['app_id'])
        roles.exclude(id=roles.first().id).delete()


@login_required
def roles_modal(request):
    if request.method == "POST":
        user = UserProfile.objects.get(id=request.POST['user_id'])
        change_description = request.POST.get('change_description')
        change_reason = request.POST.get('change_reason')
        role =Roles.objects.none()
        try:
            role = Roles.objects.get(id=request.POST['role'])
        except:pass
        app_id = request.POST['selectedapp_id']
        
        
        profile_mod = ProfileChange(
            user=user,
            change_date=datetime.now(),
            changed_by=user
        )
        profile_mod.save()
        user.add_role(role, app_id)
        responsibility = user.responsibilities.filter( user__id=user.id, role__app_id=app_id).first()
        responsibilityForm = ResponsibilitiesForm(request.POST, instance=responsibility)
        if responsibilityForm.is_valid():
            print("Saving responsibility")
            res= responsibilityForm.save()
            res.user = user
            res.save()
            for role in user.roles.filter(app_id=app_id):
                user.roles.remove(role)
            if res.role:
                user.roles.add(Roles.objects.get(id=res.role.id))
                print("Role added")
            if res.role and res.role.name:
                return JsonResponse({"status": "success", "appid":res.role.app_id.id, "role":res.role.name}, safe=False)
            else:
                return JsonResponse({"status": "success", "appid":app_id, "role":None}, safe=False)   
        else:
            print("Error: ", responsibilityForm.errors)
            user = UserProfile.objects.get(id=userid)
            regioncc=user.cost_center.get_region().get_decendance()
            regioncc_list = list(regioncc.values('id', 'code', 'name', 'parent'))
            return JsonResponse({"form":responsibilityForm.as_p(),"regioncc":regioncc_list, "app":Application.objects.get(id=appid ).fullname }, safe=False)
      
    remove_duplicates()
    userid = request.GET['user_id']
    appid = request.GET['app_id']
    user = UserProfile.objects.get(id=userid)
    roles = Roles.objects.filter(app_id=appid)
    """use a model form to assign roles to the user"""
    regioncc=user.cost_center.get_region().get_decendance()
    responsibility = user.responsibilities.filter(role__app_id=appid).first()
    form = ResponsibilitiesForm(roles_queryset=roles,cost_centers_queryset=regioncc, instance=responsibility)
    regioncc_list = list(regioncc.values('id', 'code', 'name', 'parent'))
    return JsonResponse({"form":form.as_p(),"regioncc":regioncc_list,"app":{'fullname':Application.objects.get(id=appid).fullname,'id':Application.objects.get(id=appid ).id} }, safe=False)


@login_required
def profile_deactivation_request(request):
    try:
        change_reason = request.POST.get('change_reason')
        change_description = request.POST.get('change_description')
        profile_username = request.POST.get('user_profile')
        application = request.POST.get('application')
        user = UserProfile.objects.filter(username=profile_username).first()
        auth_user = request.user
        if user:
            
            if not auth_user.cost_center:
                messages.error(request, "User does not have a cost center")
                return redirect("/change_requests/change_request_index")
            profile_deactivation = ProfileDeactivation(
                user=user,
                application=application,
                deactivation_date=datetime.now(),
                deactivated_by=user
            )
            profile_deactivation.save()

            cr_id = "CR-" + datetime.now().strftime("%Y%m%d%I%M%S")
            change_request = ChangeRequest(
                cr_id=cr_id,
                change_type="Profile Deactivation",
                profile_deactivation=profile_deactivation,
                change_description=change_description,
                change_reason=change_reason,
                application=application,
                creator_designation=user.designation,
                created_by=request.user,
                region=auth_user.region,
                cost_center=auth_user.cost_center if auth_user.cost_center else None,
                created_at=datetime.now()
            )
            change_request.save()
            
            messages.success(request, "Change request submitted successfully")   
            try:     
                # Get section head approver for this cost center
                application = Application.objects.filter(name="Change Requests").first()
                section_head_role = Roles.objects.filter(role="section_head", app_id=application.id).first()
                approver_responsibilities = Responsibilities.objects.filter(
                    role=section_head_role,
                cost_centers__in=[auth_user.cost_center]
                ).first()
                approver = approver_responsibilities.user if approver_responsibilities else None
                if not approver:
                    messages.error(request, "No section head approver found for this cost center")
                    return redirect("/change_requests/create_change_request")
                print("Sending email to: ", approver.email)
                email_template_name = 'registration/email.html'
                msg = "Profile deactivation request submitted successfully"
                type_ = "Profile Deactivation Request"
                app_base = "change_requests/profile_deactivation_request?i="+change_request.cr_id
                c = {
                    "email": approver.email if approver.email else "",
                    "message": msg,
                    "type": type_,
                    "redirect_app_base": app_base,
                    "id": change_request.cr_id,
                    "domain": request.META['HTTP_HOST'],
                    "site_name": "Zetdc Business Excellence",
                    "protocol": 'https' if request.is_secure() else 'http',
                }
                email = render_to_string(email_template_name, c, request=request)
                ms_exhange_reset_password_html(subject=type_,to_recipients=[approver.email], cc_recipients=[],template=email,
                                                kwargs={"kwargs": c})
            
                if approver.section:
                    messages.success(request, f'Section head approver {approver.first_name} {approver.last_name}, {approver.section.name} notified successfully')
                else:
                    messages.success(request, f'Section head approver {approver.first_name} {approver.last_name} notified successfully')
            except Exception as ex:
                print("error: ", str(ex))
        else:
            messages.error(request, "User not found")
    except Exception as ex:
        print("error: ", ex)
        messages.error(request, "An error occurred while submitting the change request")
        
    return redirect("/change_requests/change_request_index")

@login_required
def new_profile_request(request):
    if request.method == "GET":
        change_request = ChangeRequest.objects.get(cr_id=request.GET['i'])
        if change_request.new_profile:

                new_user = {
                    "id": change_request.new_profile.pk,
                    "username": change_request.new_profile.username,
                    "firstname": change_request.new_profile.first_name,
                    "lastname": change_request.new_profile.last_name,
                    "email": change_request.new_profile.email,
                    "roles_to_action": change_request.new_profile.roles_to_action,
                    "roles_actions": change_request.new_profile.roles_actions,
                    "section": Sections.objects.filter(id=change_request.new_profile.section.id).first() if change_request.new_profile.section else None,
                    "district": Districts.objects.filter(id=change_request.new_profile.district.id).first() if change_request.new_profile.district else None,
                    "region": Regions.objects.filter(id=change_request.new_profile.region.id).first() if change_request.new_profile.region else None,
                    "cost_center": CostCenter.objects.filter(id=change_request.new_profile.cost_center.id).first() if change_request.new_profile.cost_center else None,
                    "designation": Designations.objects.filter(id=change_request.new_profile.designation.id).first() if change_request.new_profile.designation else None,
                }

                cr = {
                    "user": new_user,
                    "cr_id": change_request.cr_id,
                    "change_reason": change_request.change_reason,
                    "change_description": change_request.change_description,
                    "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                    "creator_designation": change_request.creator_designation.description,
                    "created_at": change_request.created_at
                }
                return render(
                    request,
                    "change_requests/new_profile_request.html",
                    {
                        "user_applications": Application.objects.all(),
                        "user_designations": Designations.objects.all(),
                        "sections": Sections.objects.all(),
                        "districts": Districts.objects.all(),
                        "regions": Regions.objects.all(),
                        "user_title": request.user.get_full_name(),
                        "user_groups": list(request.user.groups.values_list('name', flat=True)),
                        "cr": cr
                    }
                )
                
@login_required
def update_change_request(request):
    if request.method == "GET":
        change_request = ChangeRequest.objects.get(cr_id=request.GET['i'])
        if change_request.new_profile:

                new_user = {
                    "id": change_request.new_profile.pk,
                    "username": change_request.new_profile.username,
                    "firstname": change_request.new_profile.first_name,
                    "lastname": change_request.new_profile.last_name,
                    "email": change_request.new_profile.email,
                    "roles_to_action": change_request.new_profile.roles_to_action,
                    "roles_actions": change_request.new_profile.roles_actions,
                    "section": Sections.objects.filter(id=change_request.new_profile.section.id).first() if change_request.new_profile.section else None,
                    "district": Districts.objects.filter(id=change_request.new_profile.district.id).first() if change_request.new_profile.district else None,
                    "region": Regions.objects.filter(id=change_request.new_profile.region.id).first() if change_request.new_profile.region else None,
                    "cost_center": CostCenter.objects.filter(id=change_request.new_profile.cost_center.id).first() if change_request.new_profile.cost_center else None,
                    "designation": Designations.objects.filter(id=change_request.new_profile.designation.id).first() if change_request.new_profile.designation else None,
                }

                cr = {
                    "user": new_user,
                    "cr_id": change_request.cr_id,
                    "change_reason": change_request.change_reason,
                    "change_description": change_request.change_description,
                    "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                    "creator_designation": change_request.creator_designation.description,
                    "created_at": change_request.created_at
                }
                return render(
                    request,
                    "change_requests/new_profile_request.html",
                    {
                        "user_applications": Application.objects.all(),
                        "user_designations": Designations.objects.all(),
                        "sections": Sections.objects.all(),
                        "districts": Districts.objects.all(),
                        "regions": Regions.objects.all(),
                        "user_title": request.user.get_full_name(),
                        "user_groups": list(request.user.groups.values_list('name', flat=True)),
                        "cr": cr
                    }
                )
        
        elif change_request.profile_change:
            profile_change = change_request.profile_change
            user = profile_change.user
            try:
                cost_center = user.cost_center
            except Exception as ex:
                print("error: ", ex)
                cost_center = None
            new_user = {
                "id": user.pk,
                "username": user.username,
                "firstname": user.first_name,
                "lastname": user.last_name,
                "email": user.email,
                "section": user.section,
                "district": user.district,
                "region": user.region,
                "cost_center": cost_center,
                "designation": user.designation if user.designation else None,
                "roles_to_action": profile_change.roles_to_action,
                "roles_actions": profile_change.roles_actions,
            }

            cr = {
                "user": new_user,
                "cr_id": change_request.cr_id,
                "change_reason": change_request.change_reason,
                "change_description": change_request.change_description,
                "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                "creator_designation": change_request.creator_designation.description,
                "created_at": change_request.created_at
            }
            return render(
                request,
                "change_requests/update_profile_modification.html",
                {
                    "user_applications": Application.objects.all(),
                    "user_designations": Designations.objects.all(),
                    "sections": Sections.objects.all(),
                    "districts": Districts.objects.all(),
                    "regions": Regions.objects.all(),
                    "user_title": request.user.get_full_name(),
                    "user_groups": list(request.user.groups.values_list('name', flat=True)),
                    "cr": cr,
                    "change_request": change_request
                }
            )
        
        elif change_request.profile_deactivation:
            profile_deactivation = change_request.profile_deactivation
            user = profile_deactivation.user
            cr = {
                "cr_id": change_request.cr_id,
                "change_reason": change_request.change_reason,
                "change_description": change_request.change_description,
                "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                "creator_designation": change_request.creator_designation.description,
                "created_at": change_request.created_at
            }
            return render(
                request,
                "change_requests/update_profile_deactivation.html",
                {
                    "user_applications": Application.objects.all(),
                    "user_designations": Designations.objects.all(),
                    "sections": Sections.objects.all(),
                    "districts": Districts.objects.all(),
                    "regions": Regions.objects.all(),
                    "user_title": request.user.get_full_name(),
                    "user_groups": list(request.user.groups.values_list('name', flat=True)),
                    "cr": cr,
                    "change_request": change_request
                }
            )
            
    elif request.method == "POST":
        try:
            cr_id = request.POST.get('cr_id')
            change_reason = request.POST.get('change_reason')
            change_description = request.POST.get('change_description')
            roles_to_action = request.POST.get('roles_to_action')
            roles_actions = request.POST.get('roles_actions')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            
            section_head_approval = CRApproval.objects.filter(cr_id=change_request, approver_role__role="section_head").first()
            if not change_request:
                messages.error(request, "Change request not found")
                return redirect("/change_requests/change_request_index")
            elif section_head_approval:
                messages.warning(request, "Change request has already been approved by the section head. You cannot update it")
                return redirect("/change_requests/change_request_index")
            else:
                
                change_request.change_reason = change_reason if change_reason else change_request.change_reason
                change_request.change_description = change_description if change_reason else change_request.change_description
                change_request.roles_to_action = roles_to_action if roles_to_action else change_request.roles_to_action
                change_request.roles_actions = roles_actions if roles_actions else change_request.roles_actions
                change_request.save()

                if change_request.profile_change:
                    profile_mod = ProfileChange.objects.filter(id=change_request.profile_change.id).first()
                    # if profile_mod.application == "BUSINESS EXCELLENCE":
                    #     roles = [role for role in [request.POST.get(app.name) for app in Application.objects.all() if request.POST.get(app.name) != 'Select Role'] if role and role != ""]
                    #     profile_mod.role_to_assign.clear()
                    #     profile_mod.role_to_assign.add(*Roles.objects.filter(id__in=roles))
                    #     profile_mod.save()
                    
                elif change_request.profile_deactivation:
                    profile_deactivation = ProfileDeactivation.objects.filter(id=change_request.profile_deactivation.id).first()
                    profile_deactivation.application = request.POST.get('application')
                    profile_deactivation.save()
                # clear approvals
                CRApproval.objects.filter(cr_id=change_request).delete()
                messages.success(request, "Change Request updated successfully")
        except Exception as ex:
            traceback.print_exc()
            print("save user error", ex)
            messages.error(request, "An error occurred while saving the change request")
    
        return redirect("/change_requests/change_request_index")
                
@login_required
def view_profile_request(request):
    if request.method == "GET":
        change_request = ChangeRequest.objects.get(cr_id=request.GET['i'])
        
        role = request.user.get_user_role_for_application("change_requests")
        user_role = role.role if role else None
        print("user_role: ", user_role)
        user_responsibilities = Responsibilities.objects.filter(user=request.user, role=role).first() if role else None
        print("user_responsibilities: ", user_responsibilities)
        cost_centers = user_responsibilities.cost_centers.all() if user_responsibilities else []
        print("cost_centers: ", cost_centers)
        section_head_allowed = False
        it_section_head_allowed = False
        if user_role == "section_head":
            if change_request.cost_center in cost_centers:
                section_head_allowed = True
        elif user_role == "it_section_head":
            if change_request.cost_center in cost_centers:
                it_section_head_allowed = True
        
        # Set modal_auto_show to False to prevent modals from showing automatically
        modal_auto_show = False
        
        if change_request.new_profile:

                new_user = {
                    "id": change_request.new_profile.pk,
                    "username": change_request.new_profile.username,
                    "firstname": change_request.new_profile.first_name,
                    "lastname": change_request.new_profile.last_name,
                    "email": change_request.new_profile.email,
                    "roles_to_action": change_request.new_profile.roles_to_action,
                    "roles_actions": change_request.new_profile.roles_actions,
                    "section": Sections.objects.filter(id=change_request.new_profile.section.id).first() if change_request.new_profile.section else None,
                    "district": Districts.objects.filter(id=change_request.new_profile.district.id).first() if change_request.new_profile.district else None,
                    "region": Regions.objects.filter(id=change_request.new_profile.region.id).first() if change_request.new_profile.region else None,
                    "cost_center": CostCenter.objects.filter(id=change_request.new_profile.cost_center.id).first() if change_request.new_profile.cost_center else None,
                    "designation": Designations.objects.filter(id=change_request.new_profile.designation.id).first() if change_request.new_profile.designation else None,
                }

                cr = {
                    "user": new_user,
                    "cr_id": change_request.cr_id,
                    "change_reason": change_request.change_reason,
                    "change_description": change_request.change_description,
                    "application": change_request.application,
                    "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                    "creator_designation": change_request.creator_designation.description,
                    "created_at": change_request.created_at
                }
                
                # get all approvals
                cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
                section_head_awaiting_action = True
                it_section_head_awaiting_action = True
                for approval in cr_approvals:
                    if approval.approver_role.role == "section_head":
                        section_head_awaiting_action = False
                        if approval.approval_status == False:
                            it_section_head_awaiting_action = False
                    if approval.approver_role.role == "it_section_head":
                        it_section_head_awaiting_action = False
                
                requestor = UserProfile.objects.filter(username=request.user.username).first()
                requestor_role = requestor.get_user_roles_for_application("change_requests")

                return render(
                    request,
                    "change_requests/view_profile_request.html",
                    {
                        "section_head_allowed": section_head_allowed,
                        "it_section_head_allowed": it_section_head_allowed,
                        "requestor_role": requestor_role,
                        "section_head_awaiting_action": section_head_awaiting_action,
                        "it_section_head_awaiting_action": it_section_head_awaiting_action,
                        "user_applications": Application.objects.all(),
                        "user_designations": Designations.objects.all(),
                        "sections": Sections.objects.all(),
                        "districts": Districts.objects.all(),
                        "regions": Regions.objects.all(),
                        "cr_approvals": cr_approvals,
                        "user_title": request.user.get_full_name(),
                        "user_groups": list(request.user.groups.values_list('name', flat=True)),
                        "cr": cr,
                        "modal_auto_show": modal_auto_show
                    }
                )
        
        elif change_request.profile_change:
            profile_change = change_request.profile_change
            user = profile_change.user
            try:
                cost_center = user.cost_center
            except Exception as ex:
                print("error: ", ex)
                cost_center = None

            new_user = {
                "id": user.pk,
                "username": user.username,
                "firstname": user.first_name,
                "lastname": user.last_name,
                "email": user.email,
                "section": user.section,
                "district": user.district,
                "region": user.region,
                "cost_center": cost_center,
                "designation": user.designation,
                "roles_to_action": profile_change.roles_to_action,
                "roles_actions": profile_change.roles_actions,
            }

            cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
            section_head_awaiting_action = True
            it_section_head_awaiting_action = True
            for approval in cr_approvals:
                if approval.approver_role.role == "section_head":
                    section_head_awaiting_action = False
                    if approval.approval_status == False:
                        it_section_head_awaiting_action = False
                if approval.approver_role.role == "it_section_head":
                    it_section_head_awaiting_action = False
            
            print("section_head_awaiting_action: ", section_head_awaiting_action)
            print("it_section_head_awaiting_action: ", it_section_head_awaiting_action)
            requestor = UserProfile.objects.filter(username=request.user.username).first()
            requestor_role = requestor.get_user_roles_for_application("change_requests")
            cr = {
                "user": new_user,
                "cr_id": change_request.cr_id,
                "change_reason": change_request.change_reason,
                "change_description": change_request.change_description,
                "application": change_request.application,
                "roles_to_action": profile_change.roles_to_action,
                "roles_actions": profile_change.roles_actions,
                "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                "creator_designation": change_request.creator_designation.description,
                "created_at": change_request.created_at
            }
            return render(
                request,
                "change_requests/view_profile_modification.html",
                {
                    "section_head_allowed": section_head_allowed,
                    "it_section_head_allowed": it_section_head_allowed,
                    "requestor_role": requestor_role,
                    "section_head_awaiting_action": section_head_awaiting_action,
                    "it_section_head_awaiting_action": it_section_head_awaiting_action,
                    "user_applications": Application.objects.all(),
                    "user_designations": Designations.objects.all(),
                    "sections": Sections.objects.all(),
                    "districts": Districts.objects.all(),
                    "regions": Regions.objects.all(),
                    "user_title": request.user.get_full_name(),
                    "user_groups": list(request.user.groups.values_list('name', flat=True)),
                    "cr": cr,
                    "cr_approvals": cr_approvals,
                    "change_request": change_request
                }
            )

        elif change_request.profile_deactivation:
            profile_deactivation = change_request.profile_deactivation
            user = profile_deactivation.user
            cr = {
                "cr_id": change_request.cr_id,
                "change_reason": change_request.change_reason,
                "change_description": change_request.change_description,
                "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                "creator_designation": change_request.creator_designation.description,
                "created_at": change_request.created_at
            }
            
            cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
            section_head_awaiting_action = True
            it_section_head_awaiting_action = True
            for approval in cr_approvals:
                if approval.approver_role.role == "section_head":
                    section_head_awaiting_action = False
                    if approval.approval_status == False:
                        it_section_head_awaiting_action = False
                if approval.approver_role.role == "it_section_head":
                    it_section_head_awaiting_action = False
            
            requestor = UserProfile.objects.filter(username=request.user.username).first()
            requestor_role = requestor.get_user_roles_for_application("change_requests")
            return render(
                request,
                "change_requests/view_profile_deactivation.html",
                {
                    "section_head_allowed": section_head_allowed,
                    "it_section_head_allowed": it_section_head_allowed,
                    "user_applications": Application.objects.all(),
                    "user_designations": Designations.objects.all(),
                    "sections": Sections.objects.all(),
                    "districts": Districts.objects.all(),
                    "regions": Regions.objects.all(),
                    "user_title": request.user.get_full_name(),
                    "user_groups": list(request.user.groups.values_list('name', flat=True)),
                    "requestor_role": requestor_role,
                    "section_head_awaiting_action": section_head_awaiting_action,
                    "it_section_head_awaiting_action": it_section_head_awaiting_action,
                    "cr": cr,
                    "change_request": change_request,
                    "cr_approvals": cr_approvals,
                }
            )
            
@login_required
def get_user_data(request, username):
    user = UserProfile.objects.filter(username=username).first()
    applications = Application.objects.all()
    all_roles = {app.name: [model_to_dict(role) for role in Roles.objects.filter(app_id=app.id).all()] for app in Application.objects.all()}
    active_roles = {role.app_id.name: model_to_dict(role) for role in user.roles.all() if role.app_id}
    
    if user:
        return JsonResponse({
            "applications": list(applications.values('id', 'name', 'fullname')),
            "userData": all_roles,
            "active_roles": active_roles,
        })
    else:
        return JsonResponse({
            "error": "User not found",
            "applications": [],
            "userData": []
        })

@login_required
def update_new_profile_request(request):
    if request.method == "POST":
        try:
            cr_id = request.POST.get('cr_id')
            change_reason = request.POST.get('change_reason')
            change_description = request.POST.get('change_description')
            roles_to_action = request.POST.get('roles_to_action')
            roles_actions = request.POST.get('roles_actions')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            
            section_head_approval = CRApproval.objects.filter(cr_id=change_request, approver_role__role="section_head").first()
            if not change_request:
                messages.error(request, "Change request not found")
                return redirect("/change_requests/change_request_index")
            elif section_head_approval:
                messages.warning(request, "Change request has already been approved by the section head. You cannot update it")
                return redirect("/change_requests/change_request_index")
            else:
                change_request.roles_to_action = roles_to_action if roles_to_action else change_request.new_profile.roles_to_action
                change_request.roles_actions = roles_actions if roles_actions else change_request.new_profile.roles_actions
                change_request.change_reason = change_reason if change_reason else change_request.change_reason
                change_request.change_description = change_description if change_reason else change_request.change_description
                change_request.save()
            
                user_data = {
                    'first_name': request.POST.get('firstname'),
                    'last_name': request.POST.get('lastname'),
                    'username': request.POST.get('username'),
                    'email': request.POST.get('email'),
                    'roles_to_action': roles_to_action if roles_to_action else change_request.roles_to_action,
                    'roles_actions': roles_actions if roles_actions else change_request.roles_actions,
                    'region': Regions.objects.filter(id=request.POST.get('region')).first(),
                    'cost_center': CostCenter.objects.filter(id=request.POST.get('cost_center')).first() if request.POST.get('cost_center') not in ["Select Cost Center", ""] else None,
                    'district': Districts.objects.filter(id=request.POST.get('district')).first() if request.POST.get('district') not in ["Select District", ""] else None,
                    'section': Sections.objects.filter(code=request.POST.get('section')).first(),
                    'designation': Designations.objects.filter(id=request.POST.get('designation')).first() if request.POST.get('designation') not in ["Select Designation", ""] else None
                }

                if change_request.new_profile:
                    user_id = change_request.new_profile.id
                    user = NewProfile.objects.filter(id=user_id).first()
                    for field, value in user_data.items():
                        if value:
                            setattr(user, field, value)

                    user.save()

                    roles = [role for role in [request.POST.get(app.name) for app in Application.objects.all() if request.POST.get(app.name) != 'Select Role'] if role and role != ""]
                    user.roles.clear()
                    user.roles.add(*Roles.objects.filter(id__in=roles))
                
                # clear approvals
                CRApproval.objects.filter(cr_id=change_request).delete()
                messages.success(request, "Change Request updated successfully")
        except Exception as ex:
            traceback.print_exc()
            print("save user error", ex)
            messages.error(request, "An error occurred while saving the change request")
    
        return redirect("/change_requests/change_request_index")
    
@login_required
def approve_profile_request(request):
    if request.method == "POST":
        try:
            action_button = request.POST.get('actionButton')
            cr_id = request.POST.get('cr_id')
            requestor = UserProfile.objects.filter(username=request.user.username).first()
            user_role = requestor.get_user_roles_for_application("change_requests")
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            if 'APPROVE' in action_button:
                # The "APPROVE CHANGE REQUEST" button was clicked
                if not change_request:
                    messages.error(request, "Change request not found")
                    return redirect("/change_requests/change_request_index")
                else:
                    
                    if user_role == "section_head":
                        cr_approval = CRApproval(
                            cr_id=change_request,
                            approver=request.user,
                            approver_role=requestor.get_user_role_for_application("change_requests"),
                            approval_status=True,
                            approval_date=timezone.now()
                        )
                        cr_approval.save()
                        messages.success(request, "Change Request approved successfully")
                        try:
                            region = change_request.region
                            region_cost_center = CostCenter.objects.filter(Q(code=region.code), Q(code="CC"+region.code)).first()
                            # Get section head approver for this cost center
                            application = Application.objects.filter(name="Change Requests").first()
                            section_head_role = Roles.objects.filter(role="section_head", app_id=application.id).first()
                            approver_responsibilities = Responsibilities.objects.filter(
                                role=section_head_role,
                                cost_centers__in=[region_cost_center]
                            ).first()
                            approver = approver_responsibilities.user if approver_responsibilities else None
                            if not approver:
                                messages.error(request, "No IT section head approver found for this cost center")
                                return redirect("/change_requests/change_request_index")
                            print("Sending email to: ", approver.email)
                            cr_type = "new_profile_request" if change_request.change_type == "new_profile" else "profile_modification_request" if change_request.change_type == "profile_modification" else "profile_deactivation_request" if change_request.change_type == "profile_deactivation" else ""
                            ms_exhange_send_html("Change Request Implementation", [approver.email], [], "emails/email_template.html", {
                                "message": "Change Request Implementation",
                                "type": "Change Request Implementation",
                                "redirect_url": "https://172.16.29.32:9300/change_requests/" + cr_type + "?i=" + change_request.cr_id
                            })
                            
                            messages.success(request, "Section head approver notified successfully")
                        except Exception as ex:
                            print("error: ", ex)
                    else:
                        messages.error(request, "Error. Please check your Change Request role")
                    
                    return redirect("/change_requests/change_request_index")
                    
            elif 'REJECT' in action_button:
                # The "REJECT CHANGE REQUEST" button was clicked
                cr_approval = CRApproval(
                    cr_id=change_request,
                    approver=request.user,
                    approver_role=requestor.get_user_role_for_application("change_requests"),
                    approval_status=False,
                    comment=request.POST.get('rejectReason'),
                    approval_date=timezone.now()
                )
                cr_approval.save()
                messages.success(request, "Change Request rejected successfully")
                
                return redirect("/change_requests/change_request_index")
            elif 'APPLY' in action_button:
                # The "APPLY CHANGE REQUEST" button was clicked
                    
                if user_role == "it_section_head":
                    roles_actions = request.POST.get('roles_actions')
                    print("roles_actions: ", roles_actions)
                    if roles_actions:
                        roles_actions = roles_actions.strip()
<<<<<<< HEAD
                        if change_request.change_type == "new_profile":
                            new_profile = change_request.new_profile
                            new_profile.roles_actions = roles_actions if roles_actions else new_profile.roles_actions
                            new_profile.save()
                        elif change_request.change_type == "profile_modification":
                            profile_modification = change_request.profile_modification
                            profile_modification.roles_actions = roles_actions if roles_actions else profile_modification.roles_actions
                            profile_modification.save()
=======
                    if not roles_actions:
                        messages.error(request, "Please enter the roles implemented")
                        return redirect("/change_requests/change_request_index")
                    if change_request.change_type == "new_profile":
                        new_profile = change_request.new_profile
                        print("new_profile: ", new_profile)
                        new_profile.roles_actions = roles_actions
                        new_profile.save()
                    elif change_request.change_type == "profile_modification":
                        profile_modification = change_request.profile_modification
                        print("profile modification: ", profile_modification)
                        profile_modification.roles_actions = roles_actions
                        profile_modification.save()
>>>>>>> de24f90 (...)
                        
                    cr_approval = CRApproval(
                        cr_id=change_request,
                        approver=request.user,
                        approver_role=requestor.get_user_role_for_application("change_requests"),
                        approval_status=True,
                        approval_date=timezone.now()
                    )
                    cr_approval.save()
                    messages.success(request, "Change Request approved successfully")
                    return redirect("/change_requests/change_request_index")

        except Exception as ex:
            print("error: ", ex)
            # messages.error(request, "An error occurred while approving the change request " + str(ex))
    return redirect("/change_requests/change_request_index")

@login_required
def change_request_index(request):

    user_page = 'change_requests/change_request_index.html'
    user_title = request.user.get_full_name()
    regions = Regions.objects.all()
    return render(
        request,
        user_page,
        {
            "title": "Change Requests",
            "user_title": user_title,
            "regions": regions
        })
    
@login_required
def change_request_reports(request):

    user_page = 'change_requests/change_request_reports.html'
    user_title = request.user.get_full_name()
    regions = Regions.objects.all()
    return render(
        request,
        user_page,
        {
            "title": "Change Requests Reports",
            "user_title": user_title,
            "regions": regions
        })
    
@login_required
def datatable_data(request, view):
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    length = int(request.GET.get('length', default=10))
    search_value = request.GET.get('search[value]', default='')
    
    try:
        user = request.user
        
        print("view: ", view)

        if user.region:
            # Fetch your data from the model
            records = ChangeRequest.objects.filter(region=user.region)
            # Filter based on search value
            if search_value and records:
                records = records.filter(
                Q(change_reason__icontains=search_value) |
                Q(change_description__icontains=search_value) |
                Q(application__icontains=search_value) |
                Q(new_profile__first_name__icontains=search_value) |
                Q(new_profile__last_name__icontains=search_value) |
                Q(new_profile__email__icontains=search_value) |
                Q(new_profile__username__icontains=search_value)
                )
            
            # Sorting
            order_column = request.GET.get('order[0][column]')
            order = request.GET.get('order[0][dir]')
            if order_column:
                column_name = request.GET.get(f'columns[{order_column}][data]')
                if column_name != "it_section_head_approval" and column_name != "section_head_approval":
                    column_name = f'{column_name}'
                else:
                    column_name = "created_at"
                if order == 'desc' and column_name != 'it_section_head_approval' and column_name != 'section_head_approval':
                    column_name = f'-{column_name}'
                records = records.order_by(column_name)
            
            if view == "filter":
                region = request.GET.get('region')
                cr_type = request.GET.get('cr_type')
                cr_app = request.GET.get('cr_app')
                status = request.GET.get('status')
                cost_center = request.GET.get('cost_center')
                start_date = request.GET.get('start_date')
                end_date = request.GET.get('end_date')
                print("region: ", region, " cr_type: ", cr_type, " cr_app: ", cr_app, " status: ", status, " cost_center: ")
                if region:
                    region_ = Regions.objects.filter(id=region).first()
                    records = records.filter(region=region_)
                if cr_type:
                    records = records.filter(change_type=cr_type)
                if cr_app:
                    records = records.filter(application=cr_app)
                if status:
                    if status == "Pending SH":
                        records = records.filter(~Q(crapproval__approver_role__role="section_head"))
                    if status == "Pending IT":
                        records = records.filter(
                                Q(crapproval__approver_role__role="section_head") & 
                                Q(crapproval__approval_status=True)
                            ).exclude(
                                Q(crapproval__approver_role__role="it_section_head") & 
                                Q(crapproval__approval_status=True)
                            )
                    if status == "Complete":
                        records = records.filter(
                            Q(crapproval__approver_role__role="it_section_head") & 
                            Q(crapproval__approval_status=True)
                        )
                    if status == "Rejected":
                        records = records.filter(
                                (Q(crapproval__approver_role__role="section_head") & 
                                Q(crapproval__approval_status=False)) |
                                Q(crapproval__approver_role__role="it_section_head") & 
                                Q(crapproval__approval_status=False)
                            )
                if cost_center:
                    cost_center_ = CostCenter.objects.filter(id=cost_center).first()
                    records = records.filter(cost_center=cost_center_)  
                if start_date and end_date:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date, "%Y-%m-%d")
                    records = records.filter(created_at__range=[start_date, end_date])
            
            elif view == "incoming_cr":
                role = user.get_user_role_for_application("change_requests")
                user_role = role.role if role else None
                print("user_role: ", user_role)
                user_responsibilities = Responsibilities.objects.filter(user=user, role=role).first() if role else None
                print("user_responsibilities: ", user_responsibilities)
                cost_centers = user_responsibilities.cost_centers.all() if user_responsibilities else []
                print("cost_centers: ", cost_centers)
                if user_role == "section_head":
                    records = records.filter(
                        ~Q(crapproval__approver_role__role="section_head"),
                        cost_center__in=cost_centers
                        ).order_by('-created_at')
                    print("section_head records: ", records)
                elif user_role == "it_section_head":
                    # Filter for records approved by section head and not yet handled by IT section head
                    # Exclude records rejected by section head
                    records = records.filter(
                        Q(crapproval__approver_role__role="section_head") & 
                        Q(crapproval__approval_status=True)
                    ).exclude(
                        Q(crapproval__approver_role__role="section_head") &
                        Q(crapproval__approval_status=False)
                    ).exclude(
                        Q(crapproval__approver_role__role="it_section_head")
                    )
                    # records = ChangeRequest.objects.filter(~Q(crapproval__approver_role__role="it_section_head")).all()
                    print("it_section_head records: ", records)
                print("records: ", records)
            # Total number of records before filtering
            total = records.count() if records else 0

            # Pagination
            paginator = Paginator(records, length)
            page_number = start // length + 1
            page_obj = paginator.get_page(page_number)

            # Prepare response
            data = []
            for obj in page_obj:
                try:
                    section_head_approval = CRApproval.objects.filter(cr_id=obj, approver_role__role="section_head").first()
                    it_section_head_approval = CRApproval.objects.filter(cr_id=obj, approver_role__role="it_section_head").first()
                    
                    sh_status = "Pending"
                    if section_head_approval:
                        sh_status = "Approved" if section_head_approval.approval_status else "Rejected"
                    itsh = "Pending"
                    if it_section_head_approval:
                        itsh = "Approved" if it_section_head_approval.approval_status else "Rejected"
                    change_requests = {
                        "cr_id": obj.cr_id,
                        "change_type": obj.change_type,
                        "change_description": obj.change_description,
                        "change_reason": obj.change_reason,
                        "application": obj.application,
                        "section_head_approval": sh_status,
                        "it_section_head_approval": itsh,
                        "creator_designation": obj.creator_designation.description,
                        "created_by": obj.created_by.first_name + " " + obj.created_by.last_name,
                        "region": obj.region.region,
                        "cost_center": obj.cost_center.name if obj.cost_center else "",
                        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M"),
                    }

                    data.append(change_requests)
                except Exception as ex:
                    print("Cost Center Error: ", ex)

            return JsonResponse({
                'draw': draw,
                'recordsTotal': total,
                'recordsFiltered': total,
                'data': data
            })

    except Exception as ex:
        print("Error: ", ex)
        traceback.print_exc()
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

def get_filtered_change_requests(records, user_id, search_value, column_name, user_region, region, cr_type, cr_app, status, cost_center, start_date, end_date):
    
    try:
        print("region: ", region, " cr_type: ", cr_type, " cr_app: ", cr_app, " status: ", status, " cost_center: ")
        if region:
            region_ = Regions.objects.filter(id=region).first()
            records = records.filter(region=region_)
        if cr_type:
            records = records.filter(change_type=cr_type)
        if cr_app:
            records = records.filter(application=cr_app)
        if status:
            if status == "Pending SH":
                records = records.filter(~Q(crapproval__approver_role__role="section_head"))
            if status == "Pending IT":
                records = records.filter(
                        Q(crapproval__approver_role__role="section_head") & 
                        Q(crapproval__approval_status=True)
                    ).exclude(
                        Q(crapproval__approver_role__role="it_section_head") & 
                        Q(crapproval__approval_status=True)
                    )
            if status == "Complete":
                records = records.filter(
                    Q(crapproval__approver_role__role="it_section_head") & 
                    Q(crapproval__approval_status=True)
                )
            if status == "Rejected":
                records = records.filter(
                        (Q(crapproval__approver_role__role="section_head") & 
                        Q(crapproval__approval_status=False)) |
                        Q(crapproval__approver_role__role="it_section_head") & 
                        Q(crapproval__approval_status=False)
                    )
        if cost_center:
            cost_center_ = CostCenter.objects.filter(id=cost_center).first()
            records = records.filter(cost_center=cost_center_)  
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            records = records.filter(created_at__range=[start_date, end_date])
            
        data = []
        for obj in records:
            section_head_approval = CRApproval.objects.filter(cr_id=obj, approver_role__role="section_head").first()
            it_section_head_approval = CRApproval.objects.filter(cr_id=obj, approver_role__role="it_section_head").first()
            
            sh_status = "Pending"
            if section_head_approval:
                sh_status = "Approved" if section_head_approval.approval_status else "Rejected"
            itsh = "Pending"
            if it_section_head_approval:
                itsh = "Approved" if it_section_head_approval.approval_status else "Rejected"
            change_requests = {
                "cr_id": obj.cr_id,
                "change_type": obj.change_type,
                "change_description": obj.change_description,
                "change_reason": obj.change_reason,
                "section_head_approval": sh_status,
                "it_section_head_approval": itsh,
                "creator_designation": obj.creator_designation.description,
                "created_by": obj.created_by.first_name + " " + obj.created_by.last_name,
                "region": obj.region.region,
                "cost_center": obj.cost_center.name,
                "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M"),
            }

            data.append(change_requests)
        return data
    except Exception as ex:
        print("ex: ", ex)
    
    return data

def get_csv_export(request):
    
    print("export csv")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rfq.csv"'
    try:  
        region = request.GET.get('region')
        cr_type = request.GET.get('cr_type')
        cr_app = request.GET.get('cr_app')
        status = request.GET.get('status')
        cost_center = request.GET.get('cost_center')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')  
        user_id = request.user.id
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
            records = ChangeRequest.objects.filter(region=user_region)
        except Exception as ex:
            user_region = None
            records = None
            print("error: ",  ex)
        print("region: ", region, " cr_type: ", cr_type, " cr_app: ", cr_app, " status: ", status, " cost_center: ")
        records_ = get_filtered_change_requests(records, user_id=user_id, search_value="", column_name="", user_region=user_region, region=region, cr_type=cr_type, cr_app=cr_app, status=status, cost_center=cost_center, start_date=start_date, end_date=end_date)
        # build csv file and return as response
        try:
            writer = csv.writer(response)
            writer.writerow(['CR ID', 'Change Type', 'Change Description', 'Change Reason', 'Section Head Approval', 'IT Section Head Approval', 'Creator Designation', 'Created By', 'Region', 'Cost Center', 'Created At'])
            for item in records_:
                try:
                    writer.writerow([item['cr_id'], item['change_type'], item['change_description'], item['change_reason'], item['section_head_approval'], item['it_section_head_approval'], item['creator_designation'], item['created_by'], item['region'], item['cost_center'], item['created_at']])
                    
                except Exception as ex:
                    print("For Writting to CSV: ", ex)
        except Exception as ex:
            print("Error Writting to CSV: ", ex)
    except Exception as ex:
        print("Error: ", ex)
    
    
    return response
