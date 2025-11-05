import csv
import logging
from datetime import datetime
from django.template.loader import render_to_string
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.db import transaction

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
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
import time
import logging

# Initialize logger
logger = logging.getLogger(__name__)

from it.users.views import ms_exhange_reset_password_html, ms_exhange_send_html
from it.users.models import RoleDelegation, DelegationNotification
from .pagination import get_paginated_data, CursorPaginator
from .query_analysis import monitor_performance, analyze_queryset_performance
from .constants import (
    ERROR_MESSAGES, SUCCESS_MESSAGES, WARNING_MESSAGES, LOG_MESSAGES,
    MAX_REASON_LENGTH, MAX_DESCRIPTION_LENGTH, REQUIRED_CHANGE_REQUEST_FIELDS,
    REQUIRED_NEW_PROFILE_FIELDS, URL_PATTERNS, CACHE_TIMEOUT, USER_DATA_CACHE_KEY_PREFIX,
    PROFILE_CHANGE_STATUS, APPLICATION_NAMES
)

# Import service layer
from .services import (
    ChangeRequestService, CRTypeHandler, ApprovalService, ApprovalWorkflow,
    NotificationService, ContextBuilder, NewProfileHandler, ProfileModificationHandler,
    ProfileDeactivationHandler
)

# Create your views here.

# Set up logging
logger = logging.getLogger(__name__)

def validate_change_request_data(data):
    """Validate change request input data"""
    errors = []
    
    for field in REQUIRED_CHANGE_REQUEST_FIELDS:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    if len(data.get('change_reason', '')) > MAX_REASON_LENGTH:
        errors.append(f"Change reason too long (max {MAX_REASON_LENGTH} characters)")
    
    if len(data.get('change_description', '')) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Change description too long (max {MAX_DESCRIPTION_LENGTH} characters)")
    
    return errors

def validate_new_profile_data(data):
    """Validate new profile data"""
    errors = []
    
    for field in REQUIRED_NEW_PROFILE_FIELDS:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Check for duplicate username
    if data.get('username') and NewProfile.objects.filter(username=data['username']).exists():
        errors.append(ERROR_MESSAGES['DUPLICATE_USERNAME'])
    
    return errors

def sanitize_input(data):
    """Sanitize user input to prevent XSS attacks"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = escape(value.strip())
        else:
            sanitized[key] = value
    return sanitized

def check_change_request_permissions(user, change_request):
    """Check if user has permission to modify change request"""
    if not change_request:
        return False, "Change request not found"
    
    # Check if user is the creator (owner can edit their own request)
    if change_request.created_by == user:
        return True, "User is the creator"
    
    # Check if user has section head role for the cost center
    try:
        user_role = user.get_user_role_for_application("change_requests")
        if user_role and user_role.role == "section_head":
            user_responsibilities = Responsibilities.objects.filter(
                user=user, role=user_role
            ).first()
            if user_responsibilities and change_request.cost_center in user_responsibilities.cost_centers.all():
                return True, "User has section head permissions"
        # Check if user has IT section head role
        elif user_role and user_role.role == "it_section_head":
            user_responsibilities = Responsibilities.objects.filter(
                user=user, role=user_role
            ).first()
            if user_responsibilities and change_request.cost_center in user_responsibilities.cost_centers.all():
                return True, "User has IT section head permissions"
    except Exception:
        pass
    
    return False, "Insufficient permissions to edit this request"

@monitor_performance(threshold_ms=200)
def get_change_requests_optimized(user, filters=None, include_deleted=False):
    """Optimized query for change requests with select_related and prefetch_related"""
    from it.users.models import Responsibilities
    
    queryset = ChangeRequest.objects.select_related(
        'new_profile',
        'profile_change__user',
        'profile_deactivation__user',
        'created_by',
        'creator_designation',
        'region',
        'cost_center'
    ).prefetch_related(
        'crapproval_set__approver',
        'crapproval_set__approver_role'
    ).filter(region=user.region)
    
    # Exclude soft-deleted records by default
    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)
    
    # Get user role for change requests application
    user_role = user.get_user_role_for_application("change_requests")
    user_role_name = user_role.role if user_role else None
    
    # Apply role-based filtering
    if user_role_name in ["section_head", "it_section_head"]:
        # Users with approval roles see awaiting action records first
        # This will be handled in the datatable_data function for specific views
        pass
    else:
        # General users see only records they created or from their cost center
        user_responsibilities = Responsibilities.objects.filter(user=user, role=user_role).first() if user_role else None
        if user_responsibilities:
            cost_centers = user_responsibilities.cost_centers.all()
            queryset = queryset.filter(
                Q(created_by=user) | Q(cost_center__in=cost_centers)
            )
        else:
            # If no responsibilities, only show records they created
            queryset = queryset.filter(created_by=user)
    
    # Default ordering by creation date (newest first)
    queryset = queryset.order_by('-created_at')
    
    if filters:
        queryset = apply_filters(queryset, filters)
    
    return queryset

@monitor_performance(threshold_ms=150)
def get_filtered_records(user, view_type, additional_filters=None):
    """
    Simplified filtering logic for different view types.
    Reduces complexity and improves maintainability.
    """
    from it.users.models import Responsibilities
    
    base_queryset = get_change_requests_optimized(user)
    
    if view_type == "incoming_cr":
        # Show records awaiting user's approval
        role = user.get_user_role_for_application("change_requests")
        if role and role.role == "section_head":
            user_responsibilities = Responsibilities.objects.filter(user=user, role=role).first()
            if user_responsibilities:
                cost_centers = user_responsibilities.cost_centers.all()
                return base_queryset.filter(
                    ~Q(crapproval__approver_role__role="section_head"),
                    cost_center__in=cost_centers
                )
        elif role and role.role == "it_section_head":
            return base_queryset.filter(
                Q(crapproval__approver_role__role="section_head", crapproval__approval_status=True),
                ~Q(crapproval__approver_role__role="it_section_head")
            )
    
    elif view_type == "delegation_requests":
        return base_queryset.filter(change_type="Temporary Role Delegation")
    
    elif view_type == "active_delegations":
        return base_queryset.filter(
            change_type="Temporary Role Delegation",
            crapproval__approver_role__role="it_section_head",
            crapproval__approval_status=True
        )
    
    return base_queryset

def apply_filters(queryset, filters):
    """Apply filters to the queryset"""
    if filters.get('change_type'):
        queryset = queryset.filter(change_type=filters['change_type'])
    
    if filters.get('application'):
        queryset = queryset.filter(application=filters['application'])
    
    if filters.get('created_by'):
        queryset = queryset.filter(created_by__username=filters['created_by'])
    
    if filters.get('date_from'):
        queryset = queryset.filter(created_at__gte=filters['date_from'])
    
    if filters.get('date_to'):
        queryset = queryset.filter(created_at__lte=filters['date_to'])
    
    return queryset

def get_cached_user_data(username):
    """Get cached user data to reduce database queries"""
    from django.core.cache import cache
    
    cache_key = f"{USER_DATA_CACHE_KEY_PREFIX}{username}"
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        user = UserProfile.objects.filter(username=username).first()
        if user:
            applications = Application.objects.all()
            all_roles = {app.name: [model_to_dict(role) for role in Roles.objects.filter(app_id=app.id).all()] for app in applications}
            active_roles = {role.app_id.name: model_to_dict(role) for role in user.roles.all() if role.app_id}
            
            cached_data = {
                "applications": list(applications.values('id', 'name', 'fullname')),
                "userData": all_roles,
                "active_roles": active_roles,
            }
            cache.set(cache_key, cached_data, CACHE_TIMEOUT)
    
    return cached_data

def prepare_change_request_data(change_request):
    """Prepare change request data for display"""
    data = {
        'cr_id': change_request.cr_id,
        'change_type': change_request.change_type,
        'change_reason': change_request.change_reason,
        'change_description': change_request.change_description,
        'created_by': change_request.created_by,
        'created_at': change_request.created_at,
        'is_deleted': change_request.is_deleted,
    }
    
    if change_request.new_profile:
        data['new_profile'] = {
            'username': change_request.new_profile.username,
            'first_name': change_request.new_profile.first_name,
            'last_name': change_request.new_profile.last_name,
            'email': change_request.new_profile.email,
        }
    
    return data

def get_approval_status(change_request):
    """Get approval status for a change request"""
    section_head_approval = CRApproval.objects.filter(
        cr_id=change_request, 
        approver_role__role="section_head"
    ).first()
    
    it_section_head_approval = CRApproval.objects.filter(
        cr_id=change_request, 
        approver_role__role="it_section_head"
    ).first()
    
    if it_section_head_approval and it_section_head_approval.approval_status:
        return 'Complete'
    elif section_head_approval and section_head_approval.approval_status:
        return 'Pending IT'
    else:
        return 'Pending SH'

def send_approval_notification(change_request, approver, notification_type):
    """Send approval notification email"""
    try:
        # This would integrate with the existing email system
        logger.info(f"Approval notification sent: {notification_type} for {change_request.cr_id} by {approver.username}")
        return True
    except Exception as ex:
        logger.error(f"Failed to send approval notification: {str(ex)}")
        return False

def log_change_request_action(action, cr_id, username, details=None):
    """Log change request actions for audit trail"""
    log_message = f"Change request {action}: {cr_id} by {username}"
    if details:
        log_message += f" - {details}"
    
    logger.info(log_message)

@csrf_protect
@login_required
def delete_change_request(request):
    """Soft delete a change request"""
    if request.method == "POST":
        try:
            cr_id = request.POST.get('cr_id')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id, is_deleted=False).first()
            
            if not change_request:
                logger.warning(f"Delete attempt on non-existent change request: {cr_id} by {request.user.username}")
                messages.error(request, ERROR_MESSAGES['CHANGE_REQUEST_NOT_FOUND'])
                return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])
            
            # Check permissions
            has_permission, permission_message = check_change_request_permissions(request.user, change_request)
            if not has_permission:
                logger.warning(LOG_MESSAGES['PERMISSION_DENIED'].format(
                    username=request.user.username, cr_id=cr_id
                ))
                messages.error(request, permission_message)
                return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])
            
            # Check if already approved
            section_head_approval = CRApproval.objects.filter(
                cr_id=change_request, 
                approver_role__role="section_head"
            ).first()
            
            if section_head_approval:
                logger.warning(f"Delete attempt on approved change request: {cr_id} by {request.user.username}")
                messages.warning(request, WARNING_MESSAGES['ALREADY_APPROVED'])
                return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])
            
            change_request.soft_delete(request.user)
            logger.info(LOG_MESSAGES['CHANGE_REQUEST_DELETED'].format(
                cr_id=cr_id, username=request.user.username
            ))
            messages.success(request, SUCCESS_MESSAGES['CHANGE_REQUEST_DELETED'])
            
        except Exception as ex:
            logger.error(f"Error deleting change request {cr_id}: {str(ex)}", exc_info=True)
            messages.error(request, f"Error deleting change request: {str(ex)}")
    
    return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])

@csrf_protect
@login_required
def restore_change_request(request):
    """Restore a soft-deleted change request"""
    if request.method == "POST":
        try:
            cr_id = request.POST.get('cr_id')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id, is_deleted=True).first()
            
            if not change_request:
                logger.warning(f"Restore attempt on non-existent change request: {cr_id} by {request.user.username}")
                messages.error(request, ERROR_MESSAGES['CHANGE_REQUEST_NOT_FOUND'])
                return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])
            
            # Check permissions (only admin or creator can restore)
            if not (request.user.is_superuser or change_request.deleted_by == request.user):
                logger.warning(f"Restore permission denied for user {request.user.username} on change request {cr_id}")
                messages.error(request, ERROR_MESSAGES['CANNOT_RESTORE'])
                return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])
            
            change_request.restore()
            logger.info(LOG_MESSAGES['CHANGE_REQUEST_RESTORED'].format(
                cr_id=cr_id, username=request.user.username
            ))
            messages.success(request, SUCCESS_MESSAGES['CHANGE_REQUEST_RESTORED'])
            
        except Exception as ex:
            logger.error(f"Error restoring change request {cr_id}: {str(ex)}", exc_info=True)
            messages.error(request, f"Error restoring change request: {str(ex)}")
    
    return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])

@csrf_protect
@login_required
def bulk_delete_change_requests(request):
    """Bulk delete change requests"""
    if request.method == "POST":
        try:
            cr_ids = request.POST.getlist('cr_ids[]')
            deleted_count = 0
            
            logger.info(f"Bulk delete initiated by {request.user.username} for {len(cr_ids)} change requests")
            
            for cr_id in cr_ids:
                change_request = ChangeRequest.objects.filter(cr_id=cr_id, is_deleted=False).first()
                if change_request:
                    has_permission, _ = check_change_request_permissions(request.user, change_request)
                    if has_permission:
                        # Check if already approved
                        section_head_approval = CRApproval.objects.filter(
                            cr_id=change_request, 
                            approver_role__role="section_head"
                        ).first()
                        
                        if not section_head_approval:
                            change_request.soft_delete(request.user)
                            deleted_count += 1
                        else:
                            logger.warning(f"Skipped approved change request {cr_id} in bulk delete by {request.user.username}")
                    else:
                        logger.warning(f"Permission denied for change request {cr_id} in bulk delete by {request.user.username}")
                else:
                    logger.warning(f"Change request {cr_id} not found in bulk delete by {request.user.username}")
            
            logger.info(LOG_MESSAGES['BULK_DELETE'].format(
                count=deleted_count, username=request.user.username
            ))
            messages.success(request, SUCCESS_MESSAGES['BULK_DELETE_SUCCESS'].format(count=deleted_count))
            
        except Exception as ex:
            logger.error(f"Error in bulk delete by {request.user.username}: {str(ex)}", exc_info=True)
            messages.error(request, f"Error in bulk delete: {str(ex)}")
    
    return redirect(URL_PATTERNS['CHANGE_REQUEST_INDEX'])

@csrf_protect
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
    
@csrf_protect
@login_required
def create_new_profile(request):
    try:
        # Sanitize input data
        sanitized_data = sanitize_input(request.POST.dict())
        
        change_reason = sanitized_data.get('change_reason')
        change_description = sanitized_data.get('change_description')
        profile_username = sanitized_data.get('username')
        first_name = sanitized_data.get('first_name')
        last_name = sanitized_data.get('last_name')
        email = sanitized_data.get('email')
        designation_ = sanitized_data.get('designation')
        cost_center = sanitized_data.get('cost_center')
        application = sanitized_data.get('for_application')
        roles_to_action = sanitized_data.get('roles_to_action')
        
        # Validate input data
        validation_errors = validate_change_request_data({
            'change_reason': change_reason,
            'change_description': change_description
        })
        
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return redirect("/change_requests/create_change_request")
        
        profile_validation_errors = validate_new_profile_data({
            'username': profile_username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        })
        
        if profile_validation_errors:
            for error in profile_validation_errors:
                messages.error(request, error)
            return redirect("/change_requests/create_change_request")

        # Check if username already exists
        if UserProfile.objects.filter(username=profile_username).exists():
            messages.error(request, f"Username '{profile_username}' already exists. Please choose a different username.")
            return redirect("/change_requests/create_change_request")

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
            created_at=timezone.now(),
            roles_to_action=roles_to_action
        )

        user.save()

        cr_id = "CR-" + timezone.now().strftime("%Y%m%d%I%M%S")
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
            created_at=timezone.now()
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

@csrf_protect
@login_required
def profile_modification_request(request):
    import traceback
    
    print("=== PROFILE MODIFICATION REQUEST START ===")
    print(f"User: {request.user.username}, Method: {request.method}")
    
    try:
        change_reason = request.POST.get("change_reason")
        change_description = request.POST.get("change_description")
        delegator_username = request.POST.get("delegator")
        delegatee_username = request.POST.get("delegatee")
        application = request.POST.get("for_application")
        roles_to_action = request.POST.get("roles_to_action")
        change_type = request.POST.get("change_type", "PERMANENT")
        auth_user = request.user
        
        print(f"Form data - delegator: {delegator_username}, delegatee: {delegatee_username}")
        print(f"Form data - application: {application}, change_type: {change_type}")
        print(f"Form data - roles_to_action: {roles_to_action}")
        print("delegator: ", delegator_username, "delegatee: ", delegatee_username)
        
        # Get delegator and delegatee users
        print("Fetching delegator and delegatee users from database")
        delegator = UserProfile.objects.filter(username=delegator_username).first()
        delegatee = UserProfile.objects.filter(username=delegatee_username).first()
        
        print(f"Delegator found: {delegator is not None}")
        print(f"Delegatee found: {delegatee is not None}")
        
        if not delegator:
            error_msg = f"Delegator '{delegator_username}' not found in database"
            print(f"ERROR: {error_msg}")
            messages.error(request, error_msg)
            return redirect("/change_requests/change_request_index")
            
        if not delegatee:
            error_msg = f"Delegatee '{delegatee_username}' not found in database"
            print(f"ERROR: {error_msg}")
            messages.error(request, error_msg)
            return redirect("/change_requests/change_request_index")
        
        print(f"Delegator details: ID={delegator.id}, designation={delegator.designation}")
        print(f"Delegatee details: ID={delegatee.id}, designation={delegatee.designation}")
            
        region, cost_center = None, None
        try:
            region = auth_user.region
            cost_center = auth_user.cost_center
            print(f"Auth user region: {region}, cost_center: {cost_center}")
        except Exception as ex:
            error_msg = f"Error getting region/cost_center for user {auth_user.username}: {str(ex)}"
            print(f"ERROR: {error_msg}")
            print("error: ", ex)
            messages.error(request, error_msg)
            return redirect("/change_requests/change_request_index")
        
        # Handle delegation requests
        if change_type == "TEMPORARY_DELEGATION":
            print("Creating ProfileChange for TEMPORARY_DELEGATION")
            try:
                # Create ProfileChange with delegation metadata
                profile_mod = ProfileChange(
                    user=delegatee,  # The delegatee receives the roles
                    application=application,
                    roles_to_action="TEMPORARY_DELEGATION",
                    change_date=timezone.now(),
                    changed_by=delegator,  # The delegator is the one delegating
                    status=PROFILE_CHANGE_STATUS['PENDING']  # Explicitly set status to PENDING
                )
                print(f"ProfileChange object created, about to save with status: {PROFILE_CHANGE_STATUS['PENDING']}")
                profile_mod.save()
                print(f"ProfileChange saved successfully with ID: {profile_mod.id}")
            except Exception as e:
                error_msg = f"Error creating ProfileChange: {str(e)}"
                print(f"ERROR: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
                return redirect("/change_requests/change_request_index")
            
            # Store delegation details in roles_actions
            try:
                import json
                delegation_data = {
                    'type': 'DELEGATION',
                    'delegator_id': delegator.id,  # Use delegator ID instead of auth_user
                    'start_date': request.POST.get('delegation_start_date'),
                    'end_date': request.POST.get('delegation_end_date'),
                    'reason': request.POST.get('delegation_reason')
                }
                print(f"Delegation data: {delegation_data}")
                profile_mod.roles_actions = json.dumps(delegation_data)
                profile_mod.save()
                print("Delegation metadata saved successfully")
                
                # Add roles to be delegated
                selected_roles = request.POST.getlist('roles')
                print(f"Selected roles for delegation: {selected_roles}")
                if selected_roles:
                    profile_mod.role_to_assign.set(Roles.objects.filter(id__in=selected_roles))
                    print("Roles assigned to ProfileChange successfully")
            except Exception as e:
                error_msg = f"Error storing delegation data: {str(e)}"
                print(f"ERROR: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
                return redirect("/change_requests/change_request_index")
        else:
            print("Creating ProfileChange for regular profile modification")
            try:
                # Handle regular profile modification
                profile_mod = ProfileChange(
                    user=delegatee,  # Use delegatee for regular modifications too
                    change_date=timezone.now(),
                    changed_by=delegator,  # Use delegator as the one making the change
                    roles_to_action=roles_to_action,
                    status=PROFILE_CHANGE_STATUS['PENDING']  # Explicitly set status to PENDING
                )
                print(f"ProfileChange object created, about to save with status: {PROFILE_CHANGE_STATUS['PENDING']}")
                profile_mod.save()
                print(f"ProfileChange saved successfully with ID: {profile_mod.id}")
            except Exception as e:
                error_msg = f"Error creating regular ProfileChange: {str(e)}"
                print(f"ERROR: {error_msg}")
                print(f"Traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
                return redirect("/change_requests/change_request_index")
        
        cr_id = "CR-" + timezone.now().strftime("%Y%m%d%I%M%S")
        print(f"Generated CR ID: {cr_id}")
        
        # Determine change type for the request
        if change_type == "TEMPORARY_DELEGATION":
            change_type_display = "Temporary Role Delegation"
        else:
            change_type_display = "Profile Modification"
        
        print(f"Change type display: {change_type_display}")
        
        # Validate required fields before creating ChangeRequest
        if not delegatee.designation:
            error_msg = f"Delegatee '{delegatee.username}' must have a designation assigned"
            print(f"ERROR: {error_msg}")
            messages.error(request, error_msg)
            return redirect("/change_requests/change_request_index")
        
        if not region:
            error_msg = f"User '{request.user.username}' must have a region assigned to create change requests"
            print(f"ERROR: {error_msg}")
            messages.error(request, error_msg)
            return redirect("/change_requests/change_request_index")
        
        print("Creating ChangeRequest object")
        try:
            change_request = ChangeRequest(
                cr_id=cr_id,
                application=application,
                change_type=change_type_display,
                profile_change=profile_mod,
                change_description=change_description,
                change_reason=change_reason,
                creator_designation=delegatee.designation,
                created_by=request.user,
                region=region,
                cost_center=cost_center,
                status='PENDING',  # Explicitly set the status
                created_at=timezone.now()
            )
            print(f"ChangeRequest object created, about to save")
            change_request.save()
            print(f"ChangeRequest saved successfully with ID: {change_request.cr_id}")
        except Exception as e:
            error_msg = f"Error creating ChangeRequest: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            messages.error(request, error_msg)
            return redirect("/change_requests/change_request_index")
        
        # Send delegation notifications if this is a delegation request
        if change_type == "TEMPORARY_DELEGATION":
            send_delegation_notifications(
                change_request, 
                'DELEGATION_CREATED', 
                f"New delegation request created by {delegator.get_full_name()}"
            )
        
        messages.success(request, "Change request submitted successfully")
        
        try:
            # Get section head approver for this cost center
            application = Application.objects.filter(name="change_requests").first()
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
            error_msg = f"Error sending notification email: {str(ex)}"
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            print("Error: ", str(ex))
            # Don't block the process for email errors, just log and continue

        print("=== PROFILE MODIFICATION REQUEST COMPLETED SUCCESSFULLY ===")
        return redirect("/change_requests/change_request_index")
        
    except Exception as e:
        # Catch-all exception handler for the entire function
        error_msg = f"Unexpected error in profile_modification_request: {str(e)}"
        print(f"CRITICAL ERROR: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect("/change_requests/change_request_index")

def send_delegation_notifications(change_request, notification_type, message):
    """Send notifications for delegation requests"""
    try:
        if change_request.change_type == "Temporary Role Delegation" and change_request.profile_change:
            import json
            delegation_data = json.loads(change_request.profile_change.roles_actions) if change_request.profile_change.roles_actions else {}
            delegator_id = delegation_data.get('delegator_id')
            delegatee = change_request.profile_change.user
            
            if delegator_id:
                delegator = UserProfile.objects.filter(id=delegator_id).first()
                if delegator:
                    # Notify delegator
                    DelegationNotification.objects.create(
                        delegation=None,  # No delegation record yet
                        recipient=delegator,
                        notification_type=notification_type,
                        message=message
                    )
            
            # Notify delegatee
            DelegationNotification.objects.create(
                delegation=None,  # No delegation record yet
                recipient=delegatee,
                notification_type=notification_type,
                message=message
            )
            
            # Notify approvers
            role = change_request.created_by.get_user_role_for_application("change_requests")
            if role and role.role == "section_head":
                # Notify IT section heads
                it_section_heads = UserProfile.objects.filter(
                    roles__role="it_section_head",
                    roles__application="change_requests"
                ).distinct()
                for approver in it_section_heads:
                    DelegationNotification.objects.create(
                        delegation=None,
                        recipient=approver,
                        notification_type=notification_type,
                        message=f"New delegation request requires IT approval: {message}"
                    )
    except Exception as e:
        print(f"Error sending delegation notifications: {e}")

def apply_delegation_change_request(change_request):
    """Apply delegation changes when a delegation change request is approved"""
    if change_request.profile_change.roles_to_action == "TEMPORARY_DELEGATION":
        try:
            # Parse delegation metadata
            import json
            metadata = json.loads(change_request.profile_change.roles_actions)
            
            # Create RoleDelegation record for tracking
            delegation = RoleDelegation.objects.create(
                delegator_id=metadata['delegator_id'],
                delegatee=change_request.profile_change.user,
                start_date=datetime.fromisoformat(metadata['start_date']),
                end_date=datetime.fromisoformat(metadata['end_date']),
                reason=metadata['reason'],
                status='ACTIVE',
                created_by=change_request.created_by
            )
            
            # Add roles to delegation
            delegation.roles.set(change_request.profile_change.role_to_assign.all())
            
            # Add applications to delegation (get from the change request application)
            if change_request.application:
                from it.users.models import Application
                app = Application.objects.filter(name=change_request.application).first()
                if app:
                    delegation.applications.add(app)
            
            # Create notifications
            DelegationNotification.objects.create(
                delegation=delegation,
                recipient=delegation.delegatee,
                notification_type='DELEGATION_ACTIVATED',
                message=f"Role delegation from {delegation.delegator.get_full_name()} is now active"
            )
            
            DelegationNotification.objects.create(
                delegation=delegation,
                recipient=delegation.delegator,
                notification_type='DELEGATION_ACTIVATED',
                message=f"Your role delegation to {delegation.delegatee.get_full_name()} is now active"
            )
            
            return True, "Delegation activated successfully"
        except Exception as e:
            return False, f"Error activating delegation: {str(e)}"
    return False, "Not a delegation request"

@login_required
def get_delegation_roles(request):
    """API endpoint to get roles available for delegation"""
    if request.method == "GET":
        try:
            delegator_id = request.GET.get('delegator_id')
            application_name = request.GET.get('application', 'users')
            
            if not delegator_id:
                return JsonResponse({'error': 'Delegator ID is required'}, status=400)
            
            # Get the delegator
            delegator = UserProfile.objects.filter(id=delegator_id).first()
            if not delegator:
                return JsonResponse({'error': 'Delegator not found'}, status=404)
            
            # Get the application
            application = Application.objects.filter(name=application_name).first()
            if not application:
                return JsonResponse({'error': 'Application not found'}, status=404)
            
            # Get roles that the delegator has for this application
            delegator_roles = delegator.roles.filter(app_id=application.id)
            
            # Format roles for response
            roles_data = []
            for role in delegator_roles:
                roles_data.append({
                    'id': role.id,
                    'name': role.role,
                    'application': application.fullname
                })
            
            return JsonResponse({
                'success': True,
                'roles': roles_data,
                'delegator': {
                    'id': delegator.id,
                    'name': delegator.get_full_name(),
                    'username': delegator.username
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def get_delegator_roles_by_app(request):
    """API endpoint to get all roles grouped by application from selected delegator"""
    if request.method == "GET":
        try:
            delegator_id = request.GET.get('delegator_id')
            
            if not delegator_id:
                return JsonResponse({'error': 'Delegator ID is required'}, status=400)
            
            # Get the delegator by ID (not username)
            try:
                delegator = UserProfile.objects.get(id=delegator_id)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Delegator not found'}, status=404)
            
            # Get all roles that the delegator has
            delegator_roles = delegator.roles.all()
            
            if not delegator_roles.exists():
                return JsonResponse({
                    'success': True,
                    'roles_by_app': {},
                    'delegator': {
                        'id': delegator.id,
                        'name': delegator.get_full_name(),
                        'username': delegator.username
                    },
                    'message': f'{delegator.get_full_name()} has no roles available for delegation'
                })
            
            # Group roles by application
            roles_by_app = {}
            for role in delegator_roles:
                app = role.app_id
                if app:
                    app_key = app.name
                    if app_key not in roles_by_app:
                        roles_by_app[app_key] = {
                            'app_id': app.id,
                            'app_name': app.name,
                            'app_fullname': app.fullname,
                            'roles': []
                        }
                    
                    roles_by_app[app_key]['roles'].append({
                        'id': role.id,
                        'name': role.role,
                        'description': getattr(role, 'description', '') or role.role
                    })
            
            return JsonResponse({
                'success': True,
                'roles_by_app': roles_by_app,
                'delegator': {
                    'id': delegator.id,
                    'name': delegator.get_full_name(),
                    'username': delegator.username
                }
            })
            
        except Exception as e:
            logger.error(f"Error in get_delegator_roles_by_app: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

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
            change_date=timezone.now(),
            changed_by=user,
            status='PENDING'  # Explicitly set status to PENDING
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

@csrf_protect
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
                deactivation_date=timezone.now(),
                deactivated_by=user
            )
            profile_deactivation.save()

            cr_id = "CR-" + timezone.now().strftime("%Y%m%d%I%M%S")
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
                created_at=timezone.now()
            )
            change_request.save()
            
            messages.success(request, "Change request submitted successfully")   
            try:     
                # Get section head approver for this cost center
                application = Application.objects.filter(name="change_requests").first()
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
                    "application": change_request.application,
                    "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                    "creator_designation": change_request.creator_designation.description,
                    "created_at": change_request.created_at,
                    "change_type": change_request.change_type,
                    "overall_status": change_request.overall_status
                }
                
                # Check if current user is the owner
                is_owner = change_request.created_by == request.user
                
                return render(
                    request,
                    "change_requests/new_profile_request.html",
                    {
                        "user_applications": Application.objects.all(),
                        "user_designations": Designations.objects.all(),
                        "sections": Sections.objects.all(),
                        "districts": Districts.objects.all(),
                        "regions": Regions.objects.all(),
                        "cost_centers": CostCenter.objects.all(),
                        "user_title": request.user.get_full_name(),
                        "user_groups": list(request.user.groups.values_list('name', flat=True)),
                        "cr": cr,
                        "change_request": change_request,
                        "is_owner": is_owner
                    }
                )
                
@csrf_protect
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
                    "application": change_request.application,  # FIXED: Added missing application field
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
            # FIXED: Build roles_to_action string from actual assigned roles for delegations
            roles_to_action_display = profile_change.roles_to_action
            if change_request.change_type == "Temporary Role Delegation":
                # Get actual roles from role_to_assign ManyToMany field
                assigned_roles = profile_change.role_to_assign.all()
                print(f"DEBUG: Temporary delegation - assigned_roles count: {assigned_roles.count()}")
                if assigned_roles.exists():
                    # Build a readable string of role names
                    role_names = [role.role for role in assigned_roles]
                    roles_to_action_display = ", ".join(role_names)
                    print(f"DEBUG: Built roles display string: {roles_to_action_display}")
                else:
                    # Fallback to stored value if no roles assigned yet
                    roles_to_action_display = profile_change.roles_to_action or ""
                    print(f"DEBUG: No assigned roles, using fallback: {roles_to_action_display}")
            elif profile_change.roles_to_action:
                roles_to_action_display = profile_change.roles_to_action
            
            print(f"DEBUG: Final roles_to_action_display value: '{roles_to_action_display}'")
            
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
                "roles_to_action": roles_to_action_display,  # FIXED: Now shows actual roles for delegations
                "roles_actions": profile_change.roles_actions,
            }
            
            # FIXED: Get delegation data from the correct fields
            # The delegator is stored in profile_change.changed_by
            # The delegatee is stored in profile_change.user
            is_delegation = change_request.change_type == "Temporary Role Delegation"
            
            # Get delegator from changed_by field (who initiated the delegation)
            delegator_username = profile_change.changed_by.username if profile_change.changed_by else None
            delegator_obj = profile_change.changed_by  # Keep reference to delegator object
            # Delegatee is the user being modified
            delegatee_username = user.username
            
            # Get assigned roles for the edit form (for role selection)
            assigned_role_ids = list(profile_change.role_to_assign.values_list('id', flat=True))
            
            print(f"DEBUG: Delegator: {delegator_username}, Delegatee: {delegatee_username}")
            print(f"DEBUG: Assigned role IDs: {assigned_role_ids}")

            # ADDED: Extract delegation dates and reason from JSON
            delegation_start_date = ""
            delegation_end_date = ""
            delegation_reason = ""
            
            if is_delegation and profile_change.roles_actions:
                try:
                    import json
                    data = json.loads(profile_change.roles_actions)
                    
                    # Extract dates in format suitable for datetime-local input (YYYY-MM-DDTHH:MM)
                    start_date_raw = data.get('start_date', '')
                    end_date_raw = data.get('end_date', '')
                    
                    if start_date_raw:
                        # Convert to datetime-local format if needed
                        # Expected format: "2025-11-06T13:24" (already in datetime-local format)
                        delegation_start_date = start_date_raw
                    
                    if end_date_raw:
                        delegation_end_date = end_date_raw
                    
                    delegation_reason = data.get('reason', '')
                    
                    print(f"DEBUG: Extracted delegation dates - Start: {delegation_start_date}, End: {delegation_end_date}")
                except (json.JSONDecodeError, Exception) as e:
                    print(f"DEBUG: Error parsing delegation dates: {e}")

            cr = {
                "user": new_user,
                "cr_id": change_request.cr_id,
                "change_reason": change_request.change_reason,
                "change_description": change_request.change_description,
                "application": change_request.application,
                "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                "creator_designation": change_request.creator_designation.description,
                "created_at": change_request.created_at,
                "change_type": change_request.change_type,
                "overall_status": change_request.overall_status,
                # FIXED: Added delegation-specific fields with correct data source
                "is_delegation": is_delegation,
                "delegation_type": "TEMPORARY" if is_delegation else "PERMANENT",
                "delegator_username": delegator_username,
                "delegator_id": delegator_obj.id if delegator_obj else None,  # ADDED: Delegator ID for AJAX
                "delegatee_username": delegatee_username,
                "assigned_role_ids": assigned_role_ids,  # For pre-selecting roles in edit form
                # ADDED: Delegation date and reason fields
                "delegation_start_date": delegation_start_date,
                "delegation_end_date": delegation_end_date,
                "delegation_reason": delegation_reason,
            }
            
            # Check if current user is the owner
            is_owner = change_request.created_by == request.user
            
            # Get delegator's available roles (for role selection in delegation edits)
            delegator_roles = []
            if is_delegation and profile_change.changed_by:
                # Get the delegator's roles for the application
                delegator_obj = profile_change.changed_by
                if change_request.application:
                    app = Application.objects.filter(name=change_request.application).first()
                    if app:
                        # Get all roles the delegator has for this application
                        delegator_roles = delegator_obj.roles.filter(app_id=app.id).all()
                        print(f"DEBUG: Delegator {delegator_obj.username} has {delegator_roles.count()} roles for {change_request.application}")
            
            # Get all roles for the application (fallback for regular modifications)
            all_roles = []
            if change_request.application:
                app = Application.objects.filter(name=change_request.application).first()
                if app:
                    all_roles = Roles.objects.filter(app_id=app.id)
            
            return render(
                request,
                "change_requests/update_profile_modification.html",
                {
                    "user_applications": Application.objects.all(),
                    "user_designations": Designations.objects.all(),
                    "sections": Sections.objects.all(),
                    "districts": Districts.objects.all(),
                    "regions": Regions.objects.all(),
                    "cost_centers": CostCenter.objects.all(),
                    "user_profiles": UserProfile.objects.filter(is_active=True),
                    "user_title": request.user.get_full_name(),
                    "user_groups": list(request.user.groups.values_list('name', flat=True)),
                    "cr": cr,
                    "change_request": change_request,
                    "is_owner": is_owner,
                    "all_roles": all_roles,  # All roles for the application
                    "delegator_roles": delegator_roles,  # ADDED: Delegator's available roles
                    "assigned_roles": profile_change.role_to_assign.all(),  # Currently assigned roles
                }
            )
        
        elif change_request.profile_deactivation:
            profile_deactivation = change_request.profile_deactivation
            user = profile_deactivation.user
            cr = {
                "cr_id": change_request.cr_id,
                "change_reason": change_request.change_reason,
                "change_description": change_request.change_description,
                "application": change_request.application,
                "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
                "creator_designation": change_request.creator_designation.description,
                "created_at": change_request.created_at,
                "change_type": change_request.change_type,
                "overall_status": change_request.overall_status,
                "user": user
            }
            
            # Check if current user is the owner
            is_owner = change_request.created_by == request.user
            
            return render(
                request,
                "change_requests/update_profile_deactivation.html",
                {
                    "user_applications": Application.objects.all(),
                    "user_designations": Designations.objects.all(),
                    "sections": Sections.objects.all(),
                    "districts": Districts.objects.all(),
                    "regions": Regions.objects.all(),
                    "cost_centers": CostCenter.objects.all(),
                    "user_profiles": UserProfile.objects.filter(is_active=True),
                    "user_title": request.user.get_full_name(),
                    "user_groups": list(request.user.groups.values_list('name', flat=True)),
                    "cr": cr,
                    "change_request": change_request,
                    "is_owner": is_owner
                }
            )
            
    elif request.method == "POST":
        try:
            # Sanitize input data
            sanitized_data = sanitize_input(request.POST.dict())
            
            cr_id = sanitized_data.get('cr_id')
            change_reason = sanitized_data.get('change_reason')
            change_description = sanitized_data.get('change_description')
            roles_to_action = sanitized_data.get('roles_to_action')
            roles_actions = sanitized_data.get('roles_actions')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            
            # Check permissions
            has_permission, permission_message = check_change_request_permissions(request.user, change_request)
            if not has_permission:
                messages.error(request, permission_message)
                return redirect("/change_requests/change_request_index")
            
            section_head_approval = CRApproval.objects.filter(cr_id=change_request, approver_role__role="section_head").first()
            if not change_request:
                messages.error(request, "Change request not found")
                return redirect("/change_requests/change_request_index")
            elif section_head_approval:
                messages.warning(request, "Change request has already been approved by the section head. You cannot update it")
                return redirect("/change_requests/change_request_index")
            else:
                # Update the ChangeRequest common fields
                change_request.change_reason = change_reason if change_reason else change_request.change_reason
                change_request.change_description = change_description if change_description else change_request.change_description
                change_request.application = sanitized_data.get('application', change_request.application)
                change_request.save()

                # Update type-specific fields
                if change_request.new_profile:
                    # Update NewProfile fields
                    new_profile = change_request.new_profile
                    new_profile.roles_to_action = roles_to_action if roles_to_action else new_profile.roles_to_action
                    new_profile.roles_actions = roles_actions if roles_actions else new_profile.roles_actions
                    
                    # Update other new profile fields if provided
                    new_profile.first_name = sanitized_data.get('first_name', new_profile.first_name)
                    new_profile.last_name = sanitized_data.get('last_name', new_profile.last_name)
                    new_profile.username = sanitized_data.get('username', new_profile.username)
                    new_profile.email = sanitized_data.get('email', new_profile.email)
                    
                    # Update designation if provided
                    designation_id = sanitized_data.get('designation')
                    if designation_id:
                        new_profile.designation = Designations.objects.filter(id=designation_id).first()
                    
                    new_profile.save()
                
                elif change_request.profile_change:
                    # Update ProfileChange fields
                    profile_mod = change_request.profile_change
                    profile_mod.roles_to_action = roles_to_action if roles_to_action else profile_mod.roles_to_action
                    profile_mod.roles_actions = roles_actions if roles_actions else profile_mod.roles_actions
                    profile_mod.application = sanitized_data.get('application', profile_mod.application)
                    
                    # FIXED: Update delegated roles if this is a temporary delegation
                    if change_request.change_type == "Temporary Role Delegation":
                        selected_role_ids = request.POST.getlist('roles')
                        print(f"DEBUG: Updating delegation with selected roles: {selected_role_ids}")
                        if selected_role_ids:
                            # Update the role_to_assign ManyToMany field
                            profile_mod.role_to_assign.set(Roles.objects.filter(id__in=selected_role_ids))
                            print(f"DEBUG: Updated role_to_assign with {len(selected_role_ids)} roles")
                        else:
                            # Clear roles if none selected
                            profile_mod.role_to_assign.clear()
                            print("DEBUG: Cleared all role assignments")
                        
                        # ADDED: Update delegation dates and reason
                        delegation_start_date = sanitized_data.get('delegation_start_date')
                        delegation_end_date = sanitized_data.get('delegation_end_date')
                        delegation_reason = sanitized_data.get('delegation_reason')
                        
                        if delegation_start_date and delegation_end_date:
                            import json
                            # Get existing data or create new
                            delegation_data = {}
                            if profile_mod.roles_actions:
                                try:
                                    delegation_data = json.loads(profile_mod.roles_actions)
                                except json.JSONDecodeError:
                                    delegation_data = {}
                            
                            # Update the delegation metadata
                            delegation_data['type'] = 'DELEGATION'
                            delegation_data['start_date'] = delegation_start_date
                            delegation_data['end_date'] = delegation_end_date
                            delegation_data['reason'] = delegation_reason if delegation_reason else delegation_data.get('reason', '')
                            
                            # Keep delegator_id if it exists
                            if 'delegator_id' not in delegation_data and profile_mod.changed_by:
                                delegation_data['delegator_id'] = profile_mod.changed_by.id
                            
                            # Save back to roles_actions as JSON
                            profile_mod.roles_actions = json.dumps(delegation_data)
                            print(f"DEBUG: Updated delegation dates - Start: {delegation_start_date}, End: {delegation_end_date}")
                    
                    profile_mod.save()
                    
                elif change_request.profile_deactivation:
                    # Update ProfileDeactivation fields
                    profile_deactivation = change_request.profile_deactivation
                    profile_deactivation.application = sanitized_data.get('application', profile_deactivation.application)
                    profile_deactivation.save()
                # clear approvals
                CRApproval.objects.filter(cr_id=change_request).delete()
                messages.success(request, "Change Request updated successfully")
        except Exception as ex:
            traceback.print_exc()
            print("save user error", ex)
            messages.error(request, "An error occurred while saving the change request")
    
        return redirect("/change_requests/change_request_index")

# Helper functions for view_profile_request refactoring

def get_user_permissions(user, change_request):
    """
    Determine user permissions for the change request
    Returns: dict with permission flags
    
    FIXED: Now checks ALL user roles, not just the first one
    """
    # Get ALL roles for this application
    application = Application.objects.filter(name="change_requests").first()
    user_roles = user.roles.filter(app_id=application.id) if application else []
    
    # Extract role names
    role_names = [role.role for role in user_roles]
    logger.info(f"User {user.username} has roles: {role_names}")
    
    # Determine primary role for template (prioritize IT section head for display)
    if "it_section_head" in role_names:
        primary_role = "it_section_head"
    elif "section_head" in role_names:
        primary_role = "section_head"
    else:
        primary_role = role_names[0] if role_names else None
    
    permissions = {
        'section_head_allowed': False,
        'it_section_head_allowed': False,
        'user_role': primary_role,  # Primary role for template
        'all_roles': role_names,     # All roles for checking
        'cost_centers': []
    }
    
    # Check permissions for each role the user has
    for role_obj in user_roles:
        user_responsibilities = Responsibilities.objects.filter(user=user, role=role_obj).first()
        
        if user_responsibilities:
            cost_centers = user_responsibilities.cost_centers.all()
            permissions['cost_centers'].extend(cost_centers)
            
            # Check section head permission
            if role_obj.role == "section_head":
                if change_request.cost_center in cost_centers:
                    permissions['section_head_allowed'] = True
            
            # Check IT section head permission
            elif role_obj.role == "it_section_head":
                if change_request.cost_center in cost_centers:
                    permissions['it_section_head_allowed'] = True
    
    logger.info(f"Permissions: section_head_allowed={permissions['section_head_allowed']}, it_section_head_allowed={permissions['it_section_head_allowed']}")
    
    return permissions

def get_approval_workflow_status(change_request):
    """
    Get approval status and determine what actions are awaiting
    Returns: dict with approval status flags
    """
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
    
    return {
        'cr_approvals': cr_approvals,
        'section_head_awaiting_action': section_head_awaiting_action,
        'it_section_head_awaiting_action': it_section_head_awaiting_action
    }

def build_new_profile_context(new_profile):
    """
    Build standardized user context for new profile requests
    """
    return {
        "id": new_profile.pk,
        "username": new_profile.username,
        "first_name": new_profile.first_name,  # With underscore (standard Django naming)
        "last_name": new_profile.last_name,    # With underscore (standard Django naming)
        "firstname": new_profile.first_name,   # Without underscore (legacy compatibility)
        "lastname": new_profile.last_name,     # Without underscore (legacy compatibility)
        "email": new_profile.email,
        "roles_to_action": new_profile.roles_to_action,
        "roles_actions": new_profile.roles_actions,
        "section": new_profile.section,
        "district": new_profile.district,
        "region": new_profile.region,
        "cost_center": new_profile.cost_center,
        "designation": new_profile.designation,
    }

def build_profile_change_context(user, profile_change):
    """
    Build standardized user context for profile change requests
    """
    try:
        cost_center = user.cost_center
    except Exception as ex:
        logger.error(f"Error getting cost center for user {user.username}: {ex}")
        cost_center = None
        
    return {
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

def parse_delegation_data(profile_change):
    """
    Parse delegation data from roles_actions JSON field and format for display
    """
    import json
    from datetime import datetime
    
    delegation_info = {
        'is_delegation': False,
        'is_deactivation': False,
        'display_type': 'modification',  # modification, delegation, deactivation
        'formatted_display': '',
        'delegator_name': '',
        'start_date': '',
        'end_date': '',
        'reason': '',
        'roles': [],
        'roles_text': ''  # For text-based roles (non-Business Excellence)
    }
    
    # Check if this is a delegation request
    if profile_change.roles_to_action == "TEMPORARY_DELEGATION":
        delegation_info['is_delegation'] = True
        delegation_info['display_type'] = 'delegation'
        
        # Parse roles_actions JSON data
        try:
            if profile_change.roles_actions:
                data = json.loads(profile_change.roles_actions)
                
                # Get delegator information
                delegator_id = data.get('delegator_id')
                if delegator_id:
                    try:
                        delegator = UserProfile.objects.get(id=delegator_id)
                        delegation_info['delegator_name'] = f"{delegator.first_name} {delegator.last_name}"
                    except UserProfile.DoesNotExist:
                        delegation_info['delegator_name'] = f"User ID: {delegator_id}"
                
                # Get and format delegation dates
                start_date_raw = data.get('start_date', '')
                end_date_raw = data.get('end_date', '')
                
                # Format dates for better display
                if start_date_raw:
                    try:
                        # Parse datetime and format for display
                        start_dt = datetime.fromisoformat(start_date_raw.replace('T', ' '))
                        delegation_info['start_date'] = start_dt.strftime('%B %d, %Y at %I:%M %p')
                    except:
                        delegation_info['start_date'] = start_date_raw
                
                if end_date_raw:
                    try:
                        # Parse datetime and format for display
                        end_dt = datetime.fromisoformat(end_date_raw.replace('T', ' '))
                        delegation_info['end_date'] = end_dt.strftime('%B %d, %Y at %I:%M %p')
                    except:
                        delegation_info['end_date'] = end_date_raw
                
                delegation_info['reason'] = data.get('reason', '')
                
                # Get roles to be delegated
                delegation_info['roles'] = list(profile_change.role_to_assign.all())
                
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing delegation data: {e}")
            delegation_info['formatted_display'] = f"Temporary Role Delegation (Error parsing details: {str(e)})"
    
    elif profile_change.roles_to_action and "deactivat" in profile_change.roles_to_action.lower():
        # Handle deactivation requests
        delegation_info['is_deactivation'] = True
        delegation_info['display_type'] = 'deactivation'
        delegation_info['formatted_display'] = 'Profile Deactivation'
    
    else:
        # Handle regular profile modifications
        delegation_info['display_type'] = 'modification'
        delegation_info['formatted_display'] = profile_change.roles_to_action or 'Profile Modification'
        
        # Get delegator information for regular modifications
        if profile_change.changed_by:
            delegation_info['delegator_name'] = profile_change.changed_by.get_full_name()
            delegation_info['delegator_username'] = profile_change.changed_by.username
        else:
            delegation_info['delegator_name'] = 'Unknown'
            delegation_info['delegator_username'] = ''
        
        # Get roles for non-delegation modifications
        delegation_info['roles'] = list(profile_change.role_to_assign.all())
        
        # Check if there's text-based roles data
        if profile_change.roles_actions:
            try:
                # Try to parse as JSON first
                data = json.loads(profile_change.roles_actions)
                if isinstance(data, dict) and data.get('type') != 'DELEGATION':
                    # This might be text roles or other data
                    delegation_info['roles_text'] = data.get('text_roles', '')
            except json.JSONDecodeError:
                # Not JSON, treat as plain text roles
                delegation_info['roles_text'] = profile_change.roles_actions
    
    return delegation_info

def get_change_request_context(change_request, profile_change=None):
    """
    Get context specific to different types of change requests
    """
    context = {
        'change_type': change_request.change_type,
        'is_new_profile': change_request.new_profile is not None,
        'is_profile_change': change_request.profile_change is not None,
        'is_profile_deactivation': change_request.profile_deactivation is not None,
        'application': change_request.application,
        'is_business_excellence': change_request.application == 'BUSINESS EXCELLENCE',
    }
    
    # Add specific context based on type
    if profile_change:
        delegation_info = parse_delegation_data(profile_change)
        context.update({
            'delegation_info': delegation_info,
            'display_type': delegation_info['display_type'],
            'requires_roles': delegation_info['display_type'] != 'deactivation',
            'roles_label': get_roles_label(delegation_info['display_type'], context['is_business_excellence']),
            'implementation_label': get_implementation_label(delegation_info['display_type'])
        })
    
    return context

def get_roles_label(display_type, is_business_excellence):
    """
    Get appropriate label for roles section based on request type and application
    """
    if display_type == 'delegation':
        return 'Roles to Delegate'
    elif display_type == 'deactivation':
        return None  # No roles needed for deactivation
    elif is_business_excellence:
        return 'Roles to Assign'
    else:
        return 'Roles to Designate'

def get_implementation_label(display_type):
    """
    Get appropriate label for implementation section based on request type
    """
    if display_type == 'delegation':
        return 'Delegation Status'
    elif display_type == 'deactivation':
        return 'Deactivation Status'
    else:
        return 'Implementation Status'

def get_base_template_context(request, change_request):
    """
    Get common context data for all profile request views
    """
    requestor = UserProfile.objects.filter(username=request.user.username).first()
    requestor_role = requestor.get_user_roles_for_application("change_requests") if requestor else None
    
    return {
        "user_applications": Application.objects.all(),
        "user_designations": Designations.objects.all(),
        "sections": Sections.objects.all(),
        "districts": Districts.objects.all(),
        "regions": Regions.objects.all(),
        "user_title": request.user.get_full_name(),
        "user_groups": list(request.user.groups.values_list('name', flat=True)),
        "requestor_role": requestor_role,
        "modal_auto_show": False,
        "change_request": change_request
    }

def get_optimized_change_request(cr_id):
    """
    Get change request with optimized database queries
    """
    return ChangeRequest.objects.select_related(
        'new_profile__section',
        'new_profile__district', 
        'new_profile__region',
        'new_profile__cost_center',
        'new_profile__designation',
        'profile_change__user__section',
        'profile_change__user__district',
        'profile_change__user__region',
        'profile_change__user__cost_center',
        'profile_change__user__designation',
        'profile_deactivation__user',
        'created_by',
        'creator_designation'
    ).prefetch_related(
        'crapproval_set__approver_role'
    ).get(cr_id=cr_id)

@login_required
def view_new_profile_request(request, change_request, permissions, approval_status):
    """Handle viewing of new profile requests"""
    new_profile = change_request.new_profile
    
    # Build user context
    new_user = build_new_profile_context(new_profile)
    
    # Build change request context
    cr = {
        "user": new_user,
        "cr_id": change_request.cr_id,
        "change_type": change_request.change_type,  # ADDED: Missing change_type field
        "change_reason": change_request.change_reason,
        "change_description": change_request.change_description,
        "application": change_request.application,
        "created_by": change_request.created_by.get_full_name(),
        "creator_designation": change_request.creator_designation.description if change_request.creator_designation else "",
        "created_at": change_request.created_at
    }
    
    # Get base template context
    context = get_base_template_context(request, change_request)
    
    # Add specific context for new profile request
    context.update({
        "section_head_allowed": permissions['section_head_allowed'],
        "it_section_head_allowed": permissions['it_section_head_allowed'],
        "section_head_awaiting_action": approval_status['section_head_awaiting_action'],
        "it_section_head_awaiting_action": approval_status['it_section_head_awaiting_action'],
        "cr_approvals": approval_status['cr_approvals'],
        "cr": cr,
    })
    
    # FIXED: Use unified template instead of deleted template
    return render(request, "change_requests/view_change_request.html", context)

@login_required
def view_profile_modification_request(request, change_request, permissions, approval_status):
    """Handle viewing of profile modification requests"""
    profile_change = change_request.profile_change
    user = profile_change.user
    
    # Build user context
    new_user = build_profile_change_context(user, profile_change)
    
    # Get change request specific context
    cr_context = get_change_request_context(change_request, profile_change)
    
    # Parse delegation data for proper display
    delegation_info = parse_delegation_data(profile_change)
    
    # FIXED: For temporary delegations, build roles display from actual assigned roles
    roles_to_action_display = delegation_info['formatted_display']
    if change_request.change_type == "Temporary Role Delegation":
        # Get actual roles from role_to_assign ManyToMany field
        assigned_roles = profile_change.role_to_assign.all()
        if assigned_roles.exists():
            # Build a readable string of role names
            role_names = [role.role for role in assigned_roles]
            roles_to_action_display = ", ".join(role_names)
            # Also store role objects for template display
            delegation_info['assigned_roles'] = list(assigned_roles)
            delegation_info['assigned_role_names'] = role_names
        else:
            # Fallback if no roles assigned
            roles_to_action_display = "TEMPORARY_DELEGATION (No roles specified)"
    
    # Get delegator and delegatee info
    delegator_name = ""
    delegatee_name = user.get_full_name() if user else ""
    
    if change_request.change_type == "Temporary Role Delegation" and profile_change.changed_by:
        delegator_name = profile_change.changed_by.get_full_name()
        delegation_info['delegator_name'] = delegator_name
        delegation_info['delegator_username'] = profile_change.changed_by.username
    elif delegation_info.get('delegator_name'):
        delegator_name = delegation_info['delegator_name']
    
    # Build change request context
    cr = {
        "user": new_user,
        "cr_id": change_request.cr_id,
        "change_reason": change_request.change_reason,
        "change_description": change_request.change_description,
        "application": change_request.application,
        "change_type": change_request.change_type,
        "roles_to_action": roles_to_action_display,  # FIXED: Now shows actual roles for delegations
        "roles_actions": profile_change.roles_actions,
        "delegation_info": delegation_info,
        "cr_context": cr_context,
        "created_by": change_request.created_by.get_full_name(),
        "creator_designation": change_request.creator_designation.description if change_request.creator_designation else "",
        "created_at": change_request.created_at,
        "is_delegation": change_request.change_type == "Temporary Role Delegation",  # ADDED: Flag for template
    }
    
    # Get base template context
    context = get_base_template_context(request, change_request)
    
    # Add debugging logs for troubleshooting
    logger.info(f"Change Request Application: {change_request.application}")
    logger.info(f"Profile Change roles_to_action: {profile_change.roles_to_action}")
    logger.info(f"Profile Change roles_actions: {profile_change.roles_actions}")
    logger.info(f"Change request ID: {change_request.cr_id}")
    
    # Add specific context for profile modification request
    context.update({
        "section_head_allowed": permissions['section_head_allowed'],
        "it_section_head_allowed": permissions['it_section_head_allowed'],
        "section_head_awaiting_action": approval_status['section_head_awaiting_action'],
        "it_section_head_awaiting_action": approval_status['it_section_head_awaiting_action'],
        "cr_approvals": approval_status['cr_approvals'],
        "cr": cr,
        # Add the application directly to context for the template
        "selected_application": change_request.application,
    })
    
    logger.info(f"Profile modification request - section_head_awaiting_action: {approval_status['section_head_awaiting_action']}")
    logger.info(f"Profile modification request - it_section_head_awaiting_action: {approval_status['it_section_head_awaiting_action']}")
    
    # DEBUG LOG: Button visibility conditions
    logger.info(f"=== BUTTON VISIBILITY DEBUG for CR {change_request.cr_id} ===")
    logger.info(f"User: {request.user.username}")
    logger.info(f"requestor_role: {permissions.get('user_role', 'N/A')}")
    logger.info(f"section_head_allowed: {permissions['section_head_allowed']}")
    logger.info(f"it_section_head_allowed: {permissions['it_section_head_allowed']}")
    logger.info(f"Apply button condition check:")
    logger.info(f"  - requestor_role == 'it_section_head': {permissions.get('user_role') == 'it_section_head'}")
    logger.info(f"  - it_section_head_awaiting_action: {approval_status['it_section_head_awaiting_action']}")
    logger.info(f"  - section_head_awaiting_action == False: {not approval_status['section_head_awaiting_action']}")
    logger.info(f"  - it_section_head_allowed: {permissions['it_section_head_allowed']}")
    logger.info(f"  => APPLY BUTTON SHOULD SHOW: {permissions.get('user_role') == 'it_section_head' and approval_status['it_section_head_awaiting_action'] and not approval_status['section_head_awaiting_action'] and permissions['it_section_head_allowed']}")
    
    # FIXED: Use unified template instead of deleted template
    return render(request, "change_requests/view_change_request.html", context)

@login_required
def view_profile_deactivation_request(request, change_request, permissions, approval_status):
    """Handle viewing of profile deactivation requests"""
    profile_deactivation = change_request.profile_deactivation
    user = profile_deactivation.user
    
    # Get change request specific context
    cr_context = get_change_request_context(change_request)
    cr_context['display_type'] = 'deactivation'
    cr_context['requires_roles'] = False
    cr_context['implementation_label'] = 'Deactivation Status'
    
    # Build change request context
    cr = {
        "cr_id": change_request.cr_id,
        "change_type": change_request.change_type,  # ADDED: Missing change_type field
        "change_reason": change_request.change_reason,
        "change_description": change_request.change_description,
        "application": change_request.application,  # ADDED: Missing application field
        "created_by": change_request.created_by.get_full_name(),
        "creator_designation": change_request.creator_designation.description if change_request.creator_designation else "",
        "created_at": change_request.created_at,
        "user": user,
        "cr_context": cr_context
    }
    
    # Get base template context
    context = get_base_template_context(request, change_request)
    
    # Add specific context for profile deactivation request
    context.update({
        "section_head_allowed": permissions['section_head_allowed'],
        "it_section_head_allowed": permissions['it_section_head_allowed'],
        "section_head_awaiting_action": approval_status['section_head_awaiting_action'],
        "it_section_head_awaiting_action": approval_status['it_section_head_awaiting_action'],
        "cr_approvals": approval_status['cr_approvals'],
        "cr": cr,
    })
    
    # FIXED: Use unified template instead of deleted template
    return render(request, "change_requests/view_change_request.html", context)

@login_required
def view_profile_request(request):
    """
    Refactored view for handling profile requests.
    Routes to appropriate sub-view based on request type.
    """
    if request.method != "GET":
        logger.warning(f"Invalid request method {request.method} for view_profile_request")
        messages.error(request, "Invalid request method")
        return redirect("/change_requests/change_request_index")
    
    cr_id = request.GET.get('i')
    if not cr_id:
        logger.error("Missing change request ID parameter")
        messages.error(request, "Change request ID is required")
        return redirect("/change_requests/change_request_index")
    
    try:
        # Get change request with optimized queries
        change_request = get_optimized_change_request(cr_id)
        
        # Get user permissions
        permissions = get_user_permissions(request.user, change_request)
        
        # Get approval workflow status
        approval_status = get_approval_workflow_status(change_request)
        
        # Route to appropriate handler based on request type
        if change_request.new_profile:
            return view_new_profile_request(request, change_request, permissions, approval_status)
        elif change_request.profile_change:
            return view_profile_modification_request(request, change_request, permissions, approval_status)
        elif change_request.profile_deactivation:
            return view_profile_deactivation_request(request, change_request, permissions, approval_status)
        else:
            logger.error(f"Unknown change request type for CR: {cr_id}")
            messages.error(request, "Unknown change request type")
            return redirect("/change_requests/change_request_index")
    
    except ChangeRequest.DoesNotExist:
        logger.error(f"Change request not found: {cr_id}")
        messages.error(request, "Change request not found")
        return redirect("/change_requests/change_request_index")
    except Exception as e:
        logger.error(f"Error viewing change request {cr_id}: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while viewing the change request")
        return redirect("/change_requests/change_request_index")


# ==================== NEW UNIFIED VIEW FUNCTIONS (USING SERVICE LAYER) ====================

@login_required
def view_change_request_unified(request):
    """
    REFACTORED: Unified view for all change request types using service layer.
    This replaces view_new_profile_request, view_profile_modification_request, 
    and view_profile_deactivation_request with a single function.
    """
    if request.method != "GET":
        logger.warning(f"Invalid request method {request.method} for view_change_request_unified")
        messages.error(request, "Invalid request method")
        return redirect("/change_requests/change_request_index")
    
    cr_id = request.GET.get('i')
    if not cr_id:
        logger.error("Missing change request ID parameter")
        messages.error(request, "Change request ID is required")
        return redirect("/change_requests/change_request_index")
    
    try:
        # Get change request with optimized queries
        cr = ChangeRequestService.get_cr_with_details(cr_id)
        
        # Get type handler for this CR
        handler = CRTypeHandler.get_handler(cr.change_type)
        
        # Get user permissions
        permissions = ApprovalService.get_user_permissions(request.user, cr)
        
        # Get approval workflow status
        approval_status = ApprovalService.get_approval_status(cr)
        
        # Build profile data using handler
        profile_data = handler.get_profile_data(cr)
        
        # Build base context
        base_context = ContextBuilder.get_base_template_context(request.user, cr)
        
        # Build CR context
        cr_context = ContextBuilder.build_cr_context(cr, profile_data)
        
        # Add type-specific context for profile modification
        if isinstance(handler, ProfileModificationHandler):
            delegation_info = handler.get_delegation_info(cr)
            cr_context['delegation_info'] = delegation_info
            cr_context['cr_context'] = handler.get_change_request_context(cr)
            # ADDED: Add is_delegation flag for template
            cr_context['is_delegation'] = delegation_info.get('is_delegation', False)
            cr_context['change_type'] = cr.change_type  # Ensure change_type is in context
        elif isinstance(handler, ProfileDeactivationHandler):
            cr_context['cr_context'] = handler.get_change_request_context(cr)
            cr_context['change_type'] = cr.change_type
        
        # For New Profile, ensure change_type is in context
        if isinstance(handler, NewProfileHandler):
            cr_context['change_type'] = cr.change_type
        
        # Add approval context
        context = ContextBuilder.add_approval_context(base_context, permissions, approval_status)
        
        # Add CR context
        context['cr'] = cr_context
        
        logger.info(f"Rendering unified view for CR {cr_id} of type {cr.change_type}")
        return render(request, "change_requests/view_change_request.html", context)
    
    except ChangeRequest.DoesNotExist:
        logger.error(f"Change request not found: {cr_id}")
        messages.error(request, "Change request not found")
        return redirect("/change_requests/change_request_index")
    except Exception as e:
        logger.error(f"Error viewing change request {cr_id}: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while viewing the change request")
        return redirect("/change_requests/change_request_index")


@csrf_protect
@login_required
@transaction.atomic
def approve_change_request_unified(request):
    """
    REFACTORED: Unified approval handler using service layer.
    This replaces the massive if/elif blocks in approve_profile_request with clean service calls.
    """
    if request.method != "POST":
        messages.error(request, "Invalid request method")
        return redirect("/change_requests/change_request_index")
    
    try:
        cr_id = request.POST.get('cr_id')
        action = request.POST.get('actionButton')
        
        if not cr_id or not action:
            messages.error(request, "Missing required parameters")
            return redirect("/change_requests/change_request_index")
        
        # Get change request
        cr = ChangeRequestService.get_cr_with_details(cr_id)
        
        # Process action using service layer
        if 'APPROVE' in action:
            success, message = ApprovalService.approve_cr(cr, request.user)
            if success:
                messages.success(request, message)
                # Send notification to next approver
                NotificationService.send_approval_notification(cr, action, request)
            else:
                messages.error(request, message)
        
        elif 'REJECT' in action:
            reason = request.POST.get('rejectReason')
            if not reason:
                messages.error(request, "Rejection reason is required")
                return redirect("/change_requests/change_request_index")
            
            success, message = ApprovalService.reject_cr(cr, request.user, reason)
            if success:
                messages.success(request, message)
                # Send notification to creator
                NotificationService.send_approval_notification(cr, action, request)
            else:
                messages.error(request, message)
        
        elif 'APPLY' in action:
            roles_actions = request.POST.get('roles_actions')
            success, message = ApprovalService.apply_cr(cr, request.user, roles_actions)
            if success:
                messages.success(request, message)
                # Send notification to creator
                NotificationService.send_approval_notification(cr, action, request)
            else:
                messages.error(request, message)
        
        else:
            messages.error(request, f"Unknown action: {action}")
        
        return redirect("/change_requests/change_request_index")
    
    except ChangeRequest.DoesNotExist:
        logger.error(f"Change request not found: {cr_id}")
        messages.error(request, "Change request not found")
        return redirect("/change_requests/change_request_index")
    except Exception as e:
        logger.error(f"Error processing approval action: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred while processing your request: {str(e)}")
        return redirect("/change_requests/change_request_index")


@csrf_protect
@login_required
def create_change_request_handler_unified(request):
    """
    REFACTORED: Unified CR creation handler using service layer.
    This consolidates create_new_profile, profile_modification_request, etc.
    """
    if request.method != "POST":
        messages.error(request, "Invalid request method")
        return redirect("/change_requests/create_change_request")
    
    try:
        # Determine CR type from form data
        request_type = request.POST.get('request_type')
        
        # Validate common fields
        errors = ChangeRequestService.validate_cr_data(request_type, request.POST.dict())
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("/change_requests/create_change_request")
        
        # Create CR based on type
        if request_type == 'NEW_PROFILE' or request.POST.get('username'):
            # Validate new profile specific fields
            profile_errors = ChangeRequestService.validate_new_profile_data(request.POST.dict())
            if profile_errors:
                for error in profile_errors:
                    messages.error(request, error)
                return redirect("/change_requests/create_change_request")
            
            # Check if username already exists
            username = request.POST.get('username')
            if UserProfile.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists. Please choose a different username.")
                return redirect("/change_requests/create_change_request")
            
            cr = ChangeRequestService.create_new_profile_cr(request.POST.dict(), request.user)
        
        elif request_type == 'PROFILE_MODIFICATION' or request.POST.get('delegator'):
            cr = ChangeRequestService.create_profile_modification_cr(request.POST.dict(), request.user)
        
        elif request_type == 'PROFILE_DEACTIVATION':
            cr = ChangeRequestService.create_profile_deactivation_cr(request.POST.dict(), request.user)
        
        else:
            messages.error(request, "Invalid request type")
            return redirect("/change_requests/create_change_request")
        
        # Send notification
        NotificationService.send_creation_notification(cr, request)
        
        messages.success(request, SUCCESS_MESSAGES['CHANGE_REQUEST_CREATED'])
        logger.info(LOG_MESSAGES['CHANGE_REQUEST_CREATED'].format(cr_id=cr.cr_id, username=request.user.username))
        
        return redirect("/change_requests/change_request_index")
    
    except ValueError as ve:
        logger.error(f"Validation error creating change request: {str(ve)}")
        messages.error(request, str(ve))
        return redirect("/change_requests/create_change_request")
    except Exception as e:
        logger.error(f"Error creating change request: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred while creating the change request: {str(e)}")
        return redirect("/change_requests/create_change_request")


# ==================== END NEW UNIFIED VIEW FUNCTIONS ====================

# view_profile_request_legacy removed - replaced with refactored version above

        #         new_user = {
        #             "id": change_request.new_profile.pk,
        #             "username": change_request.new_profile.username,
        #             "firstname": change_request.new_profile.first_name,
        #             "lastname": change_request.new_profile.last_name,
        #             "email": change_request.new_profile.email,
        #             "roles_to_action": change_request.new_profile.roles_to_action,
        #             "roles_actions": change_request.new_profile.roles_actions,
        #             "section": Sections.objects.filter(id=change_request.new_profile.section.id).first() if change_request.new_profile.section else None,
        #             "district": Districts.objects.filter(id=change_request.new_profile.district.id).first() if change_request.new_profile.district else None,
        #             "region": Regions.objects.filter(id=change_request.new_profile.region.id).first() if change_request.new_profile.region else None,
        #             "cost_center": CostCenter.objects.filter(id=change_request.new_profile.cost_center.id).first() if change_request.new_profile.cost_center else None,
        #             "designation": Designations.objects.filter(id=change_request.new_profile.designation.id).first() if change_request.new_profile.designation else None,
        #         }

        #         cr = {
        #             "user": new_user,
        #             "cr_id": change_request.cr_id,
        #             "change_reason": change_request.change_reason,
        #             "change_description": change_request.change_description,
        #             "application": change_request.application,
        #             "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
        #             "creator_designation": change_request.creator_designation.description,
        #             "created_at": change_request.created_at
        #         }
                
        #         # get all approvals
        #         cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
        #         section_head_awaiting_action = True
        #         it_section_head_awaiting_action = True
        #         for approval in cr_approvals:
        #             if approval.approver_role.role == "section_head":
        #                 section_head_awaiting_action = False
        #                 if approval.approval_status == False:
        #                     it_section_head_awaiting_action = False
        #             if approval.approver_role.role == "it_section_head":
        #                 it_section_head_awaiting_action = False
                
        #         requestor = UserProfile.objects.filter(username=request.user.username).first()
        #         requestor_role = requestor.get_user_roles_for_application("change_requests")

        #         return render(
        #             request,
        #             "change_requests/view_profile_request.html",
        #             {
        #                 "section_head_allowed": section_head_allowed,
        #                 "it_section_head_allowed": it_section_head_allowed,
        #                 "requestor_role": requestor_role,
        #                 "section_head_awaiting_action": section_head_awaiting_action,
        #                 "it_section_head_awaiting_action": it_section_head_awaiting_action,
        #                 "user_applications": Application.objects.all(),
        #                 "user_designations": Designations.objects.all(),
        #                 "sections": Sections.objects.all(),
        #                 "districts": Districts.objects.all(),
        #                 "regions": Regions.objects.all(),
        #                 "cr_approvals": cr_approvals,
        #                 "user_title": request.user.get_full_name(),
        #                 "user_groups": list(request.user.groups.values_list('name', flat=True)),
        #                 "cr": cr,
        #                 "modal_auto_show": modal_auto_show
        #             }
        #         )
        
        # elif change_request.profile_change:
        #     profile_change = change_request.profile_change
        #     user = profile_change.user
        #     try:
        #         cost_center = user.cost_center
        #     except Exception as ex:
        #         print("error: ", ex)
        #         cost_center = None

        #     new_user = {
        #         "id": user.pk,
        #         "username": user.username,
        #         "firstname": user.first_name,
        #         "lastname": user.last_name,
        #         "email": user.email,
        #         "section": user.section,
        #         "district": user.district,
        #         "region": user.region,
        #         "cost_center": cost_center,
        #         "designation": user.designation,
        #         "roles_to_action": profile_change.roles_to_action,
        #         "roles_actions": profile_change.roles_actions,
        #     }

        #     cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
        #     section_head_awaiting_action = True
        #     it_section_head_awaiting_action = True
        #     for approval in cr_approvals:
        #         if approval.approver_role.role == "section_head":
        #             section_head_awaiting_action = False
        #             if approval.approval_status == False:
        #                 it_section_head_awaiting_action = False
        #         if approval.approver_role.role == "it_section_head":
        #             it_section_head_awaiting_action = False
            
        #     print("section_head_awaiting_action: ", section_head_awaiting_action)
        #     print("it_section_head_awaiting_action: ", it_section_head_awaiting_action)
        #     requestor = UserProfile.objects.filter(username=request.user.username).first()
        #     requestor_role = requestor.get_user_roles_for_application("change_requests")
        #     cr = {
        #         "user": new_user,
        #         "cr_id": change_request.cr_id,
        #         "change_reason": change_request.change_reason,
        #         "change_description": change_request.change_description,
        #         "application": change_request.application,
        #         "roles_to_action": profile_change.roles_to_action,
        #         "roles_actions": profile_change.roles_actions,
        #         "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
        #         "creator_designation": change_request.creator_designation.description,
        #         "created_at": change_request.created_at
        #     }
        #     return render(
        #         request,
        #         "change_requests/view_profile_modification.html",
        #         {
        #             "section_head_allowed": section_head_allowed,
        #             "it_section_head_allowed": it_section_head_allowed,
        #             "requestor_role": requestor_role,
        #             "section_head_awaiting_action": section_head_awaiting_action,
        #             "it_section_head_awaiting_action": it_section_head_awaiting_action,
        #             "user_applications": Application.objects.all(),
        #             "user_designations": Designations.objects.all(),
        #             "sections": Sections.objects.all(),
        #             "districts": Districts.objects.all(),
        #             "regions": Regions.objects.all(),
        #             "user_title": request.user.get_full_name(),
        #             "user_groups": list(request.user.groups.values_list('name', flat=True)),
        #             "cr": cr,
        #             "cr_approvals": cr_approvals,
        #             "change_request": change_request
        #         }
        #     )

        # elif change_request.profile_deactivation:
        #     profile_deactivation = change_request.profile_deactivation
        #     user = profile_deactivation.user
        #     cr = {
        #         "cr_id": change_request.cr_id,
        #         "change_reason": change_request.change_reason,
        #         "change_description": change_request.change_description,
        #         "created_by": change_request.created_by.first_name + " " + change_request.created_by.last_name,
        #         "creator_designation": change_request.creator_designation.description,
        #         "created_at": change_request.created_at
        #     }
            
        #     cr_approvals = CRApproval.objects.filter(cr_id=change_request).all()
        #     section_head_awaiting_action = True
        #     it_section_head_awaiting_action = True
        #     for approval in cr_approvals:
        #         if approval.approver_role.role == "section_head":
        #             section_head_awaiting_action = False
        #             if approval.approval_status == False:
        #                 it_section_head_awaiting_action = False
        #         if approval.approver_role.role == "it_section_head":
        #             it_section_head_awaiting_action = False
            
        #     requestor = UserProfile.objects.filter(username=request.user.username).first()
        #     requestor_role = requestor.get_user_roles_for_application("change_requests")
        #     return render(
        #         request,
        #         "change_requests/view_profile_deactivation.html",
        #         {
        #             "section_head_allowed": section_head_allowed,
        #             "it_section_head_allowed": it_section_head_allowed,
        #             "user_applications": Application.objects.all(),
        #             "user_designations": Designations.objects.all(),
        #             "sections": Sections.objects.all(),
        #             "districts": Districts.objects.all(),
        #             "regions": Regions.objects.all(),
        #             "user_title": request.user.get_full_name(),
        #             "user_groups": list(request.user.groups.values_list('name', flat=True)),
        #             "requestor_role": requestor_role,
        #             "section_head_awaiting_action": section_head_awaiting_action,
        #             "it_section_head_awaiting_action": it_section_head_awaiting_action,
        #             "cr": cr,
        #             "change_request": change_request,
        #             "cr_approvals": cr_approvals,
        #         }
        #     )
            
@login_required
def get_user_data(request, username):
    """Get user data with caching for better performance"""
    cached_data = get_cached_user_data(username)
    
    if cached_data:
        return JsonResponse(cached_data)
    else:
        return JsonResponse({
            "error": "User not found",
            "applications": [],
            "userData": []
        })

@csrf_protect
@login_required
def update_new_profile_request(request):
    if request.method == "POST":
        try:
            # Sanitize input data
            sanitized_data = sanitize_input(request.POST.dict())
            
            cr_id = sanitized_data.get('cr_id')
            change_reason = sanitized_data.get('change_reason')
            change_description = sanitized_data.get('change_description')
            roles_to_action = sanitized_data.get('roles_to_action')
            roles_actions = sanitized_data.get('roles_actions')
            change_request = ChangeRequest.objects.filter(cr_id=cr_id).first()
            
            # Check permissions
            has_permission, permission_message = check_change_request_permissions(request.user, change_request)
            if not has_permission:
                messages.error(request, permission_message)
                return redirect("/change_requests/change_request_index")
            
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
                change_request.change_description = change_description if change_description else change_request.change_description
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
    
@csrf_protect
@login_required
@transaction.atomic
def approve_profile_request(request):
    """
    LEGACY ENDPOINT - Backward compatibility wrapper for old approval flow.
    New code should use approve_change_request_unified instead.
    
    This function now delegates to the service layer for actual business logic.
    """
    if request.method != "POST":
        return redirect("/change_requests/change_request_index")
    
    try:
        action = request.POST.get('actionButton')
        cr_id = request.POST.get('cr_id')
        
        if not action or not cr_id:
            messages.error(request, "Missing required parameters")
            return redirect("/change_requests/change_request_index")
        
        # Get change request with related data
        cr = ChangeRequestService.get_cr_with_details(cr_id)
        if not cr:
            messages.error(request, "Change request not found")
            return redirect("/change_requests/change_request_index")
        
        # Process action using service layer
        if 'APPROVE' in action:
            success, message = ApprovalService.approve_cr(cr, request.user)
            if success:
                messages.success(request, message)
                # Send notification to next approver
                NotificationService.send_approval_notification(cr, action, request)
            else:
                messages.error(request, message)
        
        elif 'REJECT' in action:
            reason = request.POST.get('rejectReason')
            if not reason:
                messages.error(request, "Rejection reason is required")
                return redirect("/change_requests/change_request_index")
            
            success, message = ApprovalService.reject_cr(cr, request.user, reason)
            if success:
                messages.success(request, message)
                # Send notification to creator
                NotificationService.send_approval_notification(cr, action, request)
            else:
                messages.error(request, message)
        
        elif 'APPLY' in action:
            roles_actions = request.POST.get('roles_actions')
            success, message = ApprovalService.apply_cr(cr, request.user, roles_actions)
            if success:
                messages.success(request, message)
                # Send notification to creator
                NotificationService.send_approval_notification(cr, action, request)
            else:
                messages.error(request, message)
        
        else:
            messages.error(request, f"Unknown action: {action}")
        
        return redirect("/change_requests/change_request_index")
    
    except ChangeRequest.DoesNotExist:
        logger.error(f"Change request not found: {cr_id}")
        messages.error(request, "Change request not found")
        return redirect("/change_requests/change_request_index")
    except Exception as e:
        logger.error(f"Error processing approval action: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
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
def api_cost_centers(request):
    """API endpoint to get cost centers for filter dropdown with server-side search"""
    from it.users.models import CostCenter
    from django.http import JsonResponse
    from django.db.models import Q
    
    # Get search term from request
    search_term = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = 20  # Limit results per page
    
    # Base queryset
    queryset = CostCenter.objects.all()
    
    # Apply search filter if search term provided
    if search_term:
        # Search in name, code, and hierarchy
        search_query = Q()
        search_query |= Q(name__icontains=search_term)
        search_query |= Q(code__icontains=search_term)
        
        # Also search in parent names and codes
        search_query |= Q(parent__name__icontains=search_term)
        search_query |= Q(parent__code__icontains=search_term)
        search_query |= Q(parent__parent__name__icontains=search_term)
        search_query |= Q(parent__parent__code__icontains=search_term)
        
        queryset = queryset.filter(search_query)
    
    # Order by name and apply pagination
    queryset = queryset.order_by('name')
    start = (page - 1) * page_size
    end = start + page_size
    cost_centers = queryset[start:end]
    
    # Enhance the data with detailed hierarchy information
    enhanced_centers = []
    for center in cost_centers:
        center_data = {
            'id': center.id,
            'name': center.name,
            'code': center.code,
            'display_name': f"{center.name} ({center.code})" if center.name and center.code else center.name or center.code,
            'parent_id': center.parent_id
        }
        
        # Build detailed hierarchy with multiple levels
        hierarchy_parts = []
        
        # Get all ancestors
        try:
            ancestors = center.get_all_ancestors()
            
            # Add ancestors in order (grandparent -> parent -> current)
            for ancestor in reversed(ancestors):
                if ancestor.name and ancestor.code:
                    hierarchy_parts.append(f"{ancestor.name} ({ancestor.code})")
                elif ancestor.name:
                    hierarchy_parts.append(ancestor.name)
                elif ancestor.code:
                    hierarchy_parts.append(ancestor.code)
            
            # Add current center
            if center.name and center.code:
                hierarchy_parts.append(f"{center.name} ({center.code})")
            elif center.name:
                hierarchy_parts.append(center.name)
            elif center.code:
                hierarchy_parts.append(center.code)
                
        except Exception:
            # Fallback if hierarchy fails
            if center.name and center.code:
                hierarchy_parts.append(f"{center.name} ({center.code})")
            elif center.name:
                hierarchy_parts.append(center.name)
            elif center.code:
                hierarchy_parts.append(center.code)
        
        # Create hierarchy string
        center_data['hierarchy'] = ' > '.join(hierarchy_parts) if hierarchy_parts else center.name or center.code
        
        # Add additional context information
        center_data['full_context'] = center_data['hierarchy']
        center_data['searchable_text'] = f"{center_data['display_name']} {center_data['hierarchy']}"
        
        enhanced_centers.append(center_data)
    
    # Prepare response with pagination info
    total_count = queryset.count() if search_term else CostCenter.objects.count()
    has_more = end < total_count
    
    response_data = {
        'results': enhanced_centers,
        'pagination': {
            'more': has_more,
            'page': page,
            'total_count': total_count
        }
    }
    
    return JsonResponse(response_data, safe=False)

@login_required
def api_applications(request):
    """API endpoint to get all unique applications for filter dropdown"""
    from django.http import JsonResponse
    from django.db.models import Q
    
    # Get unique applications from change requests
    applications = ChangeRequest.objects.filter(
        Q(application__isnull=False) & 
        Q(application__gt='')
    ).values_list('application', flat=True).distinct().order_by('application')
    
    return JsonResponse(list(applications), safe=False)

    
@login_required
@monitor_performance(threshold_ms=500)
def datatable_data(request, view):
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    length = int(request.GET.get('length', default=10))
    search_value = request.GET.get('search[value]', default='')
    
    try:
        user = request.user
        
        print("view: ", view)

        if user.region:
            # Use optimized filtering function
            records = get_filtered_records(user, view)
            
            # Apply search filter
            if search_value:
                records = records.filter(
                    Q(change_reason__icontains=search_value) |
                    Q(change_description__icontains=search_value) |
                    Q(application__icontains=search_value) |
                    Q(new_profile__first_name__icontains=search_value) |
                    Q(new_profile__last_name__icontains=search_value) |
                    Q(new_profile__email__icontains=search_value) |
                    Q(new_profile__username__icontains=search_value)
                )
            
            # Apply sorting
            order_column = request.GET.get('order[0][column]')
            order = request.GET.get('order[0][dir]')
            if order_column:
                column_name = request.GET.get(f'columns[{order_column}][data]')
                if column_name not in ["it_section_head_approval", "section_head_approval"]:
                    if order == 'desc':
                        column_name = f'-{column_name}'
                else:
                    column_name = "created_at" if order == 'asc' else "-created_at"
                records = records.order_by(column_name)
            else:
                records = records.order_by('-created_at')
            
            # Apply additional filters for filter view
            if view == "filter":
                filters = {
                    'change_type': request.GET.get('cr_type'),
                    'application': request.GET.get('cr_app'),
                    'date_from': request.GET.get('start_date'),
                    'date_to': request.GET.get('end_date')
                }
                records = apply_filters(records, filters)
                
                # Handle other filters
                if request.GET.get('region'):
                    region_ = Regions.objects.filter(id=request.GET.get('region')).first()
                    if region_:
                        records = records.filter(region=region_)
                
                if request.GET.get('cost_center'):
                    cost_center_ = CostCenter.objects.filter(id=request.GET.get('cost_center')).first()
                    if cost_center_:
                        records = records.filter(cost_center=cost_center_)
            # Total number of records before filtering
            total = records.count() if records else 0

            # Pagination
            paginator = Paginator(records, length)
            page_number = start // length + 1
            page_obj = paginator.get_page(page_number)

            # Prepare response data
            data = []
            for obj in page_obj:
                try:
                    change_requests = {
                        "cr_id": obj.cr_id,
                        "change_type": obj.change_type,
                        "change_description": obj.change_description,
                        "change_reason": obj.change_reason,
                        "application": obj.application,
                        "overall_status": obj.overall_status,  # Use computed property
                        "status_display": obj.status_display,  # Use computed property
                        "status_color_class": obj.status_color_class,  # Use computed property
                        "creator_designation": obj.creator_designation.description,
                        "created_by": obj.created_by.first_name + " " + obj.created_by.last_name,
                        "region": obj.region.region,
                        "cost_center": obj.cost_center.name if obj.cost_center else "",
                        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                    
                    # Add delegation-specific information if this is a delegation request
                    if obj.change_type == "Temporary Role Delegation" and obj.profile_change:
                        try:
                            import json
                            delegation_data = json.loads(obj.profile_change.roles_actions) if obj.profile_change.roles_actions else {}
                            change_requests["delegation_info"] = {
                                "delegator": delegation_data.get('delegator_id'),
                                "delegatee": obj.profile_change.user.get_full_name(),
                                "start_date": delegation_data.get('start_date'),
                                "end_date": delegation_data.get('end_date'),
                                "reason": delegation_data.get('reason'),
                                "roles_count": obj.profile_change.role_to_assign.count()
                            }
                        except Exception as e:
                            print(f"Error parsing delegation data: {e}")
                            change_requests["delegation_info"] = None

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


# =============================================================================
# OPTIMIZED API ENDPOINTS - Phase 3 Performance Enhancement
# =============================================================================

@login_required
@require_http_methods(["GET"])
def api_change_requests_optimized(request):
    """
    Optimized API endpoint for change requests with cursor-based pagination.
    Provides better performance for large datasets.
    """
    start_time = time.time()
    
    try:
        user = request.user
        if not user.region:
            return JsonResponse({'error': 'User region not set'}, status=400)
        
        # Get query parameters
        view_type = request.GET.get('view', 'all')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 25)), 100)  # Max 100 per page
        use_cursor = request.GET.get('use_cursor', 'false').lower() == 'true'
        cursor = request.GET.get('cursor')
        
        # Get filtered records
        records = get_filtered_records(user, view_type)
        
        # Apply search if provided
        search_value = request.GET.get('search', '')
        if search_value:
            records = records.filter(
                Q(change_reason__icontains=search_value) |
                Q(change_description__icontains=search_value) |
                Q(application__icontains=search_value) |
                Q(new_profile__first_name__icontains=search_value) |
                Q(new_profile__last_name__icontains=search_value) |
                Q(new_profile__email__icontains=search_value) |
                Q(new_profile__username__icontains=search_value)
            )
        
        # Get paginated data
        paginated_data = get_paginated_data(
            records, 
            page=page, 
            per_page=per_page, 
            use_cursor=use_cursor, 
            cursor=cursor
        )
        
        # Prepare response data
        data = []
        for obj in paginated_data['data']:
            try:
                change_request_data = {
                    "cr_id": obj.cr_id,
                    "change_type": obj.change_type,
                    "change_description": obj.change_description,
                    "change_reason": obj.change_reason,
                    "application": obj.application,
                    "overall_status": obj.overall_status,
                    "status_display": obj.status_display,
                    "status_color_class": obj.status_color_class,
                    "creator_designation": obj.creator_designation.description,
                    "created_by": obj.created_by.first_name + " " + obj.created_by.last_name,
                    "region": obj.region.region,
                    "cost_center": obj.cost_center.name if obj.cost_center else "",
                    "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                data.append(change_request_data)
            except Exception as ex:
                logger.error(f"Error processing record {obj.cr_id}: {ex}")
        
        # Calculate performance metrics
        execution_time = time.time() - start_time
        
        response_data = {
            'data': data,
            'pagination': paginated_data['pagination'],
            'performance': {
                'execution_time': round(execution_time, 3),
                'records_returned': len(data),
                'view_type': view_type
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in api_change_requests_optimized: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
@cache_page(300)  # Cache for 5 minutes
def api_change_request_stats(request):
    """
    Optimized API endpoint for change request statistics.
    Cached for better performance.
    """
    try:
        user = request.user
        if not user.region:
            return JsonResponse({'error': 'User region not set'}, status=400)
        
        # Get base queryset
        base_queryset = get_change_requests_optimized(user)
        
        # Calculate statistics efficiently
        stats = {
            'total_requests': base_queryset.count(),
            'pending_sh': base_queryset.filter(overall_status='pending_sh').count(),
            'pending_it': base_queryset.filter(overall_status='pending_it').count(),
            'approved_complete': base_queryset.filter(overall_status='approved_complete').count(),
            'rejected': base_queryset.filter(
                Q(overall_status='rejected_sh') | Q(overall_status='rejected_it')
            ).count(),
            'delegation_requests': base_queryset.filter(change_type="Temporary Role Delegation").count(),
            'active_delegations': base_queryset.filter(
                change_type="Temporary Role Delegation",
                overall_status='approved_complete'
            ).count(),
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error in api_change_request_stats: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_change_request_detail(request, cr_id):
    """
    Optimized API endpoint for individual change request details.
    """
    try:
        user = request.user
        if not user.region:
            return JsonResponse({'error': 'User region not set'}, status=400)
        
        # Get change request with optimized query
        change_request = ChangeRequest.objects.select_related(
            'new_profile',
            'profile_change__user',
            'profile_deactivation__user',
            'created_by',
            'creator_designation',
            'region',
            'cost_center'
        ).prefetch_related(
            'crapproval_set__approver',
            'crapproval_set__approver_role'
        ).filter(cr_id=cr_id, region=user.region).first()
        
        if not change_request:
            return JsonResponse({'error': 'Change request not found'}, status=404)
        
        # Prepare detailed data
        detail_data = {
            'cr_id': change_request.cr_id,
            'change_type': change_request.change_type,
            'change_description': change_request.change_description,
            'change_reason': change_request.change_reason,
            'application': change_request.application,
            'overall_status': change_request.overall_status,
            'status_display': change_request.status_display,
            'status_color_class': change_request.status_color_class,
            'creator_designation': change_request.creator_designation.description,
            'created_by': {
                'name': change_request.created_by.first_name + " " + change_request.created_by.last_name,
                'username': change_request.created_by.username,
                'email': change_request.created_by.email
            },
            'region': change_request.region.region,
            'cost_center': change_request.cost_center.name if change_request.cost_center else "",
            'created_at': change_request.created_at.strftime("%Y-%m-%d %H:%M"),
            'updated_at': change_request.updated_at.strftime("%Y-%m-%d %H:%M"),
            'approvals': []
        }
        
        # Add approval details
        for approval in change_request.crapproval_set.all():
            detail_data['approvals'].append({
                'approver': approval.approver.first_name + " " + approval.approver.last_name,
                'role': approval.approver_role.role,
                'status': approval.approval_status,
                'comment': approval.comment,
                'date': approval.approval_date.strftime("%Y-%m-%d %H:%M")
            })
        
        return JsonResponse(detail_data)
        
    except Exception as e:
        logger.error(f"Error in api_change_request_detail: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_performance_metrics(request):
    """
    API endpoint to get performance metrics for monitoring.
    """
    try:
        # This would typically connect to a monitoring system
        # For now, we'll return basic metrics
        metrics = {
            'timestamp': timezone.now().isoformat(),
            'database_connections': 'active',  # Would be actual count
            'cache_hit_rate': '95%',  # Would be actual rate
            'average_response_time': '150ms',  # Would be actual time
            'active_users': 1,  # Would be actual count
        }
        
        return JsonResponse(metrics)
        
    except Exception as e:
        logger.error(f"Error in api_performance_metrics: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
