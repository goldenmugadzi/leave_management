"""
Views for managing fault locator roles using the central user roles system.
These views provide a user-friendly interface for role assignment and management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator

from it.users.models import UserProfile, Roles, Application, Depots
from fault_locator.central_roles import FaultLocatorRoleManager, is_senior_foreman
from fault_locator.models import FaultLocatorRole

@login_required
def manage_fault_locator_roles(request):
    """Main interface for managing fault locator roles"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check if user has permission to manage roles
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior foremen can manage fault locator roles")
        return redirect('fault_locator_dashboard')
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Get all users with optional filtering
    users = UserProfile.objects.filter(is_active=True)
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Get users with their current fault locator roles
    users_with_roles = []
    for user in users:
        current_role = FaultLocatorRoleManager.get_user_role(user)
        current_role_display = FaultLocatorRoleManager.get_user_role_display(user)
        
        # Apply role filter
        if role_filter and current_role != role_filter:
            continue
            
        users_with_roles.append({
            'user': user,
            'current_role': current_role,
            'current_role_display': current_role_display,
            'depot': user.depot.depot if user.depot else 'Not Assigned'
        })
    
    # Paginate results
    paginator = Paginator(users_with_roles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available roles
    available_roles = FaultLocatorRoleManager.get_available_roles()
    
    # Get available depots for depot foreperson assignments
    from .depot_foreperson_validation import get_available_depots_for_foreperson_assignment
    available_depots = get_available_depots_for_foreperson_assignment()
    
    # Get statistics
    stats = {
        'total_users': UserProfile.objects.filter(is_active=True).count(),
        'users_with_roles': len([u for u in users_with_roles if u['current_role']]),
        'senior_foremen': FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.SENIOR_FOREMAN).count(),
        'depot_forepersons': FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.DEPOT_FOREPERSON).count(),
        'team_leaders': FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.TEAM_LEADER).count(),
        'team_members': FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.TEAM_MEMBER).count(),
    }
    
    context = {
        'user_profile': user_profile,
        'page_obj': page_obj,
        'available_roles': available_roles,
        'available_depots': available_depots,
        'stats': stats,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': [
            (FaultLocatorRoleManager.SENIOR_FOREMAN, 'Senior Foreman'),
            (FaultLocatorRoleManager.DEPOT_FOREPERSON, 'Depot Foreperson'),
            (FaultLocatorRoleManager.TEAM_LEADER, 'Team Leader'),
            (FaultLocatorRoleManager.TEAM_MEMBER, 'Team Member'),
            (FaultLocatorRoleManager.FAULT_REPORTER, 'Fault Reporter'),
        ]
    }
    
    return render(request, 'fault_locator/manage_roles.html', context)

@login_required
def assign_fault_locator_role_ajax(request):
    """AJAX endpoint for assigning fault locator roles"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        user_id = request.POST.get('user_id')
        role_code = request.POST.get('role_code')
        depot_id = request.POST.get('depot_id')
        
        if not user_id or not role_code:
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        target_user = get_object_or_404(UserProfile, id=user_id)
        
        # Special handling for depot foreperson role
        if role_code == FaultLocatorRoleManager.DEPOT_FOREPERSON:
            if not depot_id:
                return JsonResponse({'success': False, 'message': 'Depot selection is required for depot foreperson role'})
            
            depot = get_object_or_404(Depots, id=depot_id)
            
            # Use the depot-specific assignment function
            from .central_roles import assign_depot_foreperson_to_depot
            success, message = assign_depot_foreperson_to_depot(target_user, depot, user_profile)
            
            if success:
                return JsonResponse({
                    'success': True, 
                    'message': message,
                    'new_role': role_code,
                    'new_role_display': 'Depot Foreperson',
                    'depot': depot.depot
                })
            else:
                return JsonResponse({'success': False, 'message': message})
        else:
            # Regular role assignment for non-depot roles
            success = FaultLocatorRoleManager.assign_role(
                target_user, 
                role_code, 
                user_profile
            )
            
            if success:
                role_display = FaultLocatorRoleManager.get_user_role_display(target_user)
                return JsonResponse({
                    'success': True, 
                    'message': f'Role "{role_display}" assigned to {target_user.get_full_name()}',
                    'new_role': role_code,
                    'new_role_display': role_display
                })
            else:
                return JsonResponse({'success': False, 'message': 'Failed to assign role'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def remove_fault_locator_role_ajax(request):
    """AJAX endpoint for removing fault locator roles"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Missing user ID'})
        
        target_user = get_object_or_404(UserProfile, id=user_id)
        
        # Remove the role
        success = FaultLocatorRoleManager.remove_role(target_user)
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': f'Fault locator role removed from {target_user.get_full_name()}'
            })
        else:
            return JsonResponse({'success': False, 'message': 'Failed to remove role'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def depot_assignment_overview(request):
    """View to show depot foreperson assignment overview"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior foremen can view depot assignments")
        return redirect('fault_locator_dashboard')
    
    from .depot_foreperson_validation import get_depot_assignment_summary, get_available_depots_for_foreperson_assignment
    
    # Get assignment summary
    summary = get_depot_assignment_summary()
    
    # Get available depots for new assignments
    available_depots = get_available_depots_for_foreperson_assignment()
    
    # Get qualified users who can be depot forepersons
    from .central_roles import is_depot_foreperson_by_designation
    qualified_users = []
    for user in UserProfile.objects.filter(is_active=True):
        if is_depot_foreperson_by_designation(user):
            # Check if user doesn't already have a depot assignment
            if not user.depot:
                qualified_users.append(user)
    
    context = {
        'user_profile': user_profile,
        'summary': summary,
        'available_depots': available_depots,
        'qualified_users': qualified_users,
    }
    
    return render(request, 'fault_locator/depot_assignment_overview.html', context)

@login_required
def assign_depot_foreperson_ajax(request):
    """AJAX endpoint for assigning depot foreperson to a specific depot"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        user_id = request.POST.get('user_id')
        depot_id = request.POST.get('depot_id')
        
        if not user_id or not depot_id:
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        target_user = get_object_or_404(UserProfile, id=user_id)
        depot = get_object_or_404(Depots, id=depot_id)
        
        # Use the depot-specific assignment function
        from .central_roles import assign_depot_foreperson_to_depot
        success, message = assign_depot_foreperson_to_depot(target_user, depot, user_profile)
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': message,
                'user_name': target_user.get_full_name(),
                'depot_name': depot.depot
            })
        else:
            return JsonResponse({'success': False, 'message': message})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def remove_depot_foreperson_ajax(request):
    """AJAX endpoint for removing depot foreperson from a depot"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Missing user ID'})
        
        target_user = get_object_or_404(UserProfile, id=user_id)
        
        # Use the depot-specific removal function
        from .central_roles import remove_depot_foreperson_from_depot
        success, message = remove_depot_foreperson_from_depot(target_user, user_profile)
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': message,
                'user_name': target_user.get_full_name()
            })
        else:
            return JsonResponse({'success': False, 'message': message})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
