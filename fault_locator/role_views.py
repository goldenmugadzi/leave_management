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
from it.users.models import UserProfile, Notification, Application, Roles
from it.users.views import ms_exhange_send_html

# Import central role functions
from .central_roles import (
    get_user_fault_locator_role,
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

# ROLE-BASED PERMISSION FUNCTIONS

# Note: Role checking functions are now imported from central_roles.py
# This maintains backward compatibility while using the central role system

def get_user_fault_locator_role_legacy(user_profile):
    """Legacy function - now uses central role system"""
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

def is_depot_foreperson_by_designation(user_profile):
    """Check if user is depot foreperson by designation (legacy function)"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        return ('foreperson' in designation_desc or 'foreman' in designation_desc) and 'senior' not in designation_desc
    except Exception:
        return False
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
        # Check if user has central fault locator permissions
        central_has_permissions = has_fault_locator_permissions(user_profile)
        
        # Get user's actual roles for debugging
        central_roles = []
        if user_profile:
            try:
                from it.users.models import Application, Roles
                fault_locator_app = Application.objects.filter(name='fault_locator').first()
                if fault_locator_app:
                    central_roles = list(user_profile.roles.filter(app_id=fault_locator_app))
            except Exception as e:
                print(f"Error getting central roles: {e}")
        
        # User has no fault locator role
        return render(request, 'fault_locator/no_access.html', {
            'user_profile': user_profile,
            'central_has_permissions': central_has_permissions,
            'central_roles': central_roles,
            'message': 'You do not have any assigned role in the Fault Locator system. Please contact your administrator.'
        })
    
    context = {
        'user_profile': user_profile,
        'user_role': user_role,
        'role_display': dict(FaultLocatorRole.ROLE_CHOICES).get(user_role, user_role),
        # Add permission checks to context
        'can_deploy_teams': can_deploy_teams(user_profile),
        'can_manage_devices': can_manage_devices(user_profile),
        'can_assign_faults': can_assign_faults(user_profile),
        'can_create_teams': can_create_teams(user_profile),
        'is_senior_foreman': is_senior_foreman(user_profile),
        'is_depot_foreperson': is_depot_foreperson(user_profile),
        'is_team_leader': is_team_leader(user_profile),
        # Provide defaults to avoid template resolution logging errors
        'recent_deployments': [],
        'my_assignments': [],
        'completed_today': [],
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
                'url': '/fault_locator/teams/deploy/',
                'icon_class': 'fas fa-rocket',
                'priority': 'high' if available_teams.count() > 0 else 'medium'
            },
            {
                'title': 'Assign Gear to Teams',
                'description': f'Assign {unassigned_devices.count()} available gear',
                'url': '/fault_locator/assign-device-to-team/',
                'icon_class': 'fas fa-mobile-screen-button',
                'priority': 'high' if unassigned_devices.count() > 0 else 'medium'
            },
            {
                'title': 'Monitor Critical Faults',
                'description': f'Review {critical_faults.count()} high priority faults',
                'url': '/fault_locator/simple-faults/?priority=3',
                'icon_class': 'fas fa-fire',
                'priority': 'critical' if critical_faults.count() > 0 else 'low'
            }
        ],
        'secondary_actions': [
            {
                'title': 'Team Overview',
                'description': 'View all teams and their status',
                'url': '/fault_locator/team-overview/',
                'icon_class': 'fas fa-users',
                'priority': 'medium'
            },
            {
                'title': 'Gear Management',
                'description': 'Manage fault locator gear',
                'url': '/fault_locator/devices/',
                'icon_class': 'fas fa-wrench',
                'priority': 'medium'
            },
            {
                'title': 'Create New Team',
                'description': 'Create and configure new teams',
                'url': '/fault_locator/teams/create/',
                'icon_class': 'fas fa-plus',
                'priority': 'medium'
            },
            {
                'title': 'Advanced Fault Assignment',
                'description': 'Bulk assign faults to teams',
                'url': '/fault_locator/advanced-assign/',
                'icon_class': 'fas fa-bolt',
                'priority': 'medium'
            },
            {
                'title': 'Performance Monitoring',
                'description': 'View system performance metrics',
                'url': '/fault_locator/performance-monitoring/',
                'icon_class': 'fas fa-chart-line',
                'priority': 'medium'
            },
            {
                'title': 'Role Management',
                'description': 'Manage user roles and permissions',
                'url': '/fault_locator/manage-roles/',
                'icon_class': 'fas fa-user-shield',
                'priority': 'medium'
            },
            {
                'title': 'Team-Depot Management',
                'description': 'Manage team deployments to depots',
                'url': '/fault_locator/team-depot-management/',
                'icon_class': 'fas fa-building',
                'priority': 'medium'
            },
            {
                'title': 'Gear-Team Management',
                'description': 'Manage gear assignments to teams',
                'url': '/fault_locator/device-team-management/',
                'icon_class': 'fas fa-mobile-screen',
                'priority': 'medium'
            },
            {
                'title': 'Depot Assignments',
                'description': 'Manage depot foreperson assignments',
                'url': '/fault_locator/depot-assignments/',
                'icon_class': 'fas fa-industry',
                'priority': 'medium'
            },
            {
                'title': 'Senior Foreman Dashboard',
                'description': 'Access dedicated senior foreman interface',
                'url': '/fault_locator/senior-dashboard/',
                'icon_class': 'fas fa-user-tie',
                'priority': 'medium'
            }
        ]
    }

def get_depot_foreperson_context(user_profile):
    """Get context data for depot foreperson dashboard"""
    user_depot = get_user_depot(user_profile)
    
    if not user_depot:
        return {'error': 'No depot assigned to your profile'}
    
    # Check if this user is formally assigned as depot foreperson
    depot_foreperson_role = FaultLocatorRole.objects.filter(
        user=user_profile,
        role='depot_foreperson',
        depot=user_depot,
        is_active=True
    ).first()
    
    # Faults at my depot - ordered by priority criteria (VVIP → Voltage → Clients → Date → Priority)
    my_faults = Fault.objects.filter(depot=user_depot).order_by(
        '-vvip',                 # Priority 0: VVIP status (VVIP first)
        '-voltage',              # Priority 1: Voltage (highest first)
        '-clients_affected',     # Priority 2: Clients affected (most first)
        'reported_at',           # Priority 3: Date reported (oldest first) 
        '-priority'              # Priority 4: Priority level (highest first)
    )
    pending_faults = my_faults.filter(status='requested')
    active_faults = my_faults.filter(status='assigned')
    
    # Teams at my depot
    teams_at_depot = FaultLocatorTeam.objects.filter(current_depot=user_depot)
    
    # Check if this foreperson has been assigned a specific team to lead
    my_team_as_leader = FaultLocatorTeam.objects.filter(team_leader=user_profile).first()
    
    # Check if this foreperson is part of any team as a member
    my_teams_as_member = user_profile.fault_locator_teams.all()
    
    # Get devices assigned to my team(s)
    my_team_devices = []
    if my_team_as_leader:
        team_devices = FaultLocatorDeviceAssignment.objects.filter(
            team=my_team_as_leader
        ).select_related('device')
        my_team_devices.extend(team_devices)
    
    for team in my_teams_as_member:
        team_devices = FaultLocatorDeviceAssignment.objects.filter(
            team=team
        ).select_related('device')
        my_team_devices.extend(team_devices)
    
    # Remove duplicates
    my_team_devices = list(set(my_team_devices))
    
    # Recent fault assignments I made
    my_assignments = FaultAssignment.objects.filter(
        assigned_by=user_profile,
        assigned_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).select_related('fault', 'team', 'device').order_by('-assigned_at')[:5]
    
    # Completed assignments today (for template iteration)
    completed_today = FaultAssignment.objects.filter(
        fault__depot=user_depot,
        located_at__date=timezone.now().date()
    ).select_related('fault', 'team').order_by('-located_at')[:5]
    
    # Enhanced stats
    stats = {
        'pending_faults': pending_faults.count(),
        'active_faults': active_faults.count(),
        'teams_available': teams_at_depot.count(),
        'high_priority': my_faults.filter(priority__gte=3, status__in=['requested', 'assigned']).count(),
        'completed_today': completed_today.count(),
        'my_team_devices': len(my_team_devices),
        'teams_with_devices': teams_at_depot.filter(
            faultlocatordeviceassignment__isnull=False
        ).distinct().count(),
    }
    
    return {
        'user_depot': user_depot,
        'depot_foreperson_role': depot_foreperson_role,
        'my_team_as_leader': my_team_as_leader,
        'my_teams_as_member': my_teams_as_member,
        'my_team_devices': my_team_devices,
        'pending_faults': pending_faults[:10],  # Show top 10
        'active_faults': active_faults[:10],
        'teams_at_depot': teams_at_depot,
        'my_assignments': my_assignments,
        'completed_today': completed_today,  # Pass as queryset for template iteration
        'stats': stats,
        'can_assign_faults': can_assign_faults(user_profile),
        'primary_actions': [
            {
                'title': 'Assign Pending Faults',
                'description': f'Assign {pending_faults.count()} pending faults to teams',
                'url': '/fault_locator/simple-assign/',
                'icon_class': 'fas fa-hand-point-right',
                'priority': 'high' if pending_faults.count() > 0 else 'low'
            },
            {
                'title': 'Report New Fault',
                'description': 'Report a new fault at your depot',
                'url': '/fault_locator/quick-report/',
                'icon_class': 'fas fa-pen-to-square',
                'priority': 'medium'
            },
            {
                'title': 'Monitor Team Progress',
                'description': f'Check progress of {active_faults.count()} active faults',
                'url': '/fault_locator/simple-faults/?status=assigned',
                'icon_class': 'fas fa-eye',
                'priority': 'medium' if active_faults.count() > 0 else 'low'
            }
        ],
        'secondary_actions': [
            {
                'title': 'My Work Overview',
                'description': 'View your assigned work and progress',
                'url': '/fault_locator/my-work/',
                'icon_class': 'fas fa-screwdriver-wrench',
                'priority': 'medium'
            },
            {
                'title': 'All Faults at Depot',
                'description': 'View all faults at your depot',
                'url': '/fault_locator/simple-faults/',
                'icon_class': 'fas fa-clipboard-list',
                'priority': 'medium'
            },
            {
                'title': 'Create Fault Report',
                'description': 'Create detailed fault report',
                'url': '/fault_locator/create-fault/',
                'icon_class': 'fas fa-file-circle-plus',
                'priority': 'medium'
            },
            {
                'title': 'Team Management',
                'description': 'View teams at your depot',
                'url': '/fault_locator/team-overview/',
                'icon_class': 'fas fa-users',
                'priority': 'medium'
            },
            {
                'title': 'Advanced Assignment',
                'description': 'Use advanced fault assignment features',
                'url': '/fault_locator/advanced-assign/',
                'icon_class': 'fas fa-bolt',
                'priority': 'medium'
            },
            {
                'title': 'Fault Priority Management',
                'description': 'Change fault priorities',
                'url': '/fault_locator/simple-faults/',
                'icon_class': 'fas fa-fire',
                'priority': 'medium'
            },
            {
                'title': 'Team Deployment',
                'description': 'Deploy teams to your depot',
                'url': '/fault_locator/teams/deploy/',
                'icon_class': 'fas fa-rocket',
                'priority': 'medium'
            },
            {
                'title': 'Gear Assignment',
                'description': 'Assign gear to teams',
                'url': '/fault_locator/assign-device-to-team/',
                'icon_class': 'fas fa-mobile-screen-button',
                'priority': 'medium'
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
    'device_assigned': team_device.device.serial_number if team_device else 'No Gear',
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
                'url': '/fault_locator/my-work/',
                'icon_class': 'fas fa-check-circle',
                'priority': 'high' if current_assignments.count() > 0 else 'medium'
            },
            {
                'title': 'Update Work Progress',
                'description': 'Add progress notes to ongoing work',
                'url': '/fault_locator/my-work/',
                'icon_class': 'fas fa-chart-line',
                'priority': 'medium'
            },
            {
                'title': 'Request Assistance',
                'description': 'Request help from depot foreperson',
                'url': '/fault_locator/request-help/',
                'icon_class': 'fas fa-life-ring',
                'priority': 'low'
            }
        ],
        'secondary_actions': [
            {
                'title': 'Field Updates',
                'description': 'Update fault status from field',
                'url': '/fault_locator/field-update/',
                'icon_class': 'fas fa-arrows-rotate',
                'priority': 'medium'
            },
            {
                'title': 'Team Overview',
                'description': 'View your team details and members',
                'url': '/fault_locator/team-overview/',
                'icon_class': 'fas fa-users',
                'priority': 'medium'
            },
            {
                'title': 'Simple Fault List',
                'description': 'View all faults in simple format',
                'url': '/fault_locator/simple-faults/',
                'icon_class': 'fas fa-clipboard-list',
                'priority': 'medium'
            },
            {
                'title': 'Current Assignments',
                'description': 'View detailed assignment information',
                'url': '/fault_locator/my-assignments/',
                'icon_class': 'fas fa-list-check',
                'priority': 'medium'
            },
            {
                'title': 'Quick Fault Report',
                'description': 'Quick fault reporting interface',
                'url': '/fault_locator/quick-report/',
                'icon_class': 'fas fa-pen-to-square',
                'priority': 'medium'
            },
            {
                'title': 'Team Management',
                'description': 'Manage team members and settings',
                'url': '/fault_locator/teams/',
                'icon_class': 'fas fa-gear',
                'priority': 'medium'
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
    'device': team_device.device.serial_number if team_device else 'No Gear',
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
                'url': '/fault_locator/my-work/',
                'icon_class': 'fas fa-screwdriver-wrench',
                'priority': 'high' if current_assignments.count() > 0 else 'medium'
            },
            {
                'title': 'Contact Team Leader',
                'description': f'Message {team_leader.get_full_name() if team_leader else "Team Leader"}',
                'url': '/fault_locator/contact-leader/',
                'icon_class': 'fas fa-phone',
                'priority': 'medium'
            }
        ],
        'secondary_actions': [
            {
                'title': 'Team Overview',
                'description': 'View team details and members',
                'url': '/fault_locator/team-overview/',
                'icon_class': 'fas fa-users',
                'priority': 'medium'
            },
            {
                'title': 'Simple Fault List',
                'description': 'View all faults in simple format',
                'url': '/fault_locator/simple-faults/',
                'icon_class': 'fas fa-clipboard-list',
                'priority': 'medium'
            },
            {
                'title': 'Team Work',
                'description': 'View your team\'s current work',
                'url': '/fault_locator/team-work/',
                'icon_class': 'fas fa-wrench',
                'priority': 'medium'
            },
            {
                'title': 'Quick Fault Report',
                'description': 'Quick fault reporting interface',
                'url': '/fault_locator/quick-report/',
                'icon_class': 'fas fa-pen-to-square',
                'priority': 'medium'
            },
            {
                'title': 'Simple Fault Updates',
                'description': 'Update fault status from field',
                'url': '/fault_locator/field-update/',
                'icon_class': 'fas fa-mobile-screen',
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
    if not user_profile:
        return False
    
    # Check for formal roles first
    role = get_user_fault_locator_role(user_profile)
    if role is not None:
        return True
    
    # Check if user is a team member or team leader
    from .models import FaultLocatorTeam
    
    # Check if user is a team leader
    if FaultLocatorTeam.objects.filter(team_leader=user_profile).exists():
        return True
    
    # Check if user is a team member
    if FaultLocatorTeam.objects.filter(members=user_profile).exists():
        return True
    
    return False
