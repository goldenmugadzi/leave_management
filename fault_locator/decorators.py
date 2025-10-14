"""
Role-based access control decorators for fault locator views.
These decorators work with the central user roles system.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from it.users.models import UserProfile
from .central_roles import (
    FaultLocatorRoleManager,
    is_senior_foreman,
    is_depot_foreperson,
    is_team_leader,
    is_team_member,
    can_assign_faults,
    can_deploy_teams,
    can_manage_devices,
    can_create_teams,
    has_fault_locator_permissions
)

def fault_locator_access_required(view_func):
    """
    Decorator to ensure user has any fault locator role before accessing views.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not has_fault_locator_permissions(user_profile):
            messages.error(request, "You do not have access to the Fault Locator system. Please contact your administrator.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def senior_foreman_required(view_func):
    """
    Decorator to restrict access to senior foremen only.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not is_senior_foreman(user_profile):
            messages.error(request, "Only senior foremen can access this feature.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def depot_foreperson_required(view_func):
    """
    Decorator to restrict access to depot forepersons and senior foremen.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not (is_depot_foreperson(user_profile) or is_senior_foreman(user_profile)):
            messages.error(request, "Only depot forepersons and senior foremen can access this feature.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def team_leader_required(view_func):
    """
    Decorator to restrict access to team leaders and above.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not (is_team_leader(user_profile) or is_depot_foreperson(user_profile) or is_senior_foreman(user_profile)):
            messages.error(request, "Only team leaders and above can access this feature.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def team_member_required(view_func):
    """
    Decorator to restrict access to team members and above.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not (is_team_member(user_profile) or is_team_leader(user_profile) or 
                is_depot_foreperson(user_profile) or is_senior_foreman(user_profile)):
            messages.error(request, "Only team members and above can access this feature.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def device_management_required(view_func):
    """
    Decorator to restrict access to users who can manage gear.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not can_manage_devices(user_profile):
            messages.error(request, "You do not have permission to manage gear.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def team_management_required(view_func):
    """
    Decorator to restrict access to users who can manage teams.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not can_create_teams(user_profile):
            messages.error(request, "You do not have permission to manage teams.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def fault_assignment_required(view_func):
    """
    Decorator to restrict access to users who can assign faults.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not can_assign_faults(user_profile):
            messages.error(request, "You do not have permission to assign faults.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def team_deployment_required(view_func):
    """
    Decorator to restrict access to users who can deploy teams.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not can_deploy_teams(user_profile):
            messages.error(request, "You do not have permission to deploy teams.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def role_based_access(*allowed_roles):
    """
    Decorator to allow access only to users with specific roles.
    Usage: @role_based_access('senior_foreman', 'depot_foreperson')
    """
    def decorator(view_func):
        @wraps(view_func)
        @fault_locator_access_required
        def wrapper(request, *args, **kwargs):
            user_profile = UserProfile.objects.filter(id=request.user.id).first()
            user_role = FaultLocatorRoleManager.get_user_role(user_profile)
            
            if user_role not in allowed_roles:
                role_names = [dict(FaultLocatorRoleManager.get_available_roles().values_list('role', 'name')).get(role, role) for role in allowed_roles]
                messages.error(request, f"Access restricted to: {', '.join(role_names)}")
                return redirect('fault_locator:fault_locator_dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def depot_specific_access(view_func):
    """
    Decorator to ensure depot forepersons can only access their own depot's data.
    Senior foremen have access to all depots.
    """
    @wraps(view_func)
    @fault_locator_access_required
    def wrapper(request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Senior foremen have access to all depots
        if is_senior_foreman(user_profile):
            return view_func(request, *args, **kwargs)
        
        # Depot forepersons can only access their depot
        if is_depot_foreperson(user_profile):
            # Check if there's a depot parameter in the URL or request
            depot_id = kwargs.get('depot_id') or request.GET.get('depot_id')
            if depot_id:
                user_depot = user_profile.depot
                if user_depot and str(user_depot.id) != str(depot_id):
                    messages.error(request, "You can only access data for your assigned depot.")
                    return redirect('fault_locator:fault_locator_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
