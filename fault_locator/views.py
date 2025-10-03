from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, ExpressionWrapper, DurationField, Sum, Q, Count
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import datetime
from datetime import timedelta
from decouple import config

from it.users.helpers import DEPOTS
from .models import *
from .forms import FaultForm, FaultLocatorDeviceForm, FaultLocatorTeamForm, FaultLocatorTeamNameForm, AddTeamMemberForm, AssignDeviceToTeamForm, AssignFaultForm, TeamDeploymentForm, SeniorForepersonDeviceAssignmentForm, QuickFaultReportForm, TeamDepotAssignmentForm, FaultPriorityForm
from it.users.models import UserProfile, Notification
from it.users.views import ms_exhange_send_html
from .central_roles import (
    FaultLocatorRoleManager,
    is_senior_foreman,
    is_depot_foreperson,
    is_team_leader,
    is_team_member,
    is_fault_reporter,
    can_report_faults,
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

# Notification Functions
def notify_fault_locator_user(user, message, notification_type, url, fault_or_team_id, request):
    """Send notification to a fault locator user - Creates database notification and sends email"""
    try:
        # Create in-app notification
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            url=url,
            notification_id=str(fault_or_team_id)
        )
        
        # Send email notification if user has email
        if user.email:
            # Build full URL for email
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            redirect_url = f"{protocol}://{domain}{url}"
            
            # Use time-based greeting
            hour = datetime.datetime.now().hour
            greetings = {
                (0, 4): "Good night!",
                (5, 11): "Good morning!",
                (12, 16): "Good afternoon!",
                (17, 20): "Good evening!",
                (21, 23): "Good night!"
            }
            greeting = next((msg for (start, end), msg in greetings.items() if start <= hour <= end), "Hello!")
            
            subject = f"{greeting} - Fault Locator: {notification_type}"
            
            response = ms_exhange_send_html(
                subject=subject,
                to_recipients=[user.email],
                cc_recipients=[],
                template='email/email_template.html',
                kwargs={"kwargs": {
                    "redirect_url": redirect_url,
                    "type": notification_type,
                    "user_fullname": user.get_full_name(),
                    "message": message
                }}
            )
            
            # Log email response for debugging
            if hasattr(response, 'status_code') and response.status_code != 200:
                print(f"Email notification failed for {user.email}: {response.content}")
            
    except Exception as e:
        # Log error but don't break the workflow
        print(f"Notification error for user {user.id}: {e}")

def notify_fault_assignment(fault_assignment, request):
    """Notify team members when a fault is assigned to their team"""
    fault = fault_assignment.fault
    team = fault_assignment.team
    device = fault_assignment.device
    
    url = f"/fault_locator/faults/{fault.id}/"
    message = f"Fault #{fault.id} has been assigned to your team '{team.name}'. Location: {fault.location_description}. Gear: {device.serial_number}"
    notification_type = "Fault Assignment"
    
    # Notify all team members
    for member in team.members.all():
        notify_fault_locator_user(member, message, notification_type, url, fault.id, request)
    
    # Notify depot foreperson if different from assigner
    depot_forepersons = UserProfile.objects.filter(
        depot=fault.depot.code,
        designation__description__icontains='foreperson'
    ).exclude(id=request.user.id)
    
    depot_message = f"Fault #{fault.id} has been assigned to team '{team.name}' at your depot."
    for foreperson in depot_forepersons:
        notify_fault_locator_user(foreperson, depot_message, notification_type, url, fault.id, request)

def notify_fault_status_update(fault, old_status, new_status, updated_by, request):
    """Notify relevant users when fault status is updated"""
    url = f"/fault_locator/faults/{fault.id}/"
    message = f"Fault #{fault.id} status updated from '{old_status}' to '{new_status}' by {updated_by.get_full_name()}."
    notification_type = "Fault Status Update"
    
    # Notify current assignment team members
    current_assignment = FaultAssignment.objects.filter(
        fault=fault, 
        located_at__isnull=True
    ).first()
    
    if current_assignment:
        for member in current_assignment.team.members.all():
            if member.id != updated_by.id:  # Don't notify the person who made the update
                notify_fault_locator_user(member, message, notification_type, url, fault.id, request)
    
    # Notify depot foreperson
    depot_forepersons = UserProfile.objects.filter(
        depot=fault.depot.code,
        designation__description__icontains='foreperson'
    ).exclude(id=updated_by.id)
    
    for foreperson in depot_forepersons:
        notify_fault_locator_user(foreperson, message, notification_type, url, fault.id, request)
    
    # If fault is located, notify senior forepersons
    if new_status == 'located':
        senior_forepersons = UserProfile.objects.filter(
            designation__description__icontains='senior foreperson'
        ).exclude(id=updated_by.id)
        
        located_message = f"✅ Fault #{fault.id} has been located by team '{current_assignment.team.name if current_assignment else 'Unknown'}'."
        for senior in senior_forepersons:
            notify_fault_locator_user(senior, located_message, "Fault Located", url, fault.id, request)

def notify_team_deployment(deployment, request):
    """Notify team members when they are deployed to a depot"""
    team = deployment.team
    depot = deployment.depot
    
    url = f"/fault_locator/team_overview/"
    message = f"Your team '{team.name}' has been deployed to depot '{depot.depot}' by {deployment.deployed_by.get_full_name()}."
    notification_type = "Team Deployment"
    
    # Notify all team members
    for member in team.members.all():
        notify_fault_locator_user(member, message, notification_type, url, team.id, request)
    
    # Notify depot foreperson
    depot_forepersons = UserProfile.objects.filter(
        depot=depot.code,
        designation__description__icontains='foreperson'
    ).exclude(id=request.user.id)
    
    depot_message = f"Team '{team.name}' has been deployed to your depot by {deployment.deployed_by.get_full_name()}."
    for foreperson in depot_forepersons:
        notify_fault_locator_user(foreperson, depot_message, notification_type, url, team.id, request)

def notify_team_recall(team, recalled_by, request):
    """Notify team members when they are recalled from a depot"""
    if not team.current_depot:
        return
    
    depot = team.current_depot
    url = f"/fault_locator/team_overview/"
    message = f"Your team '{team.name}' has been recalled from depot '{depot.depot}' by {recalled_by.get_full_name()}."
    notification_type = "Team Recall"
    
    # Notify all team members
    for member in team.members.all():
        notify_fault_locator_user(member, message, notification_type, url, team.id, request)
    
    # Notify depot foreperson
    depot_forepersons = UserProfile.objects.filter(
        depot=depot.code,
        designation__description__icontains='foreperson'
    ).exclude(id=recalled_by.id)
    
    depot_message = f"Team '{team.name}' has been recalled from your depot by {recalled_by.get_full_name()}."
    for foreperson in depot_forepersons:
        notify_fault_locator_user(foreperson, depot_message, notification_type, url, team.id, request)

def notify_high_priority_fault(fault, request):
    """Notify senior forepersons about high priority faults"""
    if fault.priority >= 3:
        url = f"/fault_locator/faults/{fault.id}/"
        message = f"🚨 HIGH PRIORITY fault #{fault.id} reported at {fault.depot.depot}: {fault.description}"
        notification_type = "High Priority Fault"
        
        # Notify all senior forepersons
        senior_forepersons = UserProfile.objects.filter(
            designation__description__icontains='senior foreperson'
        )
        
        for senior in senior_forepersons:
            notify_fault_locator_user(senior, message, notification_type, url, fault.id, request)
        
        # Also notify depot forepersons at the affected depot
        depot_forepersons = UserProfile.objects.filter(
            depot=fault.depot.code,
            designation__description__icontains='foreperson'
        ).exclude(id=request.user.id)
        
        for foreperson in depot_forepersons:
            notify_fault_locator_user(foreperson, message, notification_type, url, fault.id, request)

def notify_device_assignment(device_assignment, request):
    """Notify team members when gear is assigned to their team"""
    team = device_assignment.team
    device = device_assignment.device
    
    url = f"/fault_locator/team_overview/"
    message = f"Your team '{team.name}' has been assigned gear '{device.serial_number}'. You can now be deployed for field work."
    notification_type = "Gear Assignment"
    
    # Notify all team members
    for member in team.members.all():
        notify_fault_locator_user(member, message, notification_type, url, team.id, request)

def notify_device_removal(team, device, removed_by, request):
    """Notify team members when gear is removed from their team"""
    url = f"/fault_locator/team_overview/"
    message = f"Gear '{device.serial_number}' has been removed from your team '{team.name}' by {removed_by.get_full_name()}."
    notification_type = "Gear Removal"
    
    # Notify all team members
    for member in team.members.all():
        notify_fault_locator_user(member, message, notification_type, url, team.id, request)

def notify_team_member_addition(team, new_member, added_by, request):
    """Notify new team member when they are added to a team"""
    url = f"/fault_locator/team_overview/"
    message = f"You have been added to fault locator team '{team.name}' by {added_by.get_full_name()}."
    notification_type = "Team Assignment"
    
    notify_fault_locator_user(new_member, message, notification_type, url, team.id, request)

def notify_team_member_removal(team, removed_member, removed_by, request):
    """Notify team member when they are removed from a team"""
    url = f"/fault_locator/"
    message = f"You have been removed from fault locator team '{team.name}' by {removed_by.get_full_name()}."
    notification_type = "Team Removal"
    
    notify_fault_locator_user(removed_member, message, notification_type, url, team.id, request)

def notify_assistance_request(fault, requesting_team, notes, request):
    """Notify senior forepersons when a team requests assistance"""
    url = f"/fault_locator/faults/{fault.id}/"
    message = f"🆘 Team '{requesting_team.name}' needs assistance with fault #{fault.id} at {fault.depot.depot}."
    if notes:
        message += f" Notes: {notes}"
    notification_type = "Team Assistance Request"
    
    # Notify all senior forepersons
    senior_forepersons = UserProfile.objects.filter(
        designation__description__icontains='senior foreperson'
    )
    
    for senior in senior_forepersons:
        notify_fault_locator_user(senior, message, notification_type, url, fault.id, request)
# SIMPLIFIED MAIN VIEWS

@login_required
def fault_locator_dashboard(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        user_role = None
        is_senior = is_senior_foreman(user_profile)
        is_depot_fp = is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)
        is_team_lead = is_team_leader(user_profile)
        is_team_member = is_team_member(user_profile)
        is_fault_rep = is_fault_reporter(user_profile)
        user_depot = user_profile.depot if user_profile and hasattr(user_profile, 'depot') else None
        user_can_manage_devices = can_manage_devices(user_profile)
        user_role_display = FaultLocatorRoleManager.get_user_role_display(user_profile)
        
        # All dashboard logic
        context = {
            'user_profile': user_profile,
            'user_role': user_role,
            'user_role_display': user_role_display,
            'is_senior_foreman': is_senior,
            'is_depot_foreperson': is_depot_fp,
            'is_team_leader': is_team_lead,
            'is_team_member': is_team_member,
            'is_fault_reporter': is_fault_rep,
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
                'is_fault_reporter': is_fault_rep,
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
                        resolution_rate = 0 if total_faults == 0 else int((depot_faults.filter(status='closed').count() / total_faults) * 100);
                        
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
            if can_manage_devices(user_profile):
                accessible_functions['device_list'] = {
                    'title': 'Gear Management',
                    'description': 'View, create, edit, and assign all fault locator gear.',
                    'url_name': 'device_list',
                    'icon': '📱'
                }
            if can_create_teams(user_profile):
                accessible_functions['team_overview'] = {
                    'title': 'Team Management',
                    'description': 'Create, edit, and manage fault locator teams and their members.',
                    'url_name': 'team_overview',
                    'icon': '👥'
                }

        if is_senior:
            accessible_functions['senior_foreman_dashboard'] = {
                'title': 'Senior Foreman Dashboard',
                'description': 'Complete management interface for team deployment, gear assignment, and performance monitoring.',
                'url_name': 'senior_foreman_dashboard',
                'icon': '📊'
            }
            if can_deploy_teams(user_profile):
                accessible_functions['deploy_team'] = {
                    'title': 'Deploy Teams',
                    'description': 'Deploy available teams to various depot locations.',
                    'url_name': 'deploy_team',
                    'icon': '🚀'
                }
            if can_assign_faults(user_profile):
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
            if can_assign_faults(user_profile):
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

        # Fault Reporter Functions  
        if is_fault_rep:
            accessible_functions['fault_reporter_dashboard'] = {
                'title': 'My Fault Reports',
                'description': 'View and manage faults you have reported.',
                'url_name': 'fault_reporter_dashboard',
                'icon': '📋'
            }
            accessible_functions['bulk_fault_report'] = {
                'title': 'Bulk Report Faults',
                'description': 'Report multiple faults at once for efficiency.',
                'url_name': 'bulk_fault_report',
                'icon': '📄'
            }

        # Only show functions user can access
        context['accessible_functions'] = [
            func for func in accessible_functions.values()
            if func['url_name'] == 'quick_fault_report'
            or (func['url_name'] == 'fault_reporter_dashboard' and is_fault_rep)
            or (func['url_name'] == 'bulk_fault_report' and is_fault_rep)
            or (func['url_name'] == 'my_work' and is_team_member)
            or (func['url_name'] == 'device_list' and can_manage_devices(user_profile))
            or (func['url_name'] == 'team_overview' and can_create_teams(user_profile))
            or (func['url_name'] == 'senior_foreman_dashboard' and is_senior)
            or (func['url_name'] == 'deploy_team' and can_deploy_teams(user_profile))
            or (func['url_name'] == 'advanced_fault_assignment' and can_assign_faults(user_profile))
            or (func['url_name'] == 'simple_fault_list' and (is_senior or is_depot_fp))
            or (func['url_name'] == 'assign_faults' and can_assign_faults(user_profile))
        ]

        # MY ACTIONS - What can I do right now?
        my_actions = []
        
        # For Fault Reporters - dedicated fault reporting functionality
        if is_fault_rep:
            # Count faults reported by this user in the last 24 hours
            from datetime import timedelta
            yesterday = timezone.now() - timedelta(days=1)
            recent_reports = Fault.objects.filter(
                reported_by=user_profile,
                reported_at__gte=yesterday
            ).count()
            
            # Count pending faults reported by this user
            pending_reports = Fault.objects.filter(
                reported_by=user_profile,
                status='requested'
            ).count()
            
            my_actions.append({
                'title': 'Report New Fault',
                'description': f'Quick fault reporting - {recent_reports} reports today',
                'url': '/fault_locator/quick-report/',
                'priority': 'medium',
                'type': 'fault_reporting',
                'count': recent_reports
            })
            
            if pending_reports > 0:
                my_actions.append({
                    'title': f'Follow Up on {pending_reports} Pending Report{"s" if pending_reports != 1 else ""}',
                    'description': 'Your reported faults awaiting assignment',
                    'url': '/fault_locator/my-reports/',
                    'priority': 'high',
                    'type': 'follow_up',
                    'count': pending_reports
                })
        
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
                    'description': 'Teams with gear ready for deployment',
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
                'Active Gear': FaultLocatorDeviceAssignment.objects.count(),
            }
        elif is_depot_fp and user_depot:
            # Depot-specific stats
            context['quick_stats'] = {
                'My Depot Faults': Fault.objects.filter(depot=user_depot).count(),
                'Pending Assignment': Fault.objects.filter(depot=user_depot, status='requested').count(),
                'In Progress': Fault.objects.filter(depot=user_depot, status='assigned').count(),
                'Teams at Depot': FaultLocatorTeam.objects.filter(current_depot=user_depot).count(),
            }
        elif is_fault_rep:
            # Fault reporter stats
            my_reported_faults = Fault.objects.filter(reported_by=user_profile)
            from datetime import timedelta
            this_week = timezone.now() - timedelta(days=7)
            this_month = timezone.now() - timedelta(days=30)
            
            context['quick_stats'] = {
                'My Total Reports': my_reported_faults.count(),
                'Pending Assignment': my_reported_faults.filter(status='requested').count(),
                'In Progress': my_reported_faults.filter(status='assigned').count(),
                'Completed': my_reported_faults.filter(status='closed').count(),
                'This Week': my_reported_faults.filter(reported_at__gte=this_week).count(),
                'This Month': my_reported_faults.filter(reported_at__gte=this_month).count(),
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
        elif is_fault_rep:
            # Fault reporter activity - my reported faults
            my_recent_faults = Fault.objects.filter(
                reported_by=user_profile
            ).order_by('-reported_at')[:5]
            for fault in my_recent_faults:
                recent_activity.append({
                    'description': f'Reported: {fault.description}',
                    'location': fault.depot.depot,
                    'time': fault.reported_at,
                    'status': fault.get_status_display(),
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dashboard error: {e}")
        messages.error(request, "An error occurred loading the dashboard.")
    return redirect('fault_locator:simple_fault_list')

@login_required
def simple_fault_list(request):
    try:
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
        
        # Order by priority: VVIP (descending), voltage level (descending), clients affected (descending), date reported (oldest first for urgency), then priority level (highest first)
        faults = faults.order_by(
            '-vvip',                 # VVIP faults first (trumps all other criteria)
            '-voltage',              # Higher voltage first (400kV before 11kV)
            '-clients_affected',     # More clients affected first  
            'reported_at',           # Oldest first (for urgency - older faults need attention)
            '-priority'              # Higher priority first (Critical before Low)
        )
        
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fault list error: {e}")
        messages.error(request, "An error occurred loading the fault list.")
    return redirect('fault_locator:fault_locator_dashboard')

@login_required
def field_update(request, fault_id):
    """Minimal fault detail/update view used by multiple templates and URLs.
    Renders fault_location_update page and allows safe updates to location details when permitted.
    """
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        fault = get_object_or_404(Fault, id=fault_id)

        # Determine permissions
        can_edit = is_senior_foreman(user_profile) or is_depot_foreperson(user_profile, fault.depot)
        current_assignment = FaultAssignment.objects.filter(
            fault=fault, located_at__isnull=True
        ).select_related('team').first()

        in_assigned_team = False
        if current_assignment and user_profile:
            in_assigned_team = (
                current_assignment.team.members.filter(id=user_profile.id).exists()
                or current_assignment.team.team_leader_id == user_profile.id
            )

        # Handle basic POST to save location details only
        if request.method == 'POST':
            location_details = request.POST.get('location_details', '')
            if (can_edit or in_assigned_team):
                try:
                    fault.location_details = location_details or ''
                    fault.save(update_fields=['location_details'])
                    messages.success(request, 'Location details updated.')
                except Exception as e:
                    messages.error(request, 'Failed to update location details.')
                return redirect('fault_locator:field_update', fault_id=fault.id)
            else:
                messages.error(request, "You don't have permission to update this fault.")
                return redirect('fault_locator:field_update', fault_id=fault.id)

        context = {
            'fault': fault,
            'current_location': {
                'latitude': None,
                'longitude': None,
            },
            'user_profile': user_profile,
            'can_update': can_edit or in_assigned_team,
        }

        return render(request, 'fault_locator/fault_location_update.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Field update error: {e}")
        messages.error(request, "An error occurred loading the fault details.")
        return redirect('fault_locator:simple_fault_list')

@login_required
def quick_fault_report(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check if user can report faults (fault reporters, team members, or other authorized roles)
        can_report = (
            is_fault_reporter(user_profile) or 
            is_team_member(user_profile) or 
            is_team_leader(user_profile) or 
            is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None) or 
            is_senior_foreman(user_profile)
        )
        
        if not can_report:
            messages.error(request, "You don't have permission to report faults. Contact your supervisor to get the appropriate role.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        # Check depot assignment for fault reporters
        if is_fault_reporter(user_profile) and (not hasattr(user_profile, 'depot') or not user_profile.depot):
            messages.error(request, "You must be assigned to a depot before you can report faults.")
            return redirect('fault_locator:fault_locator_dashboard')
        
        if request.method == "POST":
            # Determine form parameters based on user role and region
            form_kwargs = {}
            if user_profile and user_profile.region:
                form_kwargs['user_region'] = user_profile.region
            
            # Pre-fill user depot for non-senior users
            user_depot = None
            if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
                user_depot = user_profile.depot
                # For fault reporters and non-senior foremen, restrict to their depot only
                if (is_fault_reporter(user_profile) or not is_senior_foreman(user_profile)) and user_depot:
                    form_kwargs['user_depot'] = user_depot
            
            form = QuickFaultReportForm(request.POST, **form_kwargs)
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
                    return redirect('fault_locator:simple_assign_fault', fault_id=fault.id)
                else:
                    return redirect('fault_locator:simple_fault_list')
            else:
                # Form has errors, it will be displayed with errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            # GET request - show form
            form_kwargs = {}
            if user_profile and user_profile.region:
                form_kwargs['user_region'] = user_profile.region
            
            # Pre-fill user depot for non-senior users
            user_depot = None
            if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
                user_depot = user_profile.depot
                # For fault reporters and non-senior foremen, restrict to their depot only
                if (is_fault_reporter(user_profile) or not is_senior_foreman(user_profile)) and user_depot:
                    form_kwargs['user_depot'] = user_depot
            
            form = QuickFaultReportForm(**form_kwargs)
        
        context = {
            'form': form,
            'user_profile': user_profile,
            'priority_choices': Fault._meta.get_field('priority').choices,
        }
        
        return render(request, "fault_locator/quick_fault_report.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Quick fault report error: {e}")
        messages.error(request, "An error occurred reporting the fault.")
    return redirect('fault_locator:fault_locator_dashboard')

@login_required
def create_fault(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check if user can report faults
        can_report = (
            is_fault_reporter(user_profile) or 
            is_team_member(user_profile) or 
            is_team_leader(user_profile) or 
            is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None) or 
            is_senior_foreman(user_profile)
        )
        
        if not can_report:
            messages.error(request, "You don't have permission to report faults. Contact your supervisor to get the appropriate role.")
            return redirect('fault_locator:fault_locator_dashboard')
        
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
                    return redirect('fault_locator:simple_assign_fault', fault_id=fault.id)
                else:
                    return redirect('fault_locator:simple_fault_list')
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Create fault error: {e}")
        messages.error(request, "An error occurred creating the fault.")
    return redirect('fault_locator:fault_locator_dashboard')

@login_required
@fault_assignment_required
@transaction.atomic
def simple_assign_fault(request, fault_id=None):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not (is_senior_foreman(user_profile) or is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)):
            messages.error(request, "You don't have permission to assign faults")
            return redirect('fault_locator:simple_fault_list')
        
        # Get fault if specified
        fault = None
        if fault_id:
            fault = get_object_or_404(Fault, id=fault_id)
            # Check if user can assign this fault
            if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
                user_depot = Depots.objects.filter(code=user_profile.depot).first()
                if fault.depot != user_depot:
                    messages.error(request, "You can only assign faults at your depot")
                    return redirect('fault_locator:simple_fault_list')
        
        if request.method == "POST":
            fault_id = request.POST.get('fault_id')
            team_id = request.POST.get('team_id')
            
            if not fault_id or not team_id:
                messages.error(request, "Please select both fault and team")
                return redirect('fault_locator:assign_fault')
            
            try:
                # Use select_for_update to prevent race conditions
                fault = Fault.objects.select_for_update().get(id=fault_id)
                team = FaultLocatorTeam.objects.select_for_update().get(id=team_id)
                
                # Check if fault is already assigned
                existing_assignment = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).first()
                if existing_assignment:
                    messages.error(request, "This fault is already assigned to a team")
                    return redirect('fault_locator:simple_fault_list')
                
                # Check if team has gear
                device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).select_related('device').first()
                if not device_assignment:
                    messages.error(request, f"Team '{team.name}' doesn't have gear assigned")
                    return redirect('fault_locator:assign_fault')
                
                # Check if assigned gear is in working condition
                if device_assignment.device.status not in ['available', 'assigned']:
                    messages.error(request, f"Team '{team.name}' cannot be assigned faults. Gear '{device_assignment.device.serial_number}' is {device_assignment.device.get_status_display()}")
                    return redirect('fault_locator:assign_fault')
                
                # Create assignment atomically
                fault_assignment = FaultAssignment.objects.create(
                    fault=fault,
                    team=team,
                    device=device_assignment.device,
                    assigned_by=user_profile
                )
                
                # Update fault status
                fault.status = 'assigned'
                fault.save()
                
                # Send notifications
                notify_fault_assignment(fault_assignment, request)
                
                messages.success(request, f"Fault assigned to team '{team.name}' with gear '{device_assignment.device.serial_number}'")
                return redirect('fault_locator:simple_fault_list')
                
            except Fault.DoesNotExist:
                messages.error(request, "Fault not found")
                return redirect('fault_locator:simple_fault_list')
            except FaultLocatorTeam.DoesNotExist:
                messages.error(request, "Team not found")
                return redirect('fault_locator:assign_fault')
            except IntegrityError as e:
                messages.error(request, "Assignment conflict occurred. Please try again.")
                return redirect('fault_locator:assign_fault')
        
        # GET request - show assignment form
        
        # Get available faults for assignment
        available_faults = Fault.objects.filter(status='requested')
        
        # Filter faults based on user role
        if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
            user_depot = Depots.objects.filter(code=user_profile.depot).first()
            if user_depot:
                available_faults = available_faults.filter(depot=user_depot)
        
        # Get available teams (teams with working devices)
        teams_with_devices = FaultLocatorDeviceAssignment.objects.select_related(
            'team', 'device'
        ).filter(
            device__status__in=['available', 'assigned']  # Only working devices
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Assign fault error: {e}")
        messages.error(request, "An error occurred assigning the fault.")
        return redirect('fault_locator:fault_locator_dashboard')

@login_required
@team_management_required
@transaction.atomic
def create_team(request):
    """View for creating a new fault locator team"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
            messages.error(request, "You don't have permission to create teams")
            return redirect('fault_locator:team_overview')
        
        if request.method == 'POST':
            # Use the updated form (imported at module level)
            form = FaultLocatorTeamForm(request.POST, user_region=user_profile.region)
            if form.is_valid():
                team = form.save(commit=False)
                
                # Set assigned_by
                team.assigned_by = user_profile
                
                # Handle team leader assignment
                team_leader = form.cleaned_data.get('team_leader')
                members = form.cleaned_data.get('members')
                
                if not team_leader and members:
                    # If no leader is selected, assign the first member as leader
                    team.team_leader = members[0]
                
                team.save()
                form.save_m2m()  # Save many-to-many relationships
                
                # Ensure team leader is also a member
                if team.team_leader and team.team_leader not in team.members.all():
                    team.members.add(team.team_leader)
                
                messages.success(request, f"Team '{team.name}' created successfully!")
                return redirect('fault_locator:team_overview')
            else:
                # Form has errors, display them
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            # GET request - show empty form
            form = FaultLocatorTeamForm(user_region=user_profile.region)
        
        context = {
            'form': form,
            'user_profile': user_profile,
            'page_title': 'Create New Team',
        }
        
        return render(request, 'fault_locator/create_team.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Create team error: {e}")
        messages.error(request, "An error occurred creating the team.")
    return redirect('fault_locator:team_overview')

@login_required
@team_management_required
@transaction.atomic
def edit_team(request, team_id):
    """View for editing an existing fault locator team"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        team = get_object_or_404(FaultLocatorTeam, id=team_id)
        
        # Check permissions
        can_edit = is_senior_foreman(user_profile) or \
                   (is_depot_foreperson(user_profile, user_profile.depot if hasattr(user_profile, 'depot') else None) and team.current_depot and team.current_depot.code == user_profile.depot)

        if not can_edit:
            messages.error(request, "You don't have permission to edit this team")
            return redirect('fault_locator:team_overview')
        
        if request.method == 'POST':
            form = FaultLocatorTeamForm(request.POST, instance=team, user_region=user_profile.region)
            if form.is_valid():
                updated_team = form.save(commit=False)
                
                # Handle team leader assignment
                team_leader = form.cleaned_data.get('team_leader')
                members = form.cleaned_data.get('members')
                
                if not team_leader and members:
                    # If no leader is selected, assign the first member as leader
                    updated_team.team_leader = members[0]
                
                updated_team.save()
                form.save_m2m()
                
                # Ensure team leader is also a member
                if updated_team.team_leader and updated_team.team_leader not in updated_team.members.all():
                    updated_team.members.add(updated_team.team_leader)
                
                messages.success(request, f"Team '{updated_team.name}' updated successfully!")
                return redirect('fault_locator:team_overview')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            form = FaultLocatorTeamForm(instance=team, user_region=user_profile.region)
        
        context = {
            'form': form,
            'team': team,
            'user_profile': user_profile,
            'page_title': f'Edit Team "{team.name}"',
        }
        
        return render(request, 'fault_locator/edit_team.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Edit team error: {e}")
        messages.error(request, "An error occurred editing the team.")
    return redirect('fault_locator:team_overview')

@login_required
@team_management_required
def add_team_member(request, team_id):
    """View for adding a member to a fault locator team"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        team = get_object_or_404(FaultLocatorTeam, id=team_id)
        
        # Check permissions
        can_edit = is_senior_foreman(user_profile) or \
                   (is_depot_foreperson(user_profile, user_profile.depot if hasattr(user_profile, 'depot') else None) and team.current_depot and team.current_depot.code == user_profile.depot)

        if not can_edit:
            messages.error(request, "You don't have permission to add members to this team")
            return redirect('fault_locator:team_overview')
        
        if request.method == 'POST':
            form = AddTeamMemberForm(request.POST, user_region=user_profile.region, team=team)
            if form.is_valid():
                member = form.cleaned_data['member']
                
                # Check if member can be added to team
                can_add, reason = can_user_be_added_to_team(member, team)
                
                if not can_add:
                    messages.error(request, f"Cannot add {member.get_full_name()}: {reason}")
                    return redirect('fault_locator:add_team_member', team_id=team.id)
                
                if member not in team.members.all():
                    team.members.add(member)
                    
                    # Send team member addition notification
                    notify_team_member_addition(team, member, user_profile, request)
                    
                    messages.success(request, f"{member.get_full_name()} added to team")
                else:
                    messages.warning(request, f"{member.get_full_name()} is already in this team")
                return redirect('fault_locator:edit_team', team_id=team.id)
        else:
            form = AddTeamMemberForm(user_region=user_profile.region, team=team)
        
        context = {
            'form': form,
            'team': team,
            'user_profile': user_profile,
            'page_title': f'Add Member to Team "{team.name}"',
        }
        
        return render(request, 'fault_locator/add_team_member.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Add team member error: {e}")
        messages.error(request, "An error occurred adding the team member.")
    return redirect('fault_locator:team_overview')

@login_required
@team_management_required
def remove_team_member(request, team_id, member_id):
    """View for removing a member from a fault locator team"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        team = get_object_or_404(FaultLocatorTeam, id=team_id)
        member = get_object_or_404(UserProfile, id=member_id)
        
        # Check permissions
        can_edit = is_senior_foreman(user_profile) or \
                   (is_depot_foreperson(user_profile, user_profile.depot if hasattr(user_profile, 'depot') else None) and team.current_depot and team.current_depot.code == user_profile.depot)

        if not can_edit:
            messages.error(request, "You don't have permission to remove members from this team")
            return redirect('fault_locator:team_overview')
        
        if request.method == 'POST':
            # Prevent removal if it would leave the team without a leader
            if team.team_leader == member:
                messages.error(request, "Cannot remove the team leader. Please assign a new leader first.")
                return redirect('fault_locator:edit_team', team_id=team.id)
            
            team.members.remove(member)
            
            # Send team member removal notification
            notify_team_member_removal(team, member, user_profile, request)
            
            messages.success(request, f"{member.get_full_name()} removed from team")
            return redirect('fault_locator:edit_team', team_id=team.id)
        
        context = {
            'team': team,
            'member': member,
            'user_profile': user_profile,
            'page_title': f'Remove Member from Team "{team.name}"',
        }
        
        return render(request, 'fault_locator/remove_team_member.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Remove team member error: {e}")
        messages.error(request, "An error occurred removing the team member.")
    return redirect('fault_locator:team_overview')

# GEAR MANAGEMENT VIEWS

@login_required
def device_list(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not can_manage_devices(user_profile):
            messages.error(request, "You don't have permission to manage gear")
            return redirect('fault_locator:fault_locator_dashboard')
        
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Gear list error: {e}")
        messages.error(request, "An error occurred loading the gear list.")
        return redirect('fault_locator:fault_locator_dashboard')

@login_required
@device_management_required
def create_device(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not can_manage_devices(user_profile):
            messages.error(request, "You don't have permission to create gear")
            return redirect('fault_locator:fault_locator_dashboard')
        
        if request.method == "POST":
            form = FaultLocatorDeviceForm(request.POST)
            if form.is_valid():
                device = form.save()
                messages.success(request, f"Gear '{device.serial_number}' created successfully!")
                return redirect('fault_locator:device_list')
        else:
            form = FaultLocatorDeviceForm()
        
        context = {
            'form': form,
            'user_profile': user_profile,
            'page_title': 'Create New Gear',
        }
        
        return render(request, "fault_locator/create_device.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Create gear error: {e}")
        messages.error(request, "An error occurred creating the gear.")
        return redirect('fault_locator:device_list')

# Team membership helper
def can_user_be_added_to_team(user: UserProfile, team: FaultLocatorTeam = None):
    """Check whether a user can be added to a (given) team.
    Rules:
    - Must be active
    - Cannot be a depot foreperson or senior foreperson
    - Cannot already belong to another team (excluding provided team)
    - Cannot be a leader of another team (excluding provided team)
    Returns tuple (can_add: bool, reason: str)
    """
    try:
        if not user or not getattr(user, 'is_active', False):
            return False, 'Inactive user'

        # Role restrictions
        if is_depot_foreperson(user) or is_senior_foreman(user):
            return False, 'Forepersons cannot be team members'

        # Already a member of another team
        if team:
            if user.fault_locator_teams.exclude(pk=team.pk).exists():
                return False, 'Already a member of another team'
        else:
            if user.fault_locator_teams.exists():
                return False, 'Already a member of a team'

        # Already a team leader elsewhere
        if team:
            if FaultLocatorTeam.objects.filter(team_leader=user).exclude(pk=team.pk).exists():
                return False, 'Already a leader of another team'
        else:
            if FaultLocatorTeam.objects.filter(team_leader=user).exists():
                return False, 'Already a leader of a team'

        return True, 'OK'
    except Exception:
        return False, 'Validation error'

@login_required
def edit_device(request, device_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not can_manage_devices(user_profile):
            messages.error(request, "You don't have permission to edit gear")
            return redirect('fault_locator:fault_locator_dashboard')
        
        device = get_object_or_404(FaultLocatorDevice, id=device_id)
        
        if request.method == "POST":
            form = FaultLocatorDeviceForm(request.POST, instance=device)
            if form.is_valid():
                device = form.save()
                messages.success(request, f"Gear '{device.serial_number}' updated successfully!")
                return redirect('fault_locator:device_list')
        else:
            form = FaultLocatorDeviceForm(instance=device)
        
    # Check if gear is currently in use
        current_assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
        active_fault = FaultAssignment.objects.filter(device=device, located_at__isnull=True).first()
        
        context = {
            'form': form,
            'device': device,
            'current_assignment': current_assignment,
            'active_fault': active_fault,
            'user_profile': user_profile,
            'page_title': f'Edit Gear: {device.serial_number}',
            'can_delete': not current_assignment and not active_fault,
        }
        
        return render(request, "fault_locator/edit_device.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Edit gear error: {e}")
        messages.error(request, "An error occurred editing the gear.")
        return redirect('fault_locator:device_list')

@login_required
def device_detail(request, device_id):
    try:
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Gear detail error: {e}")
        messages.error(request, "An error occurred loading gear details.")
        return redirect('fault_locator:device_list')

# --- Minimal placeholder views to satisfy URL routing ---
@login_required
def fault_reporter_dashboard(request):
    messages.info(request, 'Redirected to Quick Fault Report (dashboard placeholder)')
    return redirect('fault_locator:quick_fault_report')

@login_required
def bulk_fault_report(request):
    messages.info(request, 'Redirected to Quick Fault Report (bulk placeholder)')
    return redirect('fault_locator:quick_fault_report')

@login_required
def my_fault_reports(request):
    messages.info(request, 'Redirected to fault list (my reports placeholder)')
    return redirect('fault_locator:fault_list')

@login_required
def team_overview(request):
    """Team overview page showing teams, members, gear status, and deployment state."""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()

    teams = FaultLocatorTeam.objects.all().prefetch_related('members')

    # Senior foreperson should see teams in their region only (by members, leader, or current depot region)
    user_region = getattr(user_profile, 'region', None)
    if is_senior_foreman(user_profile) and user_region:
        from it.users.models import UserProfile as ItUserProfile
        users_in_region = ItUserProfile.objects.filter(
            region=user_region,
            is_active=True
        ).values_list('id', flat=True)
        teams = teams.filter(
            Q(members__in=users_in_region) |
            Q(team_leader__in=users_in_region) |
            Q(current_depot__region=user_region)
        ).distinct()

    team_data = []
    for team in teams:
        device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).select_related('device').first()
        has_device = device_assignment is not None
        device = device_assignment.device if device_assignment else None

        is_deployed = team.current_depot is not None
        current_deployment = TeamDeployment.objects.filter(team=team, recalled_at__isnull=True).select_related('depot', 'deployed_by').first()

        status = 'deployed' if is_deployed else ('available' if has_device else 'no_device')
        status_class = 'text-green-600' if status == 'deployed' else ('text-blue-600' if status == 'available' else 'text-gray-500')

        active_assignments = FaultAssignment.objects.filter(team=team, located_at__isnull=True).select_related('fault')

        team_data.append({
            'team': team,
            'status': status,
            'status_class': status_class,
            'location': team.current_depot.depot if team.current_depot else 'Not deployed',
            'actual_member_count': team.members.count(),
            'actual_active_assignments': active_assignments.count(),
            'team_leader_name': team.get_team_leader_name(),
            'team_members': [
                {
                    'name': m.get_full_name(),
                    'email': m.email
                } for m in team.members.all()
            ],
            'deployment_info': {
                'depot_name': current_deployment.depot.depot if current_deployment else None,
                'assigned_at': current_deployment.deployed_at if current_deployment else None,
                'assigned_by': current_deployment.deployed_by.get_full_name() if (current_deployment and current_deployment.deployed_by) else None,
            },
            'has_device': has_device,
            'device_serial': device.serial_number if device else None,
            'device': device,
            'is_deployed': is_deployed,
            'can_interact_with_team': is_senior_foreman(user_profile),
            'actions': [],
        })

    # Scope summary to filtered teams
    team_ids = list(teams.values_list('id', flat=True))
    summary_stats = {
        'total_teams': len(team_ids),
        'deployed_teams': teams.filter(current_depot__isnull=False).count(),
        'teams_with_devices': FaultLocatorDeviceAssignment.objects.filter(team_id__in=team_ids).values('team').distinct().count(),
        'active_assignments': FaultAssignment.objects.filter(team_id__in=team_ids, located_at__isnull=True).count(),
    }

    context = {
        'user_profile': user_profile,
        'team_data': team_data,
        'summary_stats': summary_stats,
        'is_senior_foreman': is_senior_foreman(user_profile),
        'can_create_team': can_create_teams(user_profile),
        'page_title': 'Team Overview',
    }

    return render(request, 'fault_locator/team_overview.html', context)

@login_required
def my_work(request):
    messages.info(request, 'My work placeholder. Redirecting to fault list.')
    return redirect('fault_locator:fault_list')

@login_required
@transaction.atomic
def deploy_team(request, team_id=None):
    """Render deployment page and handle deployment submission."""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not is_senior_foreman(user_profile):
        messages.error(request, "You don't have permission to deploy teams.")
        return redirect('fault_locator:team_overview')

    # Prepare form limited to teams with devices and not deployed (form also filters)
    # Teams: senior foremen see all teams (no region filter); others filtered by their region
    team_region = None if is_senior_foreman(user_profile) else getattr(user_profile, 'region', None)
    # Depots: always restrict to user's region if available (per request)
    depot_region = getattr(user_profile, 'region', None)

    if request.method == 'POST':
        form = TeamDeploymentForm(request.POST, team_region=team_region, depot_region=depot_region)
        selected_team = None
        if form.is_valid():
            team = form.cleaned_data['team']
            depot = form.cleaned_data['depot']
            notes = form.cleaned_data.get('deployment_notes', '')

            # Ensure team still valid
            if FaultLocatorDeviceAssignment.objects.filter(team=team).first() is None:
                messages.error(request, f"Team '{team.name}' must have gear assigned before deployment.")
                return redirect('fault_locator:deploy_team')
            if team.current_depot:
                messages.error(request, f"Team '{team.name}' is already deployed to {team.current_depot.depot}.")
                return redirect('fault_locator:deploy_team')

            deployment = TeamDeployment.objects.create(
                team=team,
                depot=depot,
                deployed_by=user_profile,
                deployment_notes=notes
            )
            team.current_depot = depot
            team.assigned_at = deployment.deployed_at
            team.assigned_by = user_profile
            team.save()

            try:
                notify_team_deployment(deployment, request)
            except Exception:
                pass

            messages.success(request, f"Team '{team.name}' deployed to {depot.depot}.")
            return redirect('fault_locator:team_overview')
    else:
        form = TeamDeploymentForm(team_region=team_region, depot_region=depot_region)
        selected_team = None
        if team_id:
            selected_team = FaultLocatorTeam.objects.filter(id=team_id).first()

    # Build depot priority info for the template
    # Depot list for priority panel: restrict to user's region as well
    depots = Depots.objects.all()
    if depot_region:
        depots = depots.filter(region=depot_region)

    depot_priority_info = []
    for depot in depots:
        pending_faults = Fault.objects.filter(depot=depot, status='requested').count()
        in_progress_faults = Fault.objects.filter(depot=depot, status='assigned').count()
        critical_faults = Fault.objects.filter(depot=depot, priority__gte=3, status__in=['requested', 'assigned']).count()
        team_count = FaultLocatorTeam.objects.filter(current_depot=depot).count()
        oldest_fault = Fault.objects.filter(depot=depot, status__in=['requested', 'assigned']).order_by('reported_at').first()
        oldest_fault_hours = None
        if oldest_fault:
            delta = timezone.now() - oldest_fault.reported_at
            oldest_fault_hours = int(delta.total_seconds() // 3600)

        # Simple weighted workload score
        workload_score = pending_faults * 2 + in_progress_faults + critical_faults * 3 - team_count * 2
        if workload_score >= 10 or critical_faults >= 2:
            level = 'CRITICAL'; pclass = 'bg-red-100 text-red-800'; icon = '🚨'
        elif workload_score >= 6:
            level = 'HIGH'; pclass = 'bg-orange-100 text-orange-800'; icon = '⚠️'
        elif workload_score >= 3:
            level = 'MEDIUM'; pclass = 'bg-yellow-100 text-yellow-800'; icon = '⚡'
        else:
            level = 'LOW'; pclass = 'bg-green-100 text-green-800'; icon = '✅'

        depot_priority_info.append({
            'depot': depot,
            'pending_faults': pending_faults,
            'in_progress_faults': in_progress_faults,
            'critical_faults': critical_faults,
            'team_count': team_count,
            'oldest_fault_hours': oldest_fault_hours,
            'workload_score': workload_score,
            'priority_level': level,
            'priority_class': pclass,
            'priority_icon': icon,
            'needs_team': team_count == 0 and (pending_faults > 0 or in_progress_faults > 0),
            'overwhelmed': team_count > 0 and (pending_faults + in_progress_faults) / max(team_count, 1) >= 5,
            'team_details': [
                {
                    'name': t.name,
                    'active_assignments': FaultAssignment.objects.filter(team=t, located_at__isnull=True).count(),
                    'status': 'busy' if FaultAssignment.objects.filter(team=t, located_at__isnull=True).exists() else 'idle'
                } for t in FaultLocatorTeam.objects.filter(current_depot=depot)
            ]
        })

    context = {
        'user_profile': user_profile,
        'form': form,
        'selected_team': selected_team,
        'depot_priority_info': depot_priority_info,
        'page_title': 'Deploy Team to Depot',
    }
    return render(request, 'fault_locator/deploy_team.html', context)

@login_required
def recall_team(request, team_id):
    messages.info(request, 'Recall team placeholder.')
    return redirect('fault_locator:team_overview')

@login_required
@transaction.atomic
def assign_team_to_depot(request, team_id):
    """Assign a team to a depot (deployment)."""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not is_senior_foreman(user_profile):
        messages.error(request, "You don't have permission to deploy teams.")
        return redirect('fault_locator:team_overview')

    team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)

    # Ensure team has gear
    device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
    if not device_assignment:
        messages.error(request, f"Team '{team.name}' must have gear assigned before deployment.")
        return redirect('fault_locator:team_overview')

    if request.method == 'POST':
        form = TeamDepotAssignmentForm(request.POST, user_region=getattr(user_profile, 'region', None))
        if form.is_valid():
            depot = form.cleaned_data['depot']
            notes = form.cleaned_data.get('deployment_notes', '')

            if team.current_depot:
                messages.error(request, f"Team '{team.name}' is already deployed to {team.current_depot.depot}.")
                return redirect('fault_locator:team_overview')

            deployment = TeamDeployment.objects.create(
                team=team,
                depot=depot,
                deployed_by=user_profile,
                deployment_notes=notes,
            )
            team.current_depot = depot
            team.assigned_at = deployment.deployed_at
            team.assigned_by = user_profile
            team.save()

            # Notify
            try:
                notify_team_deployment(deployment, request)
            except Exception:
                pass

            messages.success(request, f"Team '{team.name}' deployed to {depot.depot}.")
            return redirect('fault_locator:team_overview')
    else:
        form = TeamDepotAssignmentForm(user_region=getattr(user_profile, 'region', None))

    return render(request, 'fault_locator/assign_team_to_depot.html', {
        'form': form,
        'team': team,
        'user_profile': user_profile,
        'page_title': f"Assign '{team.name}' to Depot",
    })

@login_required
@transaction.atomic
def recall_team_from_depot(request, team_id):
    """Recall a deployed team from a depot (POST)."""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not is_senior_foreman(user_profile):
        messages.error(request, "You don't have permission to recall teams.")
        return redirect('fault_locator:team_overview')

    team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('fault_locator:team_overview')

    if not team.current_depot:
        messages.error(request, f"Team '{team.name}' is not currently deployed.")
        return redirect('fault_locator:team_overview')

    # Ensure no active assignments
    active_assignments = FaultAssignment.objects.filter(team=team, located_at__isnull=True)
    if active_assignments.exists():
        messages.error(request, f"Team has {active_assignments.count()} active fault assignments. Cannot recall.")
        return redirect('fault_locator:team_overview')

    # Update current deployment record
    current_deployment = TeamDeployment.objects.filter(team=team, recalled_at__isnull=True).first()
    if current_deployment:
        current_deployment.recalled_at = timezone.now()
        current_deployment.recalled_by = user_profile
        current_deployment.recall_notes = 'Recalled via team overview'
        current_deployment.save()

    depot_name = team.current_depot.depot
    team.current_depot = None
    team.assigned_at = None
    team.assigned_by = None
    team.save()

    try:
        notify_team_recall(team, user_profile, request)
    except Exception:
        pass

    messages.success(request, f"Team '{team.name}' recalled from {depot_name}.")
    return redirect('fault_locator:team_overview')

@login_required
def advanced_fault_assignment(request):
    messages.info(request, 'Advanced assignment placeholder. Redirecting to simple assign.')
    return redirect('fault_locator:assign_fault')

@login_required
def change_fault_priority(request, fault_id):
    messages.info(request, 'Change priority placeholder.')
    return redirect('fault_locator:field_update', fault_id=fault_id)

@login_required
def debug_user(request):
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    from django.http import HttpResponse
    return HttpResponse(f"User: {user_profile.get_full_name() if user_profile else 'Unknown'}")

@login_required
def role_troubleshooting(request):
    messages.info(request, 'Role troubleshooting placeholder.')
    return redirect('fault_locator:fault_locator_dashboard')

@login_required
@transaction.atomic
def assign_device_to_team(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not can_manage_devices(user_profile):
            messages.error(request, "You don't have permission to assign gear")
            return redirect('fault_locator:fault_locator_dashboard')
        
        team_id = request.GET.get('team_id')
        
        if request.method == "POST":
            form = SeniorForepersonDeviceAssignmentForm(request.POST, user=user_profile)
            if form.is_valid():
                try:
                    # Get device and team with locks to prevent race conditions
                    device = FaultLocatorDevice.objects.select_for_update().get(id=form.cleaned_data['device'].id)
                    team = FaultLocatorTeam.objects.select_for_update().get(id=form.cleaned_data['team'].id)
                    
                    # Check if gear is already assigned
                    existing_device_assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
                    if existing_device_assignment:
                        messages.error(request, f"Gear '{device.serial_number}' is already assigned to team '{existing_device_assignment.team.name}'")
                        return redirect('fault_locator:assign_device_to_team')
                    
                    # Check if team already has gear
                    existing_team_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
                    if existing_team_assignment:
                        messages.error(request, f"Team '{team.name}' already has gear '{existing_team_assignment.device.serial_number}' assigned")
                        return redirect('fault_locator:assign_device_to_team')
                    
                    # Create assignment atomically
                    assignment = FaultLocatorDeviceAssignment.objects.create(
                        device=device,
                        team=team,
                        assigned_by=user_profile,
                        notes=form.cleaned_data.get('notes', '')
                    )
                    
                    # Notify team members
                    notify_device_assignment(assignment, request)
                    
                    messages.success(request, f"Gear '{assignment.device.serial_number}' assigned to team '{team.name}'")
                    return redirect('fault_locator:team_overview')
                    
                except FaultLocatorDevice.DoesNotExist:
                    messages.error(request, "Gear not found")
                    return redirect('fault_locator:assign_device_to_team')
                except FaultLocatorTeam.DoesNotExist:
                    messages.error(request, "Team not found")
                    return redirect('fault_locator:assign_device_to_team')
                except IntegrityError as e:
                    messages.error(request, "Gear assignment conflict. Gear may already be assigned to another team.")
                    return redirect('fault_locator:assign_device_to_team')
                except ValidationError as e:
                    messages.error(request, f"Assignment validation error: {str(e)}")
                    return redirect('fault_locator:assign_device_to_team')
        else:
            initial_data = {}
            if team_id:
                initial_data['team'] = team_id
            
            # Get user region safely
            user_region = None
            if user_profile and hasattr(user_profile, 'region') and user_profile.region:
                user_region = user_profile.region
            
            form = SeniorForepersonDeviceAssignmentForm(initial=initial_data, user=user_profile)
        
        context = {
            'form': form,
            'user_profile': user_profile,
            'page_title': 'Assign Gear to Team',
        }
        
        return render(request, "fault_locator/assign_device_to_team.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Assign gear to team error: {e}")
        messages.error(request, "An error occurred assigning the gear to team.")
        return redirect('fault_locator:device_list')

@login_required
def unassign_device(request, device_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not can_manage_devices(user_profile):
            messages.error(request, "You don't have permission to unassign gear")
            return redirect('fault_locator:fault_locator_dashboard')
        
        device = get_object_or_404(FaultLocatorDevice, id=device_id)
        assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
        
        if not assignment:
            messages.error(request, "Device is not currently assigned to any team")
            return redirect('fault_locator:device_list')
        
    # Check if gear is being used for active fault
        active_fault = FaultAssignment.objects.filter(device=device, located_at__isnull=True).first()
        if active_fault:
            messages.error(request, f"Cannot unassign gear - it's currently being used for fault: {active_fault.fault.description}")
            return redirect('fault_locator:device_list')
        
        if request.method == "POST":
            team = assignment.team
            assignment.delete()
            
            # Notify team members
            for member in team.members.all():
                if member.email:
                    message = f"Gear '{device.serial_number}' has been removed from your team '{team.name}'"
                    url = f"/fault_locator/teams/{team.id}/"
                    notify_fault_locator_user(
                        user=member,
                        message=message,
                        notification_type="Gear Removal",
                        url=url,
                        fault_or_team_id=team.id,
                        request=request
                    )
            
            messages.success(request, f"Gear '{device.serial_number}' unassigned from team '{team.name}'")
            return redirect('fault_locator:device_list')
        
        context = {
            'device': device,
            'assignment': assignment,
            'user_profile': user_profile,
        }
        
        return render(request, "fault_locator/unassign_device.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unassign gear error: {e}")
        messages.error(request, "An error occurred unassigning the gear.")
        return redirect('fault_locator:device_list')

@login_required
@transaction.atomic
def edit_team(request, team_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
            messages.error(request, "You don't have permission to edit teams")
            return redirect('fault_locator:fault_locator_dashboard')
        
        team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
        
        if request.method == "POST":
            try:
                # Handle name change
                if 'update_name' in request.POST:
                    name_form = FaultLocatorTeamNameForm(request.POST, instance=team)
                    if name_form.is_valid():
                        team = name_form.save()
                        messages.success(request, f"Team name updated to '{team.name}'")
                        return redirect('fault_locator:edit_team', team_id=team.id)
                
                # Handle member addition
                elif 'add_member' in request.POST:
                    add_form = AddTeamMemberForm(request.POST, user_region=user_profile.region, team=team)
                    if add_form.is_valid():
                        member = add_form.cleaned_data['member']
                        
                        # Check if member can be added to team
                        can_add, reason = can_user_be_added_to_team(member, team)
                        
                        if not can_add:
                            messages.error(request, f"Cannot add {member.get_full_name()}: {reason}")
                            return redirect('fault_locator:edit_team', team_id=team.id)
                        
                        if member not in team.members.all():
                            team.members.add(member)
                            
                            # Send team member addition notification
                            notify_team_member_addition(team, member, user_profile, request)
                            
                            messages.success(request, f"{member.get_full_name()} added to team")
                        else:
                            messages.warning(request, f"{member.get_full_name()} is already in this team")
                        return redirect('fault_locator:edit_team', team_id=team.id)
                
                # Handle member removal
                elif 'remove_member' in request.POST:
                    member_id = request.POST.get('member_id')
                    if member_id:
                        member = get_object_or_404(UserProfile, id=member_id)
                        team.members.remove(member)
                        
                        # Send team member removal notification
                        notify_team_member_removal(team, member, user_profile, request)
                        
                        messages.success(request, f"{member.get_full_name()} removed from team")
                        return redirect('fault_locator:edit_team', team_id=team.id)
                        
            except IntegrityError as e:
                messages.error(request, "Team update conflict occurred. Please try again.")
                return redirect('fault_locator:edit_team', team_id=team.id)
            except ValidationError as e:
                messages.error(request, f"Team validation error: {str(e)}")
                return redirect('fault_locator:edit_team', team_id=team.id)
    
        # Initialize forms
        name_form = FaultLocatorTeamNameForm(instance=team)
        add_form = AddTeamMemberForm(user_region=user_profile.region, team=team)
        
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
            'is_senior_foreman': is_senior_foreman(user_profile),
            'can_manage_devices': can_manage_devices(user_profile),
            'page_title': f'Edit Team: {team.name}',
        }
        
        return render(request, "fault_locator/edit_team.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Edit team error: {e}")
        messages.error(request, "An error occurred editing the team.")
    return redirect('fault_locator:team_overview')

@login_required
def delete_team(request, team_id):
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    if request.method == 'POST':
        team.delete()
        messages.success(request, 'Team has been deleted successfully.')
        return redirect('fault_locator:team_overview')
    
    context = {
        'team': team,
        'page_title': 'Delete Team'
    }
    return render(request, 'fault_locator/delete_team.html', context)
