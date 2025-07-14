from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, ExpressionWrapper, DurationField, Sum, Q, Count
from django.template.loader import render_to_string
from django.http import JsonResponse
import datetime
from decouple import config

from it.users.helpers import DEPOTS
from .models import *
from .forms import FaultForm, FaultLocatorDeviceForm, FaultLocatorTeamForm, FaultLocatorTeamNameForm, AddTeamMemberForm, AssignDeviceToTeamForm, AssignFaultForm, TeamDeploymentForm, SeniorForepersonDeviceAssignmentForm
from it.users.models import UserProfile, Notification
from it.users.views import ms_exhange_send_html

# ROLE-BASED PERMISSION FUNCTIONS

def get_user_fault_locator_role(user_profile):
    """Get the user's primary fault locator role"""
    if not user_profile:
        return None
    
    # Check for explicit role assignment first
    role_assignment = FaultLocatorRole.objects.filter(
        user=user_profile, 
        is_active=True
    ).first()
    
    if role_assignment:
        return role_assignment.role
    
    # Fallback to designation-based role detection
    if is_senior_foreman(user_profile):
        return 'senior_foreman'
    elif is_depot_foreperson_by_designation(user_profile):
        return 'depot_foreperson'
    
    # Check if user is a team leader
    if FaultLocatorTeam.objects.filter(team_leader=user_profile).exists():
        return 'team_leader'
    
    # Check if user is a team member
    if user_profile.fault_locator_teams.exists():
        return 'team_member'
    
    return None

def is_senior_foreman(user_profile):
    """Check if user is a senior foreman - can delegate machines to depots"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        return 'senior' in designation_desc and ('foreman' in designation_desc or 'foreperson' in designation_desc)
    except Exception:
        return False

def is_depot_foreperson_by_designation(user_profile):
    """Check if user is depot foreperson by designation"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        return ('foreperson' in designation_desc or 'foreman' in designation_desc) and 'senior' not in designation_desc
    except Exception:
        return False

def is_depot_foreperson(user_profile, depot_code=None):
    """Check if user is foreperson for specific depot or their assigned depot"""
    if not user_profile:
        return False
    
    # Check by designation first
    if not is_depot_foreperson_by_designation(user_profile):
        return False
    
    # If depot_code is provided, check if user is assigned to that depot
    if depot_code:
        if hasattr(user_profile, 'depot') and user_profile.depot:
            if isinstance(depot_code, str):
                return user_profile.depot.code == depot_code
            else:
                return user_profile.depot == depot_code
    
    # If no specific depot, just check if they are a foreperson
    return True

def can_assign_faults(user_profile, depot=None):
    """Check if user can assign faults at given depot"""
    if is_senior_foreman(user_profile):
        return True
    
    if depot and is_depot_foreperson(user_profile):
        if hasattr(user_profile, 'depot') and user_profile.depot:
            return user_profile.depot == depot or user_profile.depot.code == depot.code
    
    return False

def can_deploy_teams(user_profile):
    """Check if user can deploy teams to depots"""
    return is_senior_foreman(user_profile)

def can_manage_devices(user_profile):
    """Check if user can manage fault locator devices"""
    # Senior foremen can manage all devices
    if is_senior_foreman(user_profile):
        return True
    
    # IT personnel can manage devices
    if hasattr(user_profile, 'section') and user_profile.section:
        try:
            section_name = str(user_profile.section.section).lower()
            if 'it' in section_name or 'information technology' in section_name:
                return True
        except Exception:
            pass
    
    return False

def can_create_teams(user_profile):
    """Check if user can create and manage teams"""
    return is_senior_foreman(user_profile) or can_manage_devices(user_profile)

def is_team_leader(user_profile):
    """Check if user is a team leader"""
    if not user_profile:
        return False
    return FaultLocatorTeam.objects.filter(team_leader=user_profile).exists()

def get_user_team(user_profile):
    """Get the team where user is leader or member"""
    if not user_profile:
        return None
    
    # Check if user is team leader
    team_as_leader = FaultLocatorTeam.objects.filter(team_leader=user_profile).first()
    if team_as_leader:
        return team_as_leader
    
    # Check if user is team member
    return user_profile.fault_locator_teams.first()

def can_report_fault_status(user_profile, fault):
    """Check if user can report on fault status"""
    # Team leaders can report for their assignments
    if is_team_leader(user_profile):
        assignment = FaultAssignment.objects.filter(
            fault=fault, 
            team__team_leader=user_profile,
            located_at__isnull=True
        ).first()
        if assignment:
            return True
    
    # Forepersons can also report at their depot
    if is_depot_foreperson(user_profile):
        if hasattr(user_profile, 'depot') and user_profile.depot:
            return fault.depot == user_profile.depot
    
    # Senior foremen can report on any fault
    return is_senior_foreman(user_profile)

def get_user_depot(user_profile):
    """Get the depot object for a user profile"""
    if not user_profile or not hasattr(user_profile, 'depot') or not user_profile.depot:
        return None
    
    try:
        # Handle both direct depot object and depot code
        if hasattr(user_profile.depot, 'depot'):
            return user_profile.depot
        else:
            return Depots.objects.filter(code=user_profile.depot).first()
    except Exception:
        return None

@login_required
def role_based_dashboard(request):
    """Role-based dashboard showing appropriate functions for each user role"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    user_role = get_user_fault_locator_role(user_profile)
    
    if not user_role:
        # User has no fault locator role
        return render(request, 'fault_locator/no_access.html', {
            'user_profile': user_profile,
            'message': 'You do not have any assigned role in the Fault Locator system. Please contact your administrator.'
        })
    
    context = {
        'user_profile': user_profile,
        'user_role': user_role,
        'role_display': dict(FaultLocatorRole.ROLE_CHOICES).get(user_role, user_role),
    }
    
    # Role-specific context and actions
    if user_role == 'senior_foreman':
        context.update(get_senior_foreman_context(user_profile))
    elif user_role == 'depot_foreperson':
        context.update(get_depot_foreperson_context(user_profile))
    elif user_role == 'team_leader':
        context.update(get_team_leader_context(user_profile))
    elif user_role == 'team_member':
        context.update(get_team_member_context(user_profile))
    
    return render(request, 'fault_locator/role_dashboard.html', context)

def get_senior_foreman_context(user_profile):
    """Get context data for senior foreman dashboard"""
    # Senior foreman can see system-wide statistics and manage all aspects
    
    # Available teams for deployment
    available_teams = FaultLocatorTeam.objects.filter(
        current_depot__isnull=True,
        faultlocatordeviceassignment__isnull=False
    ).distinct()
    
    # Teams currently deployed
    deployed_teams = TeamDeployment.objects.filter(recalled_at__isnull=True).select_related('team', 'depot')
    
    # Devices without team assignment
    unassigned_devices = FaultLocatorDevice.objects.filter(
        faultlocatordeviceassignment__isnull=True,
        status='available'
    )
    
    # High priority unassigned faults
    critical_faults = Fault.objects.filter(
        status='requested',
        priority__gte=3
    ).select_related('depot')
    
    # System statistics
    stats = {
        'total_devices': FaultLocatorDevice.objects.filter(status='available').count(),
        'total_teams': FaultLocatorTeam.objects.count(),
        'active_deployments': deployed_teams.count(),
        'unassigned_critical': critical_faults.count(),
        'pending_faults': Fault.objects.filter(status='requested').count(),
        'active_faults': Fault.objects.filter(status='assigned').count(),
    }
    
    # Recent deployments
    recent_deployments = TeamDeployment.objects.filter(
        deployed_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).select_related('team', 'depot', 'deployed_by').order_by('-deployed_at')[:5]
    
    return {
        'available_teams': available_teams,
        'deployed_teams': deployed_teams,
        'unassigned_devices': unassigned_devices,
        'critical_faults': critical_faults,
        'stats': stats,
        'recent_deployments': recent_deployments,
        'primary_actions': [
            {
                'title': 'Deploy Team to Depot',
                'description': f'Deploy {available_teams.count()} available teams',
                'url': '/fault_locator/deploy-team/',
                'icon': '🚀',
                'priority': 'high' if available_teams.count() > 0 else 'medium'
            },
            {
                'title': 'Assign Devices to Teams',
                'description': f'Assign {unassigned_devices.count()} available devices',
                'url': '/fault_locator/assign-device-to-team/',
                'icon': '📱',
                'priority': 'high' if unassigned_devices.count() > 0 else 'medium'
            },
            {
                'title': 'Monitor Critical Faults',
                'description': f'Review {critical_faults.count()} high priority faults',
                'url': '/fault_locator/faults/?priority=3',
                'icon': '🔥',
                'priority': 'critical' if critical_faults.count() > 0 else 'low'
            }
        ]
    }

def get_depot_foreperson_context(user_profile):
    """Get context data for depot foreperson dashboard"""
    user_depot = get_user_depot(user_profile)
    
    if not user_depot:
        return {'error': 'No depot assigned to your profile'}
    
    # Faults at my depot
    my_faults = Fault.objects.filter(depot=user_depot).order_by('-priority', '-reported_at')
    pending_faults = my_faults.filter(status='requested')
    active_faults = my_faults.filter(status='assigned')
    
    # Teams at my depot
    teams_at_depot = FaultLocatorTeam.objects.filter(current_depot=user_depot)
    
    # Recent fault assignments I made
    my_assignments = FaultAssignment.objects.filter(
        assigned_by=user_profile,
        assigned_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).select_related('fault', 'team', 'device').order_by('-assigned_at')[:5]
    
    stats = {
        'pending_faults': pending_faults.count(),
        'active_faults': active_faults.count(),
        'teams_available': teams_at_depot.count(),
        'high_priority': my_faults.filter(priority__gte=3, status__in=['requested', 'assigned']).count(),
        'completed_today': my_faults.filter(
            status='located',
            faultassignment__located_at__date=timezone.now().date()
        ).count(),
    }
    
    return {
        'user_depot': user_depot,
        'pending_faults': pending_faults[:10],  # Show top 10
        'active_faults': active_faults[:10],
        'teams_at_depot': teams_at_depot,
        'my_assignments': my_assignments,
        'stats': stats,
        'primary_actions': [
            {
                'title': 'Assign Pending Faults',
                'description': f'Assign {pending_faults.count()} pending faults to teams',
                'url': '/fault_locator/assign-fault/',
                'icon': '👉',
                'priority': 'high' if pending_faults.count() > 0 else 'low'
            },
            {
                'title': 'Report New Fault',
                'description': 'Report a new fault at your depot',
                'url': '/fault_locator/report-fault/',
                'icon': '📝',
                'priority': 'medium'
            },
            {
                'title': 'Monitor Team Progress',
                'description': f'Check progress of {active_faults.count()} active faults',
                'url': f'/fault_locator/faults/?depot={user_depot.id}&status=assigned',
                'icon': '👁️',
                'priority': 'medium' if active_faults.count() > 0 else 'low'
            }
        ]
    }

def get_team_leader_context(user_profile):
    """Get context data for team leader dashboard"""
    my_team = FaultLocatorTeam.objects.filter(team_leader=user_profile).first()
    
    if not my_team:
        return {'error': 'You are not assigned as a team leader'}
    
    # Current assignments for my team
    current_assignments = FaultAssignment.objects.filter(
        team=my_team,
        located_at__isnull=True
    ).select_related('fault', 'device').order_by('-fault__priority', 'assigned_at')
    
    # Completed assignments today
    completed_today = FaultAssignment.objects.filter(
        team=my_team,
        located_at__date=timezone.now().date()
    ).select_related('fault')
    
    # Team device
    team_device = FaultLocatorDeviceAssignment.objects.filter(team=my_team).first()
    
    # Team performance stats
    stats = {
        'active_assignments': current_assignments.count(),
        'completed_today': completed_today.count(),
        'team_location': my_team.current_depot.depot if my_team.current_depot else 'Not Deployed',
        'device_assigned': team_device.device.serial_number if team_device else 'No Device',
        'team_members': my_team.members.count(),
    }
    
    # Urgent assignments (high priority or overdue)
    urgent_assignments = current_assignments.filter(
        Q(fault__priority__gte=3) | 
        Q(assigned_at__lt=timezone.now() - timezone.timedelta(hours=4))
    )
    
    return {
        'my_team': my_team,
        'current_assignments': current_assignments,
        'completed_today': completed_today,
        'team_device': team_device,
        'urgent_assignments': urgent_assignments,
        'stats': stats,
        'primary_actions': [
            {
                'title': 'Report Fault Located',
                'description': f'Update status for {current_assignments.count()} active assignments',
                'url': '/fault_locator/my-assignments/',
                'icon': '✅',
                'priority': 'high' if current_assignments.count() > 0 else 'medium'
            },
            {
                'title': 'Update Work Progress',
                'description': 'Add progress notes to ongoing work',
                'url': '/fault_locator/update-progress/',
                'icon': '📊',
                'priority': 'medium'
            },
            {
                'title': 'Request Assistance',
                'description': 'Request help from depot foreperson',
                'url': '/fault_locator/request-help/',
                'icon': '🆘',
                'priority': 'low'
            }
        ]
    }

def get_team_member_context(user_profile):
    """Get context data for team member dashboard"""
    my_teams = user_profile.fault_locator_teams.all()
    
    if not my_teams.exists():
        return {'error': 'You are not assigned to any fault locator team'}
    
    my_team = my_teams.first()  # Assuming user is in one team
    
    # Current team assignments
    current_assignments = FaultAssignment.objects.filter(
        team=my_team,
        located_at__isnull=True
    ).select_related('fault', 'device').order_by('-fault__priority')
    
    # Team leader
    team_leader = my_team.team_leader
    
    # Team device
    team_device = FaultLocatorDeviceAssignment.objects.filter(team=my_team).first()
    
    stats = {
        'team_name': my_team.name,
        'team_leader': team_leader.get_full_name() if team_leader else 'No Leader Assigned',
        'current_location': my_team.current_depot.depot if my_team.current_depot else 'Not Deployed',
        'device': team_device.device.serial_number if team_device else 'No Device',
        'active_work': current_assignments.count(),
    }
    
    return {
        'my_team': my_team,
        'team_leader': team_leader,
        'current_assignments': current_assignments,
        'team_device': team_device,
        'stats': stats,
        'primary_actions': [
            {
                'title': 'View Current Work',
                'description': f'Check {current_assignments.count()} active assignments',
                'url': '/fault_locator/team-work/',
                'icon': '🛠️',
                'priority': 'high' if current_assignments.count() > 0 else 'medium'
            },
            {
                'title': 'Contact Team Leader',
                'description': f'Message {team_leader.get_full_name() if team_leader else "Team Leader"}',
                'url': '/fault_locator/contact-leader/',
                'icon': '📞',
                'priority': 'medium'
            }
        ]
    }

@login_required 
def assign_role(request):
    """Allow senior foremen to assign roles to users"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior foremen can assign fault locator roles")
        return redirect('role_based_dashboard')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        depot_id = request.POST.get('depot_id') if request.POST.get('depot_id') else None
        
        target_user = get_object_or_404(UserProfile, id=user_id)
        
        # Remove any existing role for this user
        FaultLocatorRole.objects.filter(user=target_user).update(is_active=False)
        
        # Create new role assignment
        role_assignment = FaultLocatorRole.objects.create(
            user=target_user,
            role=role,
            depot_id=depot_id,
            assigned_by=user_profile
        )
        
        messages.success(request, f"Role '{role}' assigned to {target_user.get_full_name()}")
        return redirect('assign_role')
    
    # GET request - show form
    users = UserProfile.objects.filter(is_active=True).order_by('last_name', 'first_name')
    depots = Depots.objects.all().order_by('depot')
    current_roles = FaultLocatorRole.objects.filter(is_active=True).select_related('user', 'depot')
    
    context = {
        'user_profile': user_profile,
        'users': users,
        'depots': depots,
        'role_choices': FaultLocatorRole.ROLE_CHOICES,
        'current_roles': current_roles,
    }
    
    return render(request, 'fault_locator/assign_role.html', context)

# Legacy function aliases for backward compatibility
def can_create_device(user_profile):
    """Legacy function - check if user has permission to create devices"""
    return can_manage_devices(user_profile)

def is_foreperson(user_profile):
    """Legacy function - check if user profile belongs to any foreperson"""
    return is_depot_foreperson_by_designation(user_profile) or is_senior_foreman(user_profile)

def has_fault_locator_permissions(user_profile):
    """Check if user has any fault locator system permissions"""
    role = get_user_fault_locator_role(user_profile)
    return role is not None
