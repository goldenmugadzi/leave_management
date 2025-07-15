from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, ExpressionWrapper, DurationField, Sum, Q, Count
from django.template.loader import render_to_string
from django.http import JsonResponse
import datetime
from datetime import timedelta
from decouple import config

from it.users.helpers import DEPOTS
from .models import *
from .forms import FaultForm, FaultLocatorDeviceForm, FaultLocatorTeamForm, FaultLocatorTeamNameForm, AddTeamMemberForm, AssignDeviceToTeamForm, AssignFaultForm, TeamDeploymentForm, SeniorForepersonDeviceAssignmentForm
from it.users.models import UserProfile, Notification
from it.users.views import ms_exhange_send_html
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
from .decorators import (
    fault_locator_access_required,
    senior_foreman_required,
    depot_foreperson_required,
    team_leader_required,
    team_member_required,
    device_management_required,
    team_management_required,
    fault_assignment_required,
    team_deployment_required,
    role_based_access,
    depot_specific_access
)

# Notification Functions (keeping existing ones)
def notify_fault_locator_user(user, message, notification_type, url, fault_or_team_id, request):
    """Send notification to a fault locator user - Creates database notification and sends email"""
    try:
        # Create database notification
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            notification_id=str(fault_or_team_id),
            url=url,
            created_at=datetime.datetime.now(),
        )
        
        # Send email notification if user has email
        if user.email:
            # Determine greeting based on time
            hour = datetime.datetime.now().hour
            greetings = {
                (0, 4): "Good night!",
                (5, 11): "Good morning!",
                (12, 16): "Good afternoon!",
                (17, 20): "Good evening!",
                (21, 23): "Good night!"
            }
            subject = next((msg for (start, end), msg in greetings.items() if start <= hour <= end), "Hello!")
            
            # Build full URL
            domain_name = config('be_url', default='http://localhost:8000')
            full_url = f"{domain_name}{url}"
            
            # Email context
            email_context = {
                "redirect_url": full_url,
                "type": notification_type,
                "user_fullname": user.get_full_name(),
                "message": message
            }
            
            # Send email
            response = ms_exhange_send_html(
                subject=f"{subject} - {notification_type}",
                to_recipients=[user.email],
                cc_recipients=[],
                template='email/email_template.html',
                kwargs={"kwargs": email_context}
            )
            
            return True
            
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

def notify_fault_assignment(fault_assignment, request):
    """Notify team members when a fault is assigned to their team"""
    fault = fault_assignment.fault
    team = fault_assignment.team
    device = fault_assignment.device
    
    # Notify all team members
    for member in team.members.all():
        if member.email:
            message = f"New fault assigned to your team '{team.name}': {fault.description} at {fault.depot.depot}. Device: {device.serial_number}"
            url = f"/fault_locator/faults/{fault.id}/"
            notify_fault_locator_user(
                user=member,
                message=message,
                notification_type="Fault Assignment",
                url=url,
                fault_or_team_id=fault.id,
                request=request
            )
    
    # Notify depot foreperson if different from assigner
    depot_forepersons = UserProfile.objects.filter(
        depot=fault.depot.code,
        designation__description__icontains='foreperson'
    ).exclude(id=request.user.id)
    
    for foreperson in depot_forepersons:
        if foreperson.email:
            message = f"Fault at your depot has been assigned to team '{team.name}': {fault.description}. Priority: {fault.get_priority_display()}"
            url = f"/fault_locator/faults/{fault.id}/"
            notify_fault_locator_user(
                user=foreperson,
                message=message,
                notification_type="Fault Assignment Update",
                url=url,
                fault_or_team_id=fault.id,
                request=request
            )

def notify_fault_status_update(fault, old_status, new_status, updated_by, request):
    """Notify relevant users when fault status is updated"""
    # Get current assignment
    current_assignment = FaultAssignment.objects.filter(
        fault=fault, 
        located_at__isnull=True
    ).first()
    
    if current_assignment:
        team = current_assignment.team
        
        # Notify team members (except the one who updated)
        for member in team.members.exclude(id=updated_by.id):
            if member.email:
                message = f"Fault status updated by {updated_by.get_full_name()}: '{fault.description}' changed from {old_status} to {new_status}"
                url = f"/fault_locator/faults/{fault.id}/"
                notify_fault_locator_user(
                    user=member,
                    message=message,
                    notification_type="Fault Status Update",
                    url=url,
                    fault_or_team_id=fault.id,
                    request=request
                )
    
    # Notify depot foreperson
    depot_forepersons = UserProfile.objects.filter(
        depot=fault.depot.code,
        designation__description__icontains='foreperson'
    ).exclude(id=updated_by.id)
    
    for foreperson in depot_forepersons:
        if foreperson.email:
            message = f"Fault status updated at your depot: '{fault.description}' is now {new_status}"
            url = f"/fault_locator/faults/{fault.id}/"
            notify_fault_locator_user(
                user=foreperson,
                message=message,
                notification_type="Fault Status Update",
                url=url,
                fault_or_team_id=fault.id,
                request=request
            )
    
    # If fault is located, notify senior forepersons
    if new_status == 'located':
        senior_forepersons = UserProfile.objects.filter(
            designation__description__icontains='senior foreperson'
        )
        
        for senior_fp in senior_forepersons:
            if senior_fp.email:
                message = f"Fault successfully located: '{fault.description}' at {fault.depot.depot} by team {current_assignment.team.name if current_assignment else 'Unknown'}"
                url = f"/fault_locator/faults/{fault.id}/"
                notify_fault_locator_user(
                    user=senior_fp,
                    message=message,
                    notification_type="Fault Located",
                    url=url,
                    fault_or_team_id=fault.id,
                    request=request
                )

def notify_team_deployment(deployment, request):
    """Notify team members when they are deployed to a depot"""
    team = deployment.team
    depot = deployment.depot
    
    # Notify all team members
    for member in team.members.all():
        if member.email:
            message = f"Your team '{team.name}' has been deployed to {depot.depot}. Please report to the depot for fault location duties."
            url = f"/fault_locator/teams/{team.id}/"
            notify_fault_locator_user(
                user=member,
                message=message,
                notification_type="Team Deployment",
                url=url,
                fault_or_team_id=team.id,
                request=request
            )
    
    # Notify depot foreperson
    depot_forepersons = UserProfile.objects.filter(
        depot=depot.code,
        designation__description__icontains='foreperson'
    )
    
    for foreperson in depot_forepersons:
        if foreperson.email:
            message = f"Team '{team.name}' has been deployed to your depot. Team members: {', '.join([m.get_full_name() for m in team.members.all()])}"
            url = f"/fault_locator/teams/{team.id}/"
            notify_fault_locator_user(
                user=foreperson,
                message=message,
                notification_type="Team Deployment",
                url=url,
                fault_or_team_id=team.id,
                request=request
            )

def notify_high_priority_fault(fault, request):
    """Notify senior forepersons about high priority faults"""
    if fault.priority >= 3:  # High or Critical priority
        senior_forepersons = UserProfile.objects.filter(
            designation__description__icontains='senior foreperson'
        )
        
        for senior_fp in senior_forepersons:
            if senior_fp.email:
                priority_name = fault.get_priority_display()
                message = f"HIGH PRIORITY FAULT reported: '{fault.description}' at {fault.depot.depot}. Priority: {priority_name}"
                url = f"/fault_locator/faults/{fault.id}/"
                notify_fault_locator_user(
                    user=senior_fp,
                    message=message,
                    notification_type="High Priority Fault",
                    url=url,
                    fault_or_team_id=fault.id,
                    request=request
                )

def notify_unassigned_faults(request):
    """Daily notification function for unassigned faults (to be called by scheduler)"""
    from datetime import timedelta
    
    # Get faults that are unassigned for more than 2 hours
    two_hours_ago = timezone.now() - timedelta(hours=2)
    unassigned_faults = Fault.objects.filter(
        status='requested',
        reported_at__lt=two_hours_ago
    )
    
    if unassigned_faults.exists():
        # Group by depot
        depot_faults = {}
        for fault in unassigned_faults:
            depot_code = fault.depot.code
            if depot_code not in depot_faults:
                depot_faults[depot_code] = []
            depot_faults[depot_code].append(fault)
        
        # Notify depot forepersons
        for depot_code, faults in depot_faults.items():
            depot_forepersons = UserProfile.objects.filter(
                depot=depot_code,
                designation__description__icontains='foreperson'
            )
            
            for foreperson in depot_forepersons:
                if foreperson.email:
                    fault_list = '\n'.join([f"- {f.description}" for f in faults])
                    message = f"You have {len(faults)} unassigned fault(s) at your depot:\n{fault_list}"
                    url = "/fault_locator/faults/"
                    notify_fault_locator_user(
                        user=foreperson,
                        message=message,
                        notification_type="Unassigned Faults Alert",
                        url=url,
                        fault_or_team_id="multiple",
                        request=request
                    )

# SIMPLIFIED MAIN VIEWS

@login_required
def fault_locator_dashboard(request):
    """ROLE-BASED: Main dashboard - customized per user role with access restrictions"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check if user has any fault locator permissions
    if not has_fault_locator_permissions(user_profile):
        return render(request, 'fault_locator/no_access.html', {
            'user_profile': user_profile,
            'message': 'You do not have access to the Fault Locator system. Please contact your administrator.',
            'contact_info': 'Contact your senior foreman or IT administrator for role assignment.'
        })
    
    # Get user role from central system
    user_role = FaultLocatorRoleManager.get_user_role(user_profile)
    user_role_display = FaultLocatorRoleManager.get_user_role_display(user_profile)
    
    # Determine user permissions using central roles
    is_senior = is_senior_foreman(user_profile)
    is_depot_fp = is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)
    user_can_manage_devices = can_manage_devices(user_profile)
    user_teams = user_profile.fault_locator_teams.all() if user_profile else []
    is_team_member = user_teams.exists()
    is_team_lead = is_team_leader(user_profile)

    # Get user's depot if applicable
    user_depot = None
    if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
        user_depot = user_profile.depot  # depot is already a Depots object, not a code
    
    # Initialize context with role information
    context = {
        'user_profile': user_profile,
        'user_role': user_role,
        'user_role_display': user_role_display,
        'is_senior_foreman': is_senior,
        'is_depot_foreperson': is_depot_fp,
        'is_team_leader': is_team_lead,
        'is_team_member': is_team_member,
        'can_manage_devices': user_can_manage_devices,
        'user_depot': user_depot,
        'my_actions': [],
        'quick_stats': {},
        'recent_activity': [],
        'accessible_functions': [],
        'role_permissions': {
            'can_assign_faults': can_assign_faults(user_profile),
            'can_deploy_teams': can_deploy_teams(user_profile),
            'can_create_teams': can_create_teams(user_profile),
            'can_manage_devices': user_can_manage_devices,
            'can_create_faults': True,  # All users can create faults
            'can_view_faults': True,    # All users can view faults
            'can_view_reports': True,   # All users can view reports
        }
    }
    
    # Get role-specific statistics
    stats = {}
    
    try:
        if user_role == 'senior_foreman':
            # Senior foreman sees all statistics
            stats.update({
                'total_open_faults': Fault.objects.filter(status__in=['requested', 'assigned']).count(),
                'assigned_faults': Fault.objects.filter(status='assigned').count(),
                'resolved_today': Fault.objects.filter(
                    status='closed', 
                    reported_at__date=datetime.datetime.now().date()
                ).count(),
                'active_teams': FaultLocatorTeam.objects.filter(current_depot__isnull=False).count(),
            })
            
            # Depot performance statistics
            from django.db.models import Count, Q
            depot_stats = []
            for depot in Depots.objects.all():
                try:
                    depot_faults = Fault.objects.filter(depot=depot)
                    open_faults = depot_faults.filter(status__in=['requested', 'assigned']).count()
                    total_faults = depot_faults.count()
                    resolution_rate = 0 if total_faults == 0 else int((depot_faults.filter(status='closed').count() / total_faults) * 100)
                    
                    depot_stats.append({
                        'name': depot.depot,  # Use depot.depot field instead of depot.name
                        'open_faults': open_faults,
                        'resolution_rate': resolution_rate
                    })
                except Exception as e:
                    # Skip depot if there's an error
                    continue
            stats['depot_stats'] = depot_stats
            
        elif user_role == 'depot_foreperson':
            # Depot foreperson sees depot-specific statistics
            user_depot = user_profile.depot
            if user_depot:
                depot_faults = Fault.objects.filter(depot=user_depot)
                stats.update({
                    'depot_open_faults': depot_faults.filter(status__in=['requested', 'assigned']).count(),
                    'depot_resolved_today': depot_faults.filter(
                        status='closed', 
                        reported_at__date=datetime.datetime.now().date()
                    ).count(),
                    'user_depot': user_depot,
                })
                
                # My teams statistics
                my_teams = FaultLocatorTeam.objects.filter(current_depot=user_depot)
                stats.update({
                    'my_teams_count': my_teams.count(),
                    'my_teams': my_teams,
                })
                
                # Team efficiency calculation
                total_assigned = Fault.objects.filter(depot=user_depot, status='assigned').count()
                total_resolved = Fault.objects.filter(depot=user_depot, status='closed').count()
                team_efficiency = 0 if total_assigned == 0 else int((total_resolved / total_assigned) * 100)
                stats['team_efficiency'] = team_efficiency
                
                # Recent depot faults
                recent_depot_faults = depot_faults.select_related('depot', 'reported_by').order_by('-reported_at')[:10]
                stats['recent_depot_faults'] = recent_depot_faults
                
        elif user_role == 'team_leader':
            # Team leader sees team-specific statistics
            user_team = user_profile.fault_locator_teams.first()
            if user_team:
                # Get faults assigned to this team through FaultAssignment
                team_fault_assignments = FaultAssignment.objects.filter(assigned_team=user_team)
                team_faults = Fault.objects.filter(faultassignment__in=team_fault_assignments)
                
                stats.update({
                    'team_open_faults': team_faults.filter(status__in=['requested', 'assigned']).count(),
                    'team_completed_today': team_faults.filter(
                        status='closed', 
                        reported_at__date=datetime.datetime.now().date()
                    ).count(),
                    'team_in_progress': team_faults.filter(status='assigned').count(),
                    'user_team': user_team,
                })
                
                # Team members
                team_members = user_team.members.all()
                stats.update({
                    'team_members_count': team_members.count(),
                    'team_members': team_members,
                })
                
                # Current team assignments
                team_assignments = team_faults.filter(status__in=['requested', 'assigned']).select_related('depot')
                stats['team_assignments'] = team_assignments
                
        elif user_role == 'team_member':
            # Team member sees personal statistics
            user_team = user_profile.fault_locator_teams.first()
            if user_team:
                # Get faults assigned to this team through FaultAssignment
                team_fault_assignments = FaultAssignment.objects.filter(assigned_team=user_team)
                my_faults = Fault.objects.filter(faultassignment__in=team_fault_assignments)
                
                stats.update({
                    'my_assigned_faults': my_faults.filter(status__in=['requested', 'assigned']).count(),
                    'my_in_progress': my_faults.filter(status='assigned').count(),
                    'my_completed_today': my_faults.filter(
                        status='closed', 
                        reported_at__date=datetime.datetime.now().date()
                    ).count(),
                    'my_completed_week': my_faults.filter(
                        status='closed', 
                        reported_at__date__gte=datetime.datetime.now().date() - timedelta(days=7)
                    ).count(),
                })
                
                # My current assignments
                my_assignments = my_faults.filter(status__in=['requested', 'assigned']).select_related('depot')
                stats['my_assignments'] = my_assignments
    
    except Exception as e:
        # If there's an error getting statistics, provide empty stats
        stats = {}
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting dashboard statistics: {e}")
    
    # Add stats to context
    context.update(stats)
    
    # ACCESSIBLE FUNCTIONS - What can this user do in the system?
    accessible_functions = {}

    # Senior Foreperson & IT/Admin Functions
    if is_senior or user_can_manage_devices:
        accessible_functions['device_list'] = {
            'title': 'Device Management',
            'description': 'View, create, edit, and assign all fault locator devices.',
            'url_name': 'device_list',
            'icon': '📱'
        }
        accessible_functions['team_overview'] = {
            'title': 'Team Management',
            'description': 'Create, edit, and manage fault locator teams and their members.',
            'url_name': 'team_overview',
            'icon': '👥'
        }

    if is_senior:
        accessible_functions['deploy_team'] = {
            'title': 'Deploy Teams',
            'description': 'Deploy available teams to various depot locations.',
            'url_name': 'deploy_team',
            'icon': '🚀'
        }
        accessible_functions['advanced_fault_assignment'] = {
            'title': 'Advanced Fault Assignment',
            'description': 'Bulk-assign faults to teams with advanced filtering.',
            'url_name': 'advanced_fault_assignment',
            'icon': '⚙️'
        }
        accessible_functions['simple_fault_list_senior'] = {
            'title': 'View All Faults',
            'description': 'Monitor all faults across all depots and statuses.',
            'url_name': 'simple_fault_list',
            'icon': '🔥'
        }

    # Depot Foreperson Functions
    if is_depot_fp:
        if not is_senior: # Avoid duplication for senior FPs who are also depot FPs
            accessible_functions['simple_fault_list_depot'] = {
                'title': 'Depot Faults',
                'description': 'View and manage all faults reported at your depot.',
                'url_name': 'simple_fault_list',
                'icon': '🔥'
            }
        accessible_functions['assign_faults'] = {
            'title': 'Assign Faults',
            'description': 'Assign pending faults at your depot to available teams.',
            'url_name': 'advanced_fault_assignment',
            'icon': '👉'
        }

    # Team Member Functions
    if is_team_member:
        accessible_functions['my_work'] = {
            'title': 'My Work',
            'description': 'View your current fault assignments and update their status.',
            'url_name': 'my_work',
            'icon': '🛠️'
        }

    # General Functions for most users
    accessible_functions['quick_fault_report'] = {
        'title': 'Report a Fault',
        'description': 'Quickly report a new fault in the system.',
        'url_name': 'quick_fault_report',
        'icon': '📝'
    }
    
    context['accessible_functions'] = list(accessible_functions.values())

    # MY ACTIONS - What can I do right now?
    my_actions = []
    
    # For Team Members - Field Workers
    user_teams = user_profile.fault_locator_teams.all() if user_profile else []
    if user_teams.exists():
        # Get my team's current assignments
        my_team = user_teams.first()
        active_assignments = FaultAssignment.objects.filter(
            team=my_team,
            located_at__isnull=True
        ).select_related('fault', 'device')
        
        for assignment in active_assignments:
            my_actions.append({
                'title': f'Update Fault Status',
                'description': f'{assignment.fault.description} at {assignment.fault.depot.depot}',
                'url': f'/fault_locator/faults/{assignment.fault.id}/',
                'priority': assignment.fault.priority,
                'type': 'field_work',
                'device': assignment.device.serial_number
            })
    
    # For Depot Forepersons
    if is_depot_fp and user_depot:
        # Unassigned faults at my depot
        unassigned_count = Fault.objects.filter(
            depot=user_depot,
            status='requested'
        ).count()
        
        if unassigned_count > 0:
            my_actions.append({
                'title': f'Assign {unassigned_count} Pending Fault{"s" if unassigned_count != 1 else ""}',
                'description': f'Faults waiting for team assignment at {user_depot.depot}',
                'url': '/fault_locator/assign-fault/',
                'priority': 'high',
                'type': 'management',
                'count': unassigned_count
            })
        
        # High priority faults that need attention
        high_priority = Fault.objects.filter(
            depot=user_depot,
            priority__gte=3,
            status__in=['requested', 'assigned']
        ).count()
        
        if high_priority > 0:
            my_actions.append({
                'title': f'Monitor {high_priority} High Priority Fault{"s" if high_priority != 1 else ""}',
                'description': f'Critical/High priority faults at your depot',
                'url': f'/fault_locator/faults/?depot={user_depot.id}&priority=3',
                'priority': 'critical',
                'type': 'monitoring',
                'count': high_priority
            })
    
    # For Senior Forepersons
    if is_senior:
        # Teams available for deployment
        available_teams = FaultLocatorTeam.objects.filter(
            current_depot__isnull=True,
            faultlocatordeviceassignment__isnull=False
        ).distinct().count()
        
        if available_teams > 0:
            my_actions.append({
                'title': f'Deploy {available_teams} Available Team{"s" if available_teams != 1 else ""}',
                'description': 'Teams with devices ready for deployment',
                'url': '/fault_locator/deploy-team/',
                'priority': 'medium',
                'type': 'deployment',
                'count': available_teams
            })
        
        # Overall system status
        total_active_faults = Fault.objects.filter(status__in=['requested', 'assigned']).count()
        if total_active_faults > 10:  # Threshold for attention
            my_actions.append({
                'title': f'Review System Load',
                'description': f'{total_active_faults} active faults across all depots',
                'url': '/fault_locator/analytics/',
                'priority': 'medium',
                'type': 'system',
                'count': total_active_faults
            })
    
    context['my_actions'] = my_actions
    
    # QUICK STATS - Role-based statistics
    if is_senior:
        # System-wide stats for senior forepersons
        context['quick_stats'] = {
            'Total Faults': Fault.objects.count(),
            'Active Faults': Fault.objects.filter(status__in=['requested', 'assigned']).count(),
            'Teams Deployed': TeamDeployment.objects.filter(recalled_at__isnull=True).count(),
            'Devices Active': FaultLocatorDeviceAssignment.objects.count(),
        }
    elif is_depot_fp and user_depot:
        # Depot-specific stats
        context['quick_stats'] = {
            'My Depot Faults': Fault.objects.filter(depot=user_depot).count(),
            'Pending Assignment': Fault.objects.filter(depot=user_depot, status='requested').count(),
            'In Progress': Fault.objects.filter(depot=user_depot, status='assigned').count(),
            'Teams at Depot': FaultLocatorTeam.objects.filter(current_depot=user_depot).count(),
        }
    elif user_teams.exists():
        # Team member stats
        my_team = user_teams.first()
        context['quick_stats'] = {
            'My Team': my_team.name,
            'Current Assignments': FaultAssignment.objects.filter(team=my_team, located_at__isnull=True).count(),
            'Completed Today': FaultAssignment.objects.filter(
                team=my_team,
                located_at__date=timezone.now().date()
            ).count(),
            'Team Location': my_team.current_depot.depot if my_team.current_depot else 'Not Deployed',
        }
    
    # RECENT ACTIVITY - Last 5 relevant activities
    recent_activity = []
    
    if is_senior:
        # System-wide recent activity
        recent_faults = Fault.objects.select_related('depot').order_by('-reported_at')[:5]
        for fault in recent_faults:
            recent_activity.append({
                'description': f'New fault reported: {fault.description}',
                'location': fault.depot.depot,
                'time': fault.reported_at,
                'priority': fault.get_priority_display(),
                'url': f'/fault_locator/faults/{fault.id}/'
            })
    elif is_depot_fp and user_depot:
        # Depot-specific activity
        recent_faults = Fault.objects.filter(depot=user_depot).order_by('-reported_at')[:5]
        for fault in recent_faults:
            recent_activity.append({
                'description': f'Fault: {fault.description}',
                'status': fault.get_status_display(),
                'time': fault.reported_at,
                'priority': fault.get_priority_display(),
                'url': f'/fault_locator/faults/{fault.id}/'
            })
    elif user_teams.exists():
        # Team-specific activity
        my_team = user_teams.first()
        recent_assignments = FaultAssignment.objects.filter(
            team=my_team
        ).select_related('fault').order_by('-assigned_at')[:5]
        for assignment in recent_assignments:
            recent_activity.append({
                'description': f'Assigned: {assignment.fault.description}',
                'location': assignment.fault.depot.depot,
                'time': assignment.assigned_at,
                'status': 'Located' if assignment.located_at else 'In Progress',
                'url': f'/fault_locator/faults/{assignment.fault.id}/'
            })
    
    context['recent_activity'] = recent_activity
    
    return render(request, "fault_locator/dashboard.html", context)

@login_required
def simple_fault_list(request):
    """SIMPLIFIED: Clean, card-based fault list with clear actions"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Base queryset with optimized joins
    faults = Fault.objects.select_related('depot', 'prioritized_by').prefetch_related(
        'faultassignment_set__team', 
        'faultassignment_set__device'
    )
    
    # Role-based filtering
    if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
        depot = Depots.objects.filter(code=user_profile.depot).first()
        if depot:
            faults = faults.filter(depot=depot)
    elif not is_senior_foreman(user_profile):
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            depot = Depots.objects.filter(code=user_profile.depot).first()
            if depot:
                faults = faults.filter(depot=depot)
    
    # Simple filtering
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search_query = request.GET.get('q', '')
    
    if status_filter != 'all':
        faults = faults.filter(status=status_filter)
    
    if priority_filter != 'all':
        faults = faults.filter(priority=int(priority_filter))
    
    if search_query:
        faults = faults.filter(
            Q(description__icontains=search_query) |
            Q(depot__depot__icontains=search_query)
        )
    
    # Order by priority and urgency
    faults = faults.order_by('-priority', '-reported_at')
    
    # Add extra context for each fault
    fault_data = []
    for fault in faults:
        current_assignment = fault.faultassignment_set.filter(located_at__isnull=True).first()
        
        # Calculate time elapsed
        time_elapsed = timezone.now() - fault.reported_at
        urgency = 'normal'
        if fault.priority >= 3:
            urgency = 'critical'
        elif time_elapsed.total_seconds() > 14400:  # 4 hours
            urgency = 'urgent'
        
        # Determine next action
        next_action = None
        can_assign = is_senior_foreman(user_profile) or is_depot_foreperson(user_profile, fault.depot)
        
        if fault.status == 'requested' and can_assign:
            next_action = {
                'text': 'Assign Team',
                'url': f'/fault_locator/assign-fault/?fault_id={fault.id}',
                'class': 'btn-primary'
            }
        elif fault.status == 'assigned' and current_assignment:
            user_teams = user_profile.fault_locator_teams.all() if user_profile else []
            if any(team.id == current_assignment.team.id for team in user_teams):
                next_action = {
                    'text': 'Update Status',
                    'url': f'/fault_locator/faults/{fault.id}/update/',
                    'class': 'btn-success'
                }
        
        fault_data.append({
            'fault': fault,
            'current_assignment': current_assignment,
            'urgency': urgency,
            'time_elapsed': time_elapsed,
            'next_action': next_action,
        })
    
    # Simple filter options
    status_options = [
        ('all', 'All Statuses'),
        ('requested', 'Needs Assignment'),
        ('assigned', 'In Progress'),
        ('located', 'Located'),
        ('closed', 'Completed'),
    ]
    
    priority_options = [
        ('all', 'All Priorities'),
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]
    
    context = {
        'fault_data': fault_data,
        'user_profile': user_profile,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'status_options': status_options,
        'priority_options': priority_options,
        'is_senior_foreman': is_senior_foreman(user_profile),
        'is_depot_foreperson': is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None),
        'total_count': len(fault_data),
    }
    
    return render(request, "fault_locator/simple_fault_list.html", context)

@login_required
def quick_fault_report(request):
    """SIMPLIFIED: Quick fault reporting with minimal fields"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if request.method == "POST":
        # Simple form processing
        description = request.POST.get('description', '').strip()
        priority = int(request.POST.get('priority', 2))
        depot_id = request.POST.get('depot')
        
        if not description:
            messages.error(request, "Please describe the fault")
            return redirect('quick_fault_report')
        
        # Get depot
        depot = None
        if depot_id:
            depot = get_object_or_404(Depots, id=depot_id)
        elif user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            depot = Depots.objects.filter(code=user_profile.depot).first()
        
        if not depot:
            messages.error(request, "Please select a depot")
            return redirect('quick_fault_report')
        
        # Create fault
        fault = Fault.objects.create(
            description=description,
            depot=depot,
            priority=priority,
            reported_by=user_profile,
        )
        
        # Send notifications for high priority faults
        if fault.priority >= 3:
            notify_high_priority_fault(fault, request)
        
        messages.success(request, f"Fault reported successfully! Reference: FL-{fault.id}")
        
        # Redirect based on user role
        if is_depot_foreperson(user_profile, depot):
            messages.info(request, "As depot foreperson, you can now assign this fault to a team")
            return redirect('simple_assign_fault', fault_id=fault.id)
        else:
            return redirect('simple_fault_list')
    
    # GET request - show form
    available_depots = Depots.objects.all().order_by('depot')
    user_depot = None
    
    # Pre-select user's depot
    if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
        user_depot = Depots.objects.filter(code=user_profile.depot).first()
        # For non-senior foremen, show only their depot if they have one
        if not is_senior_foreman(user_profile) and user_depot:
            available_depots = Depots.objects.filter(id=user_depot.id)
    
    context = {
        'user_profile': user_profile,
        'available_depots': available_depots,
        'user_depot': user_depot,
        'priority_choices': Fault._meta.get_field('priority').choices,
    }
    
    return render(request, "fault_locator/quick_fault_report.html", context)

@login_required
@team_member_required
def create_fault(request):
    """Create a new fault using the FaultForm"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if request.method == "POST":
        form = FaultForm(request.POST)
        if form.is_valid():
            fault = form.save(commit=False)
            fault.reported_by = user_profile
            fault.save()
            
            # Send notifications for high priority faults
            if fault.priority >= 3:
                notify_high_priority_fault(fault, request)
            
            messages.success(request, f"Fault reported successfully! Reference: FL-{fault.id}")
            
            # Redirect based on user role
            if is_depot_foreperson(user_profile, fault.depot):
                messages.info(request, "As depot foreperson, you can now assign this fault to a team")
                return redirect('simple_assign_fault', fault_id=fault.id)
            else:
                return redirect('simple_fault_list')
    else:
        form = FaultForm()
        
        # Pre-select user's depot if they have one
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            user_depot = Depots.objects.filter(code=user_profile.depot).first()
            if user_depot:
                form.fields['depot'].initial = user_depot
    
    context = {
        'form': form,
        'user_profile': user_profile,
        'page_title': 'Create New Fault',
    }
    
    return render(request, "fault_locator/create_fault.html", context)

@login_required
@fault_assignment_required
def simple_assign_fault(request, fault_id=None):
    """SIMPLIFIED: Easy fault assignment with available teams"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreman(user_profile) or is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)):
        messages.error(request, "You don't have permission to assign faults")
        return redirect('simple_fault_list')
    
    # Get fault if specified
    fault = None
    if fault_id:
        fault = get_object_or_404(Fault, id=fault_id)
        # Check if user can assign this fault
        if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
            user_depot = Depots.objects.filter(code=user_profile.depot).first()
            if fault.depot != user_depot:
                messages.error(request, "You can only assign faults at your depot")
                return redirect('simple_fault_list')
    
    if request.method == "POST":
        fault_id = request.POST.get('fault_id')
        team_id = request.POST.get('team_id')
        
        if not fault_id or not team_id:
            messages.error(request, "Please select both fault and team")
            return redirect('simple_assign_fault')
        
        fault = get_object_or_404(Fault, id=fault_id)
        team = get_object_or_404(FaultLocatorTeam, id=team_id)
        
        # Check if team has a device
        device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
        if not device_assignment:
            messages.error(request, f"Team '{team.name}' doesn't have a device assigned")
            return redirect('simple_assign_fault')
        
        # Check if fault is already assigned
        existing_assignment = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).first()
        if existing_assignment:
            messages.error(request, "This fault is already assigned to a team")
            return redirect('simple_fault_list')
        
        # Create assignment
        fault_assignment = FaultAssignment.objects.create(
            fault=fault,
            team=team,
            device=device_assignment.device
        )
        
        # Update fault status
        fault.status = 'assigned'
        fault.save()
        
        # Send notifications
        notify_fault_assignment(fault_assignment, request)
        
        messages.success(request, f"Fault assigned to team '{team.name}' with device '{device_assignment.device.serial_number}'")
        return redirect('simple_fault_list')
    
    # GET request - show assignment form
    
    # Get available faults for assignment
    available_faults = Fault.objects.filter(status='requested')
    
    # Filter faults based on user role
    if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
        user_depot = Depots.objects.filter(code=user_profile.depot).first()
        if user_depot:
            available_faults = available_faults.filter(depot=user_depot)
    
    # Get available teams (teams with devices)
    teams_with_devices = FaultLocatorDeviceAssignment.objects.select_related(
        'team', 'device'
    ).values_list('team', flat=True)
    
    available_teams = FaultLocatorTeam.objects.filter(
        id__in=teams_with_devices
    ).prefetch_related('members', 'faultlocatordeviceassignment_set__device')
    
    # Add team status info
    team_data = []
    for team in available_teams:
        device = team.faultlocatordeviceassignment_set.first().device
        current_assignment = FaultAssignment.objects.filter(
            team=team, 
            located_at__isnull=True
        ).first()
        
        status = 'available'
        status_text = 'Available'
        if current_assignment:
            status = 'busy'
            status_text = f'Working on: {current_assignment.fault.description[:30]}...'
        elif team.current_depot:
            status = 'deployed'
            status_text = f'Deployed to: {team.current_depot.depot}'
        
        team_data.append({
            'team': team,
            'device': device,
            'status': status,
            'status_text': status_text,
            'member_count': team.members.count(),
            'can_assign': status == 'available' or status == 'deployed',
        })
    
    context = {
        'user_profile': user_profile,
        'selected_fault': fault,
        'available_faults': available_faults,
        'team_data': team_data,
        'is_senior_foreman': is_senior_foreman(user_profile),
    }
    
    return render(request, "fault_locator/simple_assign_fault.html", context)

@login_required
@team_leader_required
def field_update(request, fault_id):
    """SIMPLIFIED: Mobile-friendly field status update"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    fault = get_object_or_404(Fault, id=fault_id)
    
    # Check if user can update this fault
    user_teams = user_profile.fault_locator_teams.all() if user_profile else []
    current_assignment = FaultAssignment.objects.filter(
        fault=fault, 
        located_at__isnull=True
    ).first()
    
    can_update = False
    if current_assignment and user_teams:
        can_update = any(team.id == current_assignment.team.id for team in user_teams)
    
    can_update = can_update or is_senior_foreman(user_profile)
    
    if not can_update:
        messages.error(request, "You don't have permission to update this fault")
        return redirect('simple_fault_list')
    
    if request.method == "POST":
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        old_status = fault.status
        
        if action == 'located':
            fault.status = 'located'
            fault.save()
            
            if current_assignment:
                current_assignment.located_at = timezone.now()
                current_assignment.save()
            
            notify_fault_status_update(fault, old_status, 'located', user_profile, request)
            messages.success(request, f"✅ Fault marked as LOCATED! Great work!")
            
        elif action == 'progress':
            # Just add a progress note without changing status
            messages.success(request, "Progress update recorded")
            
        elif action == 'need_help':
            # Escalate - notify senior foreperson
            senior_forepersons = UserProfile.objects.filter(
                designation__description__icontains='senior foreperson'
            )
            
            for senior_fp in senior_forepersons:
                if senior_fp.email:
                    message = f"Team needs assistance with fault: '{fault.description}' at {fault.depot.depot}. Notes: {notes}"
                    url = f"/fault_locator/faults/{fault.id}/"
                    notify_fault_locator_user(
                        user=senior_fp,
                        message=message,
                        notification_type="Team Assistance Request",
                        url=url,
                        fault_or_team_id=fault.id,
                        request=request
                    )
            
            messages.success(request, "🆘 Help request sent to senior forepersons")
        
        return redirect('field_update', fault_id=fault.id)
    
    # GET request - show update form
    context = {
        'fault': fault,
        'current_assignment': current_assignment,
        'user_profile': user_profile,
        'team': current_assignment.team if current_assignment else None,
        'device': current_assignment.device if current_assignment else None,
    }
    
    return render(request, "fault_locator/field_update.html", context)

@login_required
def team_overview(request):
    """SIMPLIFIED: Clean team overview with action buttons"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get teams based on user role with optimized queries
    teams = FaultLocatorTeam.objects.select_related(
        'team_leader', 
        'current_depot', 
        'assigned_by'
    ).prefetch_related(
        'members', 
        'faultlocatordeviceassignment_set__device'
    ).annotate(
        member_count=Count('members', distinct=True),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True), distinct=True)
    )
    
    # Role-based filtering
    if not is_senior_foreman(user_profile):
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            depot = get_user_depot(user_profile)
            if depot:
                teams = teams.filter(current_depot=depot)
    
    # Add extra info for each team
    team_data = []
    for team in teams:
        device_assignment = team.faultlocatordeviceassignment_set.first()
        
        status = 'no_device'
        status_class = 'text-gray-500'
        actions = []
        
        if device_assignment:
            if team.current_depot:
                status = 'deployed'
                status_class = 'text-green-600'
                if is_senior_foreman(user_profile):
                    actions.append({
                        'text': 'Recall',
                        'url': f'/fault_locator/teams/{team.id}/recall/',
                        'class': 'btn-warning btn-sm'
                    })
            else:
                status = 'available'
                status_class = 'text-blue-600'
                if is_senior_foreman(user_profile):
                    actions.append({
                        'text': 'Deploy',
                        'url': f'/fault_locator/teams/{team.id}/deploy/',
                        'class': 'btn-primary btn-sm'
                    })
        else:
            if can_manage_devices(user_profile):
                actions.append({
                    'text': 'Assign Device',
                    'url': f'/fault_locator/assign-device-to-team/?team_id={team.id}',
                    'class': 'btn-success btn-sm'
                })
        
        # Add manage action for authorized users
        if is_senior_foreman(user_profile) or can_manage_devices(user_profile):
            actions.append({
                'text': 'Manage',
                'url': f'/fault_locator/teams/{team.id}/edit/',
                'class': 'btn-outline-secondary btn-sm'
            })
        
        # Get actual member count to ensure accuracy
        actual_member_count = team.members.count()
        
        # Get actual active assignments count to ensure accuracy
        actual_active_assignments = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        ).count()
        
        # Get team leader display name with fallback
        team_leader_name = None
        if team.team_leader:
            leader_name = team.team_leader.get_full_name()
            if leader_name and leader_name.strip():
                team_leader_name = leader_name.strip()
            else:
                team_leader_name = team.team_leader.username or f"User {team.team_leader.id}"
        
        # Get members with proper display names and email handling
        team_members = []
        for member in team.members.all():
            # Handle member name
            member_name = member.get_full_name()
            if not member_name or member_name.strip() == '':
                member_name = member.username or f"User {member.id}"
            else:
                member_name = member_name.strip()
            
            # Handle member email
            member_email = 'No email'
            if member.email:
                # Fix "nan" display and other issues
                email_str = str(member.email).strip()
                if email_str and email_str.lower() != 'nan' and email_str != 'None':
                    member_email = email_str
            
            team_members.append({
                'name': member_name,
                'email': member_email,
                'id': member.id
            })
        
        # Enhanced deployment info
        deployment_info = {
            'assigned_at': team.assigned_at,
            'assigned_by': team.assigned_by.get_full_name() if team.assigned_by else None,
            'depot_name': team.current_depot.depot if team.current_depot else None,
            'depot_code': team.current_depot.code if team.current_depot else None,
        }
        
        # Add deployment status text
        if team.current_depot:
            deployment_info['status_text'] = f'Deployed to {team.current_depot.depot}'
        else:
            deployment_info['status_text'] = 'Not deployed'
        
        team_data.append({
            'team': team,
            'device': device_assignment.device if device_assignment else None,
            'status': status,
            'status_class': status_class,
            'location': team.current_depot.depot if team.current_depot else 'Base',
            'actions': actions,
            'actual_member_count': actual_member_count,
            'actual_active_assignments': actual_active_assignments,
            'team_leader_name': team_leader_name,
            'team_members': team_members,
            'deployment_info': deployment_info,
            # Add some additional computed fields for better display
            'has_device': device_assignment is not None,
            'is_deployed': team.current_depot is not None,
            'can_be_deployed': device_assignment is not None and team.current_depot is None,
            'device_serial': device_assignment.device.serial_number if device_assignment else None,
        })
    
    context = {
        'team_data': team_data,
        'user_profile': user_profile,
        'is_senior_foreman': is_senior_foreman(user_profile),
        'can_create_team': is_senior_foreman(user_profile) or can_manage_devices(user_profile),
        'total_teams': len(team_data),
        # Add some summary statistics
        'summary_stats': {
            'total_teams': len(team_data),
            'deployed_teams': sum(1 for item in team_data if item['is_deployed']),
            'teams_with_devices': sum(1 for item in team_data if item['has_device']),
            'available_for_deployment': sum(1 for item in team_data if item['can_be_deployed']),
            'total_members': sum(item['actual_member_count'] for item in team_data),
            'active_assignments': sum(item['actual_active_assignments'] for item in team_data),
        }
    }
    
    return render(request, "fault_locator/team_overview.html", context)

@login_required
def my_work(request):
    """SIMPLIFIED: Personal work view for field workers"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get user's teams
    user_teams = user_profile.fault_locator_teams.all() if user_profile else []
    
    if not user_teams.exists():
        # User is not in any fault locator team
        context = {
            'user_profile': user_profile,
            'no_team': True,
        }
        return render(request, "fault_locator/my_work.html", context)
    
    my_team = user_teams.first()  # Assuming user is in one team
    
    # Get current assignments
    current_assignments = FaultAssignment.objects.filter(
        team=my_team,
        located_at__isnull=True
    ).select_related('fault', 'device').order_by('-fault__priority', 'assigned_at')
    
    # Get completed assignments today
    today_completed = FaultAssignment.objects.filter(
        team=my_team,
        located_at__date=timezone.now().date()
    ).select_related('fault').order_by('-located_at')
    
    # Get recent completed assignments (last 7 days)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    recent_completed = FaultAssignment.objects.filter(
        team=my_team,
        located_at__gte=week_ago,
        located_at__date__lt=timezone.now().date()
    ).select_related('fault').order_by('-located_at')[:10]
    
    # Team device info
    device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=my_team).first()
    
    context = {
        'user_profile': user_profile,
        'my_team': my_team,
        'device': device_assignment.device if device_assignment else None,
        'current_location': my_team.current_depot.depot if my_team.current_depot else 'Base',
        'current_assignments': current_assignments,
        'today_completed': today_completed,
        'recent_completed': recent_completed,
        'stats': {
            'active_count': current_assignments.count(),
            'today_count': today_completed.count(),
            'week_count': recent_completed.count() + today_completed.count(),
        }
    }
    
    return render(request, "fault_locator/my_work.html", context)

# DEVICE MANAGEMENT VIEWS

@login_required
def device_list(request):
    """List all fault locator devices with management options"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not can_manage_devices(user_profile):
        messages.error(request, "You don't have permission to manage devices")
        return redirect('fault_locator_dashboard')
    
    # Get all devices with assignment status
    devices = FaultLocatorDevice.objects.all().order_by('serial_number')
    
    device_data = []
    for device in devices:
        assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
        current_fault = None
        
        if assignment:
            current_fault = FaultAssignment.objects.filter(
                device=device, 
                located_at__isnull=True
            ).first()
        
        device_data.append({
            'device': device,
            'assignment': assignment,
            'team': assignment.team if assignment else None,
            'current_fault': current_fault,
            'status': 'in_use' if current_fault else ('assigned' if assignment else 'available'),
        })
    
    context = {
        'device_data': device_data,
        'user_profile': user_profile,
        'is_senior_foreman': is_senior_foreman(user_profile),
        'total_devices': len(device_data),
    }
    
    return render(request, "fault_locator/device_list.html", context)

@login_required
@device_management_required
def create_device(request):
    """Create a new fault locator device"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not can_manage_devices(user_profile):
        messages.error(request, "You don't have permission to create devices")
        return redirect('fault_locator_dashboard')
    
    if request.method == "POST":
        form = FaultLocatorDeviceForm(request.POST)
        if form.is_valid():
            device = form.save()
            messages.success(request, f"Device '{device.serial_number}' created successfully!")
            return redirect('device_list')
    else:
        form = FaultLocatorDeviceForm()
    
    context = {
        'form': form,
        'user_profile': user_profile,
        'page_title': 'Create New Device',
    }
    
    return render(request, "fault_locator/create_device.html", context)

@login_required
def edit_device(request, device_id):
    """Edit an existing fault locator device"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not can_manage_devices(user_profile):
        messages.error(request, "You don't have permission to edit devices")
        return redirect('fault_locator_dashboard')
    
    device = get_object_or_404(FaultLocatorDevice, id=device_id)
    
    if request.method == "POST":
        form = FaultLocatorDeviceForm(request.POST, instance=device)
        if form.is_valid():
            device = form.save()
            messages.success(request, f"Device '{device.serial_number}' updated successfully!")
            return redirect('device_list')
    else:
        form = FaultLocatorDeviceForm(instance=device)
    
    # Check if device is currently in use
    current_assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
    active_fault = FaultAssignment.objects.filter(device=device, located_at__isnull=True).first()
    
    context = {
        'form': form,
        'device': device,
        'current_assignment': current_assignment,
        'active_fault': active_fault,
        'user_profile': user_profile,
        'page_title': f'Edit Device: {device.serial_number}',
        'can_delete': not current_assignment and not active_fault,
    }
    
    return render(request, "fault_locator/edit_device.html", context)

@login_required
def device_detail(request, device_id):
    """View detailed information about a device"""
    device = get_object_or_404(FaultLocatorDevice, id=device_id)
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get device assignment history
    assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
    
    # Get fault history for this device
    fault_history = FaultAssignment.objects.filter(device=device).select_related(
        'fault', 'team'
    ).order_by('-assigned_at')[:10]
    
    # Get current active fault
    current_fault = FaultAssignment.objects.filter(
        device=device, 
        located_at__isnull=True
    ).first()
    
    context = {
        'device': device,
        'assignment': assignment,
        'current_fault': current_fault,
        'fault_history': fault_history,
        'user_profile': user_profile,
        'can_edit': can_manage_devices(user_profile),
    }
    
    return render(request, "fault_locator/device_detail.html", context)

@login_required
def assign_device_to_team(request):
    """Assign a device to a team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not can_manage_devices(user_profile):
        messages.error(request, "You don't have permission to assign devices")
        return redirect('fault_locator_dashboard')
    
    team_id = request.GET.get('team_id')
    
    if request.method == "POST":
        form = SeniorForepersonDeviceAssignmentForm(request.POST, user=user_profile)
        if form.is_valid():
            assignment = form.save()
            
            # Notify team members
            team = assignment.team
            for member in team.members.all():
                if member.email:
                    message = f"Your team '{team.name}' has been assigned device '{assignment.device.serial_number}'"
                    url = f"/fault_locator/teams/{team.id}/"
                    notify_fault_locator_user(
                        user=member,
                        message=message,
                        notification_type="Device Assignment",
                        url=url,
                        fault_or_team_id=team.id,
                        request=request
                    )
            
            messages.success(request, f"Device '{assignment.device.serial_number}' assigned to team '{team.name}'")
            return redirect('team_overview')
    else:
        initial_data = {}
        if team_id:
            initial_data['team'] = team_id
        form = SeniorForepersonDeviceAssignmentForm(initial=initial_data, user=user_profile)
    
    context = {
        'form': form,
        'user_profile': user_profile,
        'page_title': 'Assign Device to Team',
    }
    
    return render(request, "fault_locator/assign_device_to_team.html", context)

@login_required
def unassign_device(request, device_id):
    """Remove device assignment from team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not can_manage_devices(user_profile):
        messages.error(request, "You don't have permission to unassign devices")
        return redirect('fault_locator_dashboard')
    
    device = get_object_or_404(FaultLocatorDevice, id=device_id)
    assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
    
    if not assignment:
        messages.error(request, "Device is not currently assigned to any team")
        return redirect('device_list')
    
    # Check if device is being used for active fault
    active_fault = FaultAssignment.objects.filter(device=device, located_at__isnull=True).first()
    if active_fault:
        messages.error(request, f"Cannot unassign device - it's currently being used for fault: {active_fault.fault.description}")
        return redirect('device_list')
    
    if request.method == "POST":
        team = assignment.team
        assignment.delete()
        
        # Notify team members
        for member in team.members.all():
            if member.email:
                message = f"Device '{device.serial_number}' has been removed from your team '{team.name}'"
                url = f"/fault_locator/teams/{team.id}/"
                notify_fault_locator_user(
                    user=member,
                    message=message,
                    notification_type="Device Removal",
                    url=url,
                    fault_or_team_id=team.id,
                    request=request
                )
        
        messages.success(request, f"Device '{device.serial_number}' unassigned from team '{team.name}'")
        return redirect('device_list')
    
    context = {
        'device': device,
        'assignment': assignment,
        'user_profile': user_profile,
    }
    
    return render(request, "fault_locator/unassign_device.html", context)

# TEAM MANAGEMENT VIEWS

@login_required
@team_management_required
def create_team(request):
    """Create a new fault locator team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
        messages.error(request, "You don't have permission to create teams")
        return redirect('fault_locator_dashboard')
    
    if request.method == "POST":
        form = FaultLocatorTeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            
            # Notify team members
            for member in team.members.all():
                if member.email:
                    message = f"You have been added to fault locator team '{team.name}'"
                    url = f"/fault_locator/teams/{team.id}/"
                    notify_fault_locator_user(
                        user=member,
                        message=message,
                        notification_type="Team Assignment",
                        url=url,
                        fault_or_team_id=team.id,
                        request=request
                    )
            
            messages.success(request, f"Team '{team.name}' created successfully with {team.members.count()} members!")
            return redirect('team_overview')
    else:
        form = FaultLocatorTeamForm()
    
    context = {
        'form': form,
        'user_profile': user_profile,
        'page_title': 'Create New Team',
    }
    
    return render(request, "fault_locator/create_team.html", context)

@login_required
def edit_team(request, team_id):
    """Edit an existing fault locator team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
        messages.error(request, "You don't have permission to edit teams")
        return redirect('fault_locator_dashboard')
    
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    
    if request.method == "POST":
        # Handle name change
        if 'update_name' in request.POST:
            name_form = FaultLocatorTeamNameForm(request.POST, instance=team)
            if name_form.is_valid():
                team = name_form.save()
                messages.success(request, f"Team name updated to '{team.name}'")
                return redirect('edit_team', team_id=team.id)
        
        # Handle member addition
        elif 'add_member' in request.POST:
            add_form = AddTeamMemberForm(request.POST)
            if add_form.is_valid():
                member = add_form.cleaned_data['member']
                if member not in team.members.all():
                    team.members.add(member)
                    
                    # Notify new member
                    if member.email:
                        message = f"You have been added to fault locator team '{team.name}'"
                        url = f"/fault_locator/teams/{team.id}/"
                        notify_fault_locator_user(
                            user=member,
                            message=message,
                            notification_type="Team Assignment",
                            url=url,
                            fault_or_team_id=team.id,
                            request=request
                        )
                    
                    messages.success(request, f"{member.get_full_name()} added to team")
                else:
                    messages.warning(request, f"{member.get_full_name()} is already in this team")
                return redirect('edit_team', team_id=team.id)
        
        # Handle member removal
        elif 'remove_member' in request.POST:
            member_id = request.POST.get('member_id')
            if member_id:
                member = get_object_or_404(UserProfile, id=member_id)
                team.members.remove(member)
                
                # Notify removed member
                if member.email:
                    message = f"You have been removed from fault locator team '{team.name}'"
                    url = "/fault_locator/"
                    notify_fault_locator_user(
                        user=member,
                        message=message,
                        notification_type="Team Removal",
                        url=url,
                        fault_or_team_id=team.id,
                        request=request
                    )
                
                messages.success(request, f"{member.get_full_name()} removed from team")
                return redirect('edit_team', team_id=team.id)
    
    # Initialize forms
    name_form = FaultLocatorTeamNameForm(instance=team)
    add_form = AddTeamMemberForm()
    
    # Get device assignment
    device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
    
    # Get current assignments
    current_assignments = FaultAssignment.objects.filter(
        team=team, 
        located_at__isnull=True
    ).select_related('fault')
    
    context = {
        'team': team,
        'name_form': name_form,
        'add_form': add_form,
        'device_assignment': device_assignment,
        'current_assignments': current_assignments,
        'user_profile': user_profile,
        'can_delete': not current_assignments.exists() and not device_assignment,
        'page_title': f'Edit Team: {team.name}',
    }
    
    return render(request, "fault_locator/edit_team.html", context)

@login_required
def delete_team(request, team_id):
    """Delete a fault locator team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior forepersons can delete teams")
        return redirect('fault_locator_dashboard')
    
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    
    # Check if team has active assignments or device
    device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
    active_faults = FaultAssignment.objects.filter(team=team, located_at__isnull=True).exists()
    
    if device_assignment or active_faults:
        messages.error(request, "Cannot delete team - it has active assignments or assigned devices")
        return redirect('edit_team', team_id=team.id)
    
    if request.method == "POST":
        team_name = team.name
        
        # Notify team members
        for member in team.members.all():
            if member.email:
                message = f"Fault locator team '{team_name}' has been dissolved"
                url = "/fault_locator/"
                notify_fault_locator_user(
                    user=member,
                    message=message,
                    notification_type="Team Dissolution",
                    url=url,
                    fault_or_team_id=team.id,
                    request=request
                )
        
        team.delete()
        messages.success(request, f"Team '{team_name}' deleted successfully")
        return redirect('team_overview')
    
    context = {
        'team': team,
        'user_profile': user_profile,
    }
    
    return render(request, "fault_locator/delete_team.html", context)

# TEAM DEPLOYMENT VIEWS

@login_required
def deploy_team(request, team_id=None):
    """Deploy a team to a depot"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior forepersons can deploy teams")
        return redirect('fault_locator_dashboard')
    
    team = None
    if team_id:
        team = get_object_or_404(FaultLocatorTeam, id=team_id)
        
        # Check if team already deployed
        if team.current_depot:
            messages.warning(request, f"Team '{team.name}' is already deployed to {team.current_depot.depot}")
            return redirect('team_overview')
        
        # Check if team has a device
        device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
        if not device_assignment:
            messages.error(request, f"Team '{team.name}' must have a device assigned before deployment")
            return redirect('team_overview')
    
    if request.method == "POST":
        form = TeamDeploymentForm(request.POST)
        if form.is_valid():
            deployment = form.save(commit=False)
            deployment.deployed_by = user_profile
            deployment.save()
            
            # Update team's current depot
            team = deployment.team
            team.current_depot = deployment.depot
            team.assigned_at = deployment.deployed_at
            team.assigned_by = user_profile
            team.save()
            
            # Send notifications
            notify_team_deployment(deployment, request)
            
            messages.success(request, f"Team '{team.name}' deployed to {deployment.depot.depot}")
            return redirect('team_overview')
    else:
        initial_data = {}
        if team:
            initial_data['team'] = team
        form = TeamDeploymentForm(initial=initial_data)
    
    context = {
        'form': form,
        'selected_team': team,
        'user_profile': user_profile,
        'page_title': 'Deploy Team to Depot',
    }
    
    return render(request, "fault_locator/deploy_team.html", context)

@login_required
def recall_team(request, team_id):
    """Recall a team from depot deployment"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not is_senior_foreman(user_profile):
        messages.error(request, "Only senior forepersons can recall teams")
        return redirect('fault_locator_dashboard')
    
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    
    if not team.current_depot:
        messages.warning(request, f"Team '{team.name}' is not currently deployed")
        return redirect('team_overview')
    
    # Check for active assignments
    active_assignments = FaultAssignment.objects.filter(team=team, located_at__isnull=True)
    
    if request.method == "POST":
        if active_assignments.exists() and not request.POST.get('force_recall'):
            messages.error(request, "Team has active fault assignments. Use force recall if necessary.")
            return redirect('recall_team', team_id=team.id)
        
        # Find current deployment
        current_deployment = TeamDeployment.objects.filter(
            team=team,
            recalled_at__isnull=True
        ).first()
        
        if current_deployment:
            current_deployment.recalled_at = timezone.now()
            current_deployment.save()
        
        # Update team status
        depot_name = team.current_depot.depot
        team.current_depot = None
        team.assigned_at = None
        team.assigned_by = None
        team.save()
        
        # Notify team members
        for member in team.members.all():
            if member.email:
                message = f"Your team '{team.name}' has been recalled from {depot_name}"
                url = f"/fault_locator/teams/{team.id}/"
                notify_fault_locator_user(
                    user=member,
                    message=message,
                    notification_type="Team Recall",
                    url=url,
                    fault_or_team_id=team.id,
                    request=request
                )
        
        messages.success(request, f"Team '{team.name}' recalled from {depot_name}")
        return redirect('team_overview')
    
    context = {
        'team': team,
        'active_assignments': active_assignments,
        'user_profile': user_profile,
    }
    
    return render(request, "fault_locator/recall_team.html", context)

# ADVANCED FAULT ASSIGNMENT

@login_required
def advanced_fault_assignment(request):
    """Advanced fault assignment with bulk operations and filtering"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreman(user_profile) or is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)):
        messages.error(request, "You don't have permission to assign faults")
        return redirect('fault_locator_dashboard')
    
    # Get unassigned faults
    unassigned_faults = Fault.objects.filter(status='requested').select_related('depot')
    
    # Role-based filtering
    if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None) and not is_senior_foreman(user_profile):
        user_depot = Depots.objects.filter(code=user_profile.depot).first()
        if user_depot:
            unassigned_faults = unassigned_faults.filter(depot=user_depot)
    
    # Apply filters
    depot_filter = request.GET.get('depot')
    priority_filter = request.GET.get('priority')
    
    if depot_filter:
        unassigned_faults = unassigned_faults.filter(depot_id=depot_filter)
    
    if priority_filter:
        unassigned_faults = unassigned_faults.filter(priority=priority_filter)
    
    # Get available teams with devices
    available_teams = FaultLocatorTeam.objects.filter(
        faultlocatordeviceassignment__isnull=False
    ).prefetch_related('members', 'faultlocatordeviceassignment_set__device')
    
    # Add team availability info
    team_data = []
    for team in available_teams:
        device = team.faultlocatordeviceassignment_set.first().device
        current_assignments_count = FaultAssignment.objects.filter(
            team=team, 
            located_at__isnull=True
        ).count()
        
        status = 'available'
        if current_assignments_count > 0:
            status = f'{current_assignments_count} active'
        elif not team.current_depot:
            status = 'not deployed'
        
        team_data.append({
            'team': team,
            'device': device,
            'status': status,
            'current_assignments': current_assignments_count,
            'location': team.current_depot.depot if team.current_depot else 'Base',
            'can_assign': True,  # Can assign even if busy for urgent faults
        })
    
    # Handle bulk assignment
    if request.method == "POST":
        fault_ids = request.POST.getlist('fault_ids')
        team_id = request.POST.get('team_id')
        
        if not fault_ids or not team_id:
            messages.error(request, "Please select faults and a team")
            return redirect('advanced_fault_assignment')
        
        team = get_object_or_404(FaultLocatorTeam, id=team_id)
        device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
        
        if not device_assignment:
            messages.error(request, f"Team '{team.name}' doesn't have a device assigned")
            return redirect('advanced_fault_assignment')
        
        assigned_count = 0
        for fault_id in fault_ids:
            fault = get_object_or_404(Fault, id=fault_id)
            
            # Check if fault is already assigned
            existing_assignment = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).first()
            if existing_assignment:
                continue
            
            # Create assignment
            fault_assignment = FaultAssignment.objects.create(
                fault=fault,
                team=team,
                device=device_assignment.device
            )
            
            # Update fault status
            fault.status = 'assigned'
            fault.save()
            
            # Send notifications
            notify_fault_assignment(fault_assignment, request)
            assigned_count += 1
        
        if assigned_count > 0:
            messages.success(request, f"{assigned_count} fault(s) assigned to team '{team.name}'")
        else:
            messages.warning(request, "No faults were assigned (they may already be assigned)")
        
        return redirect('advanced_fault_assignment')
    
    # Get filter options
    depot_options = Depots.objects.all()
    if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None) and not is_senior_foreman(user_profile):
        user_depot = Depots.objects.filter(code=user_profile.depot).first()
        if user_depot:
            depot_options = [user_depot]
    
    context = {
        'unassigned_faults': unassigned_faults,
        'team_data': team_data,
        'depot_options': depot_options,
        'priority_options': Fault._meta.get_field('priority').choices,
        'depot_filter': depot_filter,
        'priority_filter': priority_filter,
        'user_profile': user_profile,
        'is_senior_foreman': is_senior_foreman(user_profile),
        'total_unassigned': unassigned_faults.count(),
    }
    
    return render(request, "fault_locator/advanced_fault_assignment.html", context)

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

# Keep existing utility functions for backward compatibility
def is_foreperson(user_profile):
    """Legacy function - check if user profile belongs to any foreperson"""
    return is_depot_foreperson_by_designation(user_profile) or is_senior_foreman(user_profile)

def has_fault_locator_permissions(user_profile):
    """Check if user has any fault locator system permissions"""
    role = get_user_fault_locator_role(user_profile)
    return role is not None
