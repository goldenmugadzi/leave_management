from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from it.users.models import UserProfile, Application, Roles
from fault_locator.central_roles import get_user_fault_locator_role, has_fault_locator_permissions

@login_required
def debug_role_status(request):
    """Debug view to check role status"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    debug_info = {
        'user_id': request.user.id,
        'username': request.user.username,
        'user_profile_exists': user_profile is not None,
    }
    
    if user_profile:
        debug_info.update({
            'first_name': user_profile.first_name,
            'last_name': user_profile.last_name,
            'depot': str(user_profile.depot) if user_profile.depot else None,
            'designation': str(user_profile.designation) if user_profile.designation else None,
            'section': str(user_profile.section) if user_profile.section else None,
        })
        
        # Check central roles
        try:
            fault_locator_app = Application.objects.filter(name='fault_locator').first()
            debug_info['fault_locator_app_exists'] = fault_locator_app is not None
            
            if fault_locator_app:
                debug_info['fault_locator_app_id'] = fault_locator_app.id
                debug_info['fault_locator_app_fullname'] = fault_locator_app.fullname
                
                # Get user's fault locator roles
                user_fault_locator_roles = user_profile.roles.filter(app_id=fault_locator_app)
                debug_info['user_fault_locator_roles_count'] = user_fault_locator_roles.count()
                debug_info['user_fault_locator_roles'] = [
                    {
                        'role': role.role,
                        'name': role.name,
                        'description': role.description
                    } for role in user_fault_locator_roles
                ]
                
                # Test central role functions
                debug_info['central_role_result'] = get_user_fault_locator_role(user_profile)
                debug_info['central_permissions'] = has_fault_locator_permissions(user_profile)
                
            # Get all available fault locator roles
            all_fault_locator_roles = Roles.objects.filter(application='fault_locator')
            debug_info['all_fault_locator_roles_count'] = all_fault_locator_roles.count()
            debug_info['all_fault_locator_roles'] = [
                {
                    'role': role.role,
                    'name': role.name,
                    'description': role.description
                } for role in all_fault_locator_roles
            ]
                
        except Exception as e:
            debug_info['error'] = str(e)
    
    return JsonResponse(debug_info, indent=2)
