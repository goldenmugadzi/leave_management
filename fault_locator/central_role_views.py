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

from it.users.models import UserProfile, Roles, Application
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
        
        if not user_id or not role_code:
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        target_user = get_object_or_404(UserProfile, id=user_id)
        
        # Assign the role
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
def role_assignment_history(request):
    """View role assignment history"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior foremen can view role assignment history")
        return redirect('fault_locator_dashboard')
    
    # Get legacy role assignments for migration tracking
    legacy_assignments = FaultLocatorRole.objects.select_related(
        'user', 'assigned_by', 'depot'
    ).order_by('-assigned_at')
    
    # Get current central role assignments
    application = FaultLocatorRoleManager.get_application()
    current_assignments = []
    
    if application:
        users_with_roles = UserProfile.objects.filter(
            roles__application='fault_locator',
            roles__app_id=application
        ).distinct()
        
        for user in users_with_roles:
            role = FaultLocatorRoleManager.get_user_role_display(user)
            current_assignments.append({
                'user': user,
                'role': role,
                'depot': user.depot.depot if user.depot else 'Not Assigned'
            })
    
    context = {
        'user_profile': user_profile,
        'legacy_assignments': legacy_assignments,
        'current_assignments': current_assignments,
        'application': application
    }
    
    return render(request, 'fault_locator/role_history.html', context)

@login_required
def migrate_legacy_roles_view(request):
    """View to migrate legacy FaultLocatorRole to central system"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior foremen can migrate roles")
        return redirect('fault_locator_dashboard')
    
    if request.method == 'POST':
        from fault_locator.central_roles import migrate_legacy_roles
        
        try:
            migrated, errors = migrate_legacy_roles()
            
            if migrated > 0:
                messages.success(request, f'Successfully migrated {migrated} role assignments')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
            
            if migrated == 0 and not errors:
                messages.info(request, 'No legacy roles found to migrate')
                
        except Exception as e:
            messages.error(request, f'Migration failed: {str(e)}')
    
    # Get counts for display
    legacy_count = FaultLocatorRole.objects.filter(is_active=True).count()
    
    context = {
        'user_profile': user_profile,
        'legacy_count': legacy_count,
    }
    
    return render(request, 'fault_locator/migrate_roles.html', context)
