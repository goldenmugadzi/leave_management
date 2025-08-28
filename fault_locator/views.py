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
    message = f"Fault #{fault.id} has been assigned to your team '{team.name}'. Location: {fault.location_description}. Device: {device.serial_number}"
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

def notify_unassigned_faults(request):
    """Daily notification function for unassigned faults (to be called by scheduler)"""
    from datetime import timedelta
    
    # Get faults that are unassigned for more than 2 hours
    two_hours_ago = timezone.now() - timedelta(hours=2)
    unassigned_faults = Fault.objects.filter(
        status='requested',
        reported_at__lt=two_hours_ago
    ).select_related('depot', 'reported_by')
    
    if unassigned_faults.exists():
        # Group faults by depot
        depot_faults = {}
        for fault in unassigned_faults:
            depot_code = fault.depot.code
            if depot_code not in depot_faults:
                depot_faults[depot_code] = []
            depot_faults[depot_code].append(fault)
        
        # Notify depot forepersons about unassigned faults at their depot
        for depot_code, faults in depot_faults.items():
            depot_forepersons = UserProfile.objects.filter(
                depot=depot_code,
                designation__description__icontains='foreperson'
            )
            
            fault_list = ", ".join([f"#{fault.id}" for fault in faults])
            message = f"⏰ {len(faults)} fault(s) have been unassigned for over 2 hours: {fault_list}. Please assign them to teams."
            url = "/fault_locator/assign-fault/"
            notification_type = "Unassigned Faults Alert"
            
            for foreperson in depot_forepersons:
                notify_fault_locator_user(foreperson, message, notification_type, url, depot_code, request)
        
        # Also notify senior forepersons about overall unassigned faults
        senior_forepersons = UserProfile.objects.filter(
            designation__description__icontains='senior foreperson'
        )
        
        total_unassigned = unassigned_faults.count()
        senior_message = f"⚠️ System Alert: {total_unassigned} fault(s) have been unassigned for over 2 hours across all depots."
        
        for senior in senior_forepersons:
            notify_fault_locator_user(senior, senior_message, "System Alert", url, "system", request)

def notify_device_assignment(device_assignment, request):
    """Notify team members when a device is assigned to their team"""
    team = device_assignment.team
    device = device_assignment.device
    
    url = f"/fault_locator/team_overview/"
    message = f"Your team '{team.name}' has been assigned device '{device.serial_number}'. You can now be deployed for field work."
    notification_type = "Device Assignment"
    
    # Notify all team members
    for member in team.members.all():
        notify_fault_locator_user(member, message, notification_type, url, team.id, request)

def notify_device_removal(team, device, removed_by, request):
    """Notify team members when a device is removed from their team"""
    url = f"/fault_locator/team_overview/"
    message = f"Device '{device.serial_number}' has been removed from your team '{team.name}' by {removed_by.get_full_name()}."
    notification_type = "Device Removal"
    
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
                    'title': 'Device Management',
                    'description': 'View, create, edit, and assign all fault locator devices.',
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
                'description': 'Complete management interface for team deployment, device assignment, and performance monitoring.',
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
        return redirect('simple_fault_list')

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
        return redirect('fault_locator_dashboard')

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
            return redirect('fault_locator_dashboard')
        
        # Check depot assignment for fault reporters
        if is_fault_reporter(user_profile) and (not hasattr(user_profile, 'depot') or not user_profile.depot):
            messages.error(request, "You must be assigned to a depot before you can report faults.")
            return redirect('fault_locator_dashboard')
        
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
                    return redirect('simple_assign_fault', fault_id=fault.id)
                else:
                    return redirect('simple_fault_list')
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
        return redirect('fault_locator_dashboard')

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
            return redirect('fault_locator_dashboard')
        
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Create fault error: {e}")
        messages.error(request, "An error occurred creating the fault.")
        return redirect('fault_locator_dashboard')

@login_required
@fault_assignment_required
@transaction.atomic
def simple_assign_fault(request, fault_id=None):
    try:
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
                return redirect('assign_fault')
            
            try:
                # Use select_for_update to prevent race conditions
                fault = Fault.objects.select_for_update().get(id=fault_id)
                team = FaultLocatorTeam.objects.select_for_update().get(id=team_id)
                
                # Check if fault is already assigned
                existing_assignment = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).first()
                if existing_assignment:
                    messages.error(request, "This fault is already assigned to a team")
                    return redirect('simple_fault_list')
                
                # Check if team has a device
                device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).select_related('device').first()
                if not device_assignment:
                    messages.error(request, f"Team '{team.name}' doesn't have a device assigned")
                    return redirect('assign_fault')
                
                # Check if assigned device is in working condition
                if device_assignment.device.status not in ['available', 'assigned']:
                    messages.error(request, f"Team '{team.name}' cannot be assigned faults. Device '{device_assignment.device.serial_number}' is {device_assignment.device.get_status_display()}")
                    return redirect('assign_fault')
                
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
                
                messages.success(request, f"Fault assigned to team '{team.name}' with device '{device_assignment.device.serial_number}'")
                return redirect('simple_fault_list')
                
            except Fault.DoesNotExist:
                messages.error(request, "Fault not found")
                return redirect('simple_fault_list')
            except FaultLocatorTeam.DoesNotExist:
                messages.error(request, "Team not found")
                return redirect('assign_fault')
            except IntegrityError as e:
                messages.error(request, "Assignment conflict occurred. Please try again.")
                return redirect('assign_fault')
        
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
        return redirect('fault_locator_dashboard')

@login_required
@team_leader_required
@login_required
@transaction.atomic
def field_update(request, fault_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        fault = get_object_or_404(Fault.objects.select_for_update(), id=fault_id)
        
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
                # Use atomic transaction for fault status update
                with transaction.atomic():
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
                # Get current assignment for team information
                current_assignment = FaultAssignment.objects.filter(
                    fault=fault, 
                    located_at__isnull=True
                ).first()
                
                requesting_team = current_assignment.team if current_assignment else None
                
                # Send assistance request notification
                if requesting_team:
                    notify_assistance_request(fault, requesting_team, notes, request)
                
                messages.success(request, "🆘 Help request sent to senior forepersons")
        
        # GET request - show update form
        context = {
            'fault': fault,
            'current_assignment': current_assignment,
            'user_profile': user_profile,
            'team': current_assignment.team if current_assignment else None,
            'device': current_assignment.device if current_assignment else None,
        }
        
        return render(request, "fault_locator/field_update.html", context)
    except (IntegrityError, ValidationError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Field update error: {e}")
        messages.error(request, "An error occurred updating the fault status.")
        return redirect('fault_locator_dashboard')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Field update error: {e}")
        messages.error(request, "An error occurred updating the fault status.")
        return redirect('fault_locator_dashboard')

@login_required
def team_overview(request):
    try:
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
        
        # Role-based filtering - only apply depot filtering if user is specifically a depot foreperson
        if not is_senior_foreman(user_profile):
            # Only filter by depot if user is specifically a depot foreperson with a depot
            if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
                depot = get_user_depot(user_profile)
                if depot and is_depot_foreperson(user_profile, depot):
                    teams = teams.filter(current_depot=depot)
        # If user has no depot or is not a depot foreperson, show all teams
        # This allows team members and other users to see all teams
    
        # Add extra info for each team
        team_data = []
        for team in teams:
            device_assignment = team.faultlocatordeviceassignment_set.first()
            
            status = 'no_device'
            status_class = 'text-gray-500'
            actions = []
            
            # Only show permitted actions
            user_depot = get_user_depot(user_profile)
            can_interact_with_team = False
            
            # Determine if user can interact with this team
            if is_senior_foreman(user_profile):
                can_interact_with_team = True
            elif is_depot_foreperson(user_profile, user_depot):
                # Depot foreperson can only interact with teams deployed to their depot
                can_interact_with_team = (team.current_depot == user_depot)
            
            if device_assignment:
                if team.current_depot:
                    status = 'deployed'
                    status_class = 'text-green-600'
                    if can_interact_with_team:
                        actions.append({
                            'text': 'Recall',
                            'url': f'/fault_locator/teams/{team.id}/recall/',
                            'class': 'btn-warning btn-sm'
                        })
                else:
                    status = 'available'
                    status_class = 'text-blue-600'
                    if is_senior_foreman(user_profile):  # Only senior foremen can deploy teams
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
            if can_interact_with_team or can_manage_devices(user_profile):
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
                'can_interact_with_team': can_interact_with_team,
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
            'is_depot_foreperson': is_depot_foreperson(user_profile, user_depot),
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Team overview error: {e}")
        messages.error(request, "An error occurred loading the team overview.")
        return redirect('fault_locator_dashboard')

@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def assign_team_to_depot(request, team_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
            messages.error(request, "You don't have permission to assign teams to depots.")
            return redirect('team_overview')
        
        # Use select_for_update to prevent race conditions
        team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
        
        # Check if team has a working device assigned
        is_valid, error_message = validate_team_device_for_deployment(team)
        if not is_valid:
            messages.error(request, error_message)
            return redirect('team_overview')
        
        # Get the device assignment for context
        device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
        
        # Check if team is already deployed
        if team.current_depot:
            messages.error(request, f"Team '{team.name}' is already deployed to {team.current_depot.depot}.")
            return redirect('team_overview')
        
        # Get user region for filtering depots
        user_region = user_profile.region if user_profile else None
        
        if request.method == 'POST':
            form = TeamDepotAssignmentForm(request.POST, user_region=user_region)
            if form.is_valid():
                depot = form.cleaned_data['depot']
                deployment_notes = form.cleaned_data.get('deployment_notes', '')
                
                try:
                    # Create deployment atomically
                    deployment = TeamDeployment.objects.create(
                        team=team,
                        depot=depot,
                        deployed_by=user_profile,
                        deployment_notes=deployment_notes
                    )
                    
                    # Update team
                    team.current_depot = depot
                    team.assigned_at = deployment.deployed_at
                    team.assigned_by = user_profile
                    team.save()
                    
                    # Send deployment notifications
                    notify_team_deployment(deployment, request)
                    
                    messages.success(request, f"Team '{team.name}' has been successfully deployed to {depot.depot}.")
                    return redirect('team_overview')
                    
                except IntegrityError as e:
                    messages.error(request, "Team deployment conflict occurred. Please try again.")
                    return redirect('team_overview')
                except ValidationError as e:
                    messages.error(request, f"Deployment validation error: {str(e)}")
                    return redirect('team_overview')
        else:
            form = TeamDepotAssignmentForm(user_region=user_region)
        
        context = {
            'form': form,
            'team': team,
            'device': device_assignment.device if device_assignment else None,
            'user_profile': user_profile,
            'page_title': f'Assign Team "{team.name}" to Depot',
        }
        
        return render(request, 'fault_locator/assign_team_to_depot.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Assign team to depot error: {e}")
        messages.error(request, "An error occurred assigning the team to depot.")
        return redirect('team_overview')

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def recall_team_from_depot(request, team_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
            messages.error(request, "You don't have permission to recall teams from depots.")
            return redirect('team_overview')
        
        # Use select_for_update to prevent race conditions
        team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
        
        # Check if team is deployed
        if not team.current_depot:
            messages.error(request, f"Team '{team.name}' is not currently deployed.")
            return redirect('team_overview')
        
        # Check for active assignments (not yet located)
        active_assignments = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        )
        
        if request.method == "POST":
            if active_assignments.exists() and not request.POST.get('force_recall'):
                messages.error(request, "Team has active fault assignments. Use force recall if necessary.")
                return redirect('recall_team', team_id=team.id)
            
            try:
                # Handle reassign after faults
                reassign_after_faults = request.POST.get('reassign_after_faults') == 'on'
                reassign_depot_id = request.POST.get('reassign_depot')
                recall_notes = request.POST.get('recall_notes', '')
                
                reassign_depot = None
                if reassign_after_faults and reassign_depot_id:
                    try:
                        from it.users.models import Depots
                        reassign_depot = Depots.objects.get(id=reassign_depot_id)
                    except Depots.DoesNotExist:
                        reassign_depot = None
                
                # Find current deployment
                current_deployment = TeamDeployment.objects.filter(
                    team=team,
                    recalled_at__isnull=True
                ).first()
                
                if current_deployment:
                    current_deployment.recalled_at = timezone.now()
                    current_deployment.recalled_by = user_profile
                    
                    # Store recall notes and reassign intent
                    recall_notes_text = recall_notes
                    if reassign_after_faults and reassign_depot:
                        reassign_info = f"REASSIGN_TO:{reassign_depot.id}:{reassign_depot.depot}"
                        recall_notes_text = f"{recall_notes}\n{reassign_info}" if recall_notes else reassign_info
                    
                    current_deployment.recall_notes = recall_notes_text
                    current_deployment.save()
                
                # Update team status
                depot_name = team.current_depot.depot
                team.current_depot = None
                team.assigned_at = None
                team.assigned_by = None
                team.save()
                
                # Send recall notifications
                notify_team_recall(team, user_profile, request)
                
                # Success message
                success_message = f"Team '{team.name}' recalled from {depot_name}"
                if reassign_after_faults and reassign_depot:
                    success_message += f" and will be redeployed to {reassign_depot.depot} after current faults are completed"
                
                messages.success(request, success_message)
                return redirect('team_overview')
                
            except IntegrityError as e:
                messages.error(request, "Team recall conflict occurred. Please try again.")
                return redirect('team_overview')
            except ValidationError as e:
                messages.error(request, f"Recall validation error: {str(e)}")
                return redirect('team_overview')
    
        from it.users.models import Depots
        
        # Filter depots by user's region
        depots = Depots.objects.all().order_by('depot')
        if user_profile and user_profile.region:
            depots = depots.filter(region=user_profile.region)
        
        context = {
            'team': team,
            'active_assignments': active_assignments,
            'user_profile': user_profile,
            'depots': depots,
        }
        return render(request, "fault_locator/recall_team.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Recall team from depot error: {e}")
        messages.error(request, "An error occurred recalling the team from depot.")
        return redirect('team_overview')

@login_required
def my_work(request):
    try:
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"My work error: {e}")
        messages.error(request, "An error occurred loading your work assignments.")
        return redirect('fault_locator_dashboard')

# DEVICE MANAGEMENT VIEWS

@login_required
def device_list(request):
    try:
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Device list error: {e}")
        messages.error(request, "An error occurred loading the device list.")
        return redirect('fault_locator_dashboard')

@login_required
@device_management_required
def create_device(request):
    try:
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Create device error: {e}")
        messages.error(request, "An error occurred creating the device.")
        return redirect('device_list')

@login_required
def edit_device(request, device_id):
    try:
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Edit device error: {e}")
        messages.error(request, "An error occurred editing the device.")
        return redirect('device_list')

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
        logger.error(f"Device detail error: {e}")
        messages.error(request, "An error occurred loading device details.")
        return redirect('device_list')

@login_required
@transaction.atomic
def assign_device_to_team(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not can_manage_devices(user_profile):
            messages.error(request, "You don't have permission to assign devices")
            return redirect('fault_locator_dashboard')
        
        team_id = request.GET.get('team_id')
        
        if request.method == "POST":
            form = SeniorForepersonDeviceAssignmentForm(request.POST, user=user_profile)
            if form.is_valid():
                try:
                    # Get device and team with locks to prevent race conditions
                    device = FaultLocatorDevice.objects.select_for_update().get(id=form.cleaned_data['device'].id)
                    team = FaultLocatorTeam.objects.select_for_update().get(id=form.cleaned_data['team'].id)
                    
                    # Check if device is already assigned
                    existing_device_assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
                    if existing_device_assignment:
                        messages.error(request, f"Device '{device.serial_number}' is already assigned to team '{existing_device_assignment.team.name}'")
                        return redirect('assign_device_to_team')
                    
                    # Check if team already has a device
                    existing_team_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
                    if existing_team_assignment:
                        messages.error(request, f"Team '{team.name}' already has device '{existing_team_assignment.device.serial_number}' assigned")
                        return redirect('assign_device_to_team')
                    
                    # Create assignment atomically
                    assignment = FaultLocatorDeviceAssignment.objects.create(
                        device=device,
                        team=team,
                        assigned_by=user_profile,
                        notes=form.cleaned_data.get('notes', '')
                    )
                    
                    # Notify team members
                    notify_device_assignment(assignment, request)
                    
                    messages.success(request, f"Device '{assignment.device.serial_number}' assigned to team '{team.name}'")
                    return redirect('team_overview')
                    
                except FaultLocatorDevice.DoesNotExist:
                    messages.error(request, "Device not found")
                    return redirect('assign_device_to_team')
                except FaultLocatorTeam.DoesNotExist:
                    messages.error(request, "Team not found")
                    return redirect('assign_device_to_team')
                except IntegrityError as e:
                    messages.error(request, "Device assignment conflict. Device may already be assigned to another team.")
                    return redirect('assign_device_to_team')
                except ValidationError as e:
                    messages.error(request, f"Assignment validation error: {str(e)}")
                    return redirect('assign_device_to_team')
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Assign device to team error: {e}")
        messages.error(request, "An error occurred assigning the device to team.")
        return redirect('device_list')

@login_required
def unassign_device(request, device_id):
    try:
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unassign device error: {e}")
        messages.error(request, "An error occurred unassigning the device.")
        return redirect('device_list')

@login_required
@transaction.atomic
def edit_team(request, team_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
            messages.error(request, "You don't have permission to edit teams")
            return redirect('fault_locator_dashboard')
        
        team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
        
        if request.method == "POST":
            try:
                # Handle name change
                if 'update_name' in request.POST:
                    name_form = FaultLocatorTeamNameForm(request.POST, instance=team)
                    if name_form.is_valid():
                        team = name_form.save()
                        messages.success(request, f"Team name updated to '{team.name}'")
                        return redirect('edit_team', team_id=team.id)
                
                # Handle member addition
                elif 'add_member' in request.POST:
                    add_form = AddTeamMemberForm(request.POST, user_region=user_profile.region, team=team)
                    if add_form.is_valid():
                        member = add_form.cleaned_data['member']
                        
                        # Check if member can be added to team
                        can_add, reason = can_user_be_added_to_team(member, team)
                        
                        if not can_add:
                            messages.error(request, f"Cannot add {member.get_full_name()}: {reason}")
                            return redirect('edit_team', team_id=team.id)
                        
                        if member not in team.members.all():
                            team.members.add(member)
                            
                            # Send team member addition notification
                            notify_team_member_addition(team, member, user_profile, request)
                            
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
                        
                        # Send team member removal notification
                        notify_team_member_removal(team, member, user_profile, request)
                        
                        messages.success(request, f"{member.get_full_name()} removed from team")
                        return redirect('edit_team', team_id=team.id)
                        
            except IntegrityError as e:
                messages.error(request, "Team update conflict occurred. Please try again.")
                return redirect('edit_team', team_id=team.id)
            except ValidationError as e:
                messages.error(request, f"Team validation error: {str(e)}")
                return redirect('edit_team', team_id=team.id)
    
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
        return redirect('team_overview')

@login_required
@transaction.atomic
def create_team(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()

        # Check permissions
        if not (is_senior_foreman(user_profile) or can_manage_devices(user_profile)):
            messages.error(request, "You don't have permission to create teams")
            return redirect('fault_locator_dashboard')

        if request.method == "POST":
            try:
                from .forms import FaultLocatorTeamForm
                form = FaultLocatorTeamForm(request.POST, user_region=user_profile.region)
                if form.is_valid():
                    team = form.save(commit=False)
                    team.created_by = user_profile
                    team.save()

                    messages.success(request, f"Team '{team.name}' created successfully")
                    return redirect('edit_team', team_id=team.id)
            except Exception as e:
                messages.error(request, f"Error creating team: {str(e)}")
                return redirect('create_team')

        # Initialize form
        from .forms import FaultLocatorTeamForm
        form = FaultLocatorTeamForm(user_region=user_profile.region)

        context = {
            'form': form,
            'user_profile': user_profile,
            'page_title': 'Create New Team',
        }

        return render(request, "fault_locator/create_team.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Create team error: {e}")
        messages.error(request, "An error occurred creating the team.")
        return redirect('team_overview')

@login_required
@transaction.atomic
def delete_team(request, team_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions
        if not is_senior_foreman(user_profile):
            messages.error(request, "Only senior forepersons can delete teams")
            return redirect('fault_locator_dashboard')
        
        team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
        
        # Check if team has active assignments or device
        device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
        active_faults = FaultAssignment.objects.filter(team=team, located_at__isnull=True).exists()
        
        if device_assignment or active_faults:
            messages.error(request, "Cannot delete team - it has active assignments or assigned devices")
            return redirect('edit_team', team_id=team.id)
        
        if request.method == "POST":
            team_name = team.name
            
            # Use atomic transaction for team deletion
            with transaction.atomic():
                # Notify team members before deletion
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
    except (IntegrityError, ValidationError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Delete team error: {e}")
        messages.error(request, "An error occurred deleting the team.")
        return redirect('team_overview')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Delete team error: {e}")
        messages.error(request, "An error occurred deleting the team.")
        return redirect('team_overview')

@login_required
def get_depot_priority_information(user_profile):
    """
    Get depot priority information to help senior forepersons make informed team deployment decisions.
    Uses priority order: 1) Voltage, 2) Clients Affected, 3) Date Reported, 4) Priority Level
    """
    try:
        # Validate user_profile
        if not user_profile:
            return []
            
        # Get available depots based on user's region
        if user_profile and hasattr(user_profile, 'region') and user_profile.region:
            available_depots = Depots.objects.filter(region=user_profile.region).order_by('depot')
        else:
            available_depots = Depots.objects.all().order_by('depot')
        
        depot_info = []
        
        for depot in available_depots:
            # Get active faults (requested + assigned) for this depot
            active_faults = Fault.objects.filter(
                depot=depot, 
                status__in=['requested', 'assigned']
            ).order_by('-vvip', '-voltage', '-clients_affected', '-reported_at', '-priority')
            
            # Priority Analysis based on your requested criteria
            
            # 1. VOLTAGE ANALYSIS (Priority 1)
            high_voltage_faults = active_faults.filter(
                voltage__in=['400', '220', '132', '66']  # High voltage levels
            ).count()
            
            medium_voltage_faults = active_faults.filter(
                voltage__in=['33', '22', '11']  # Medium voltage levels  
            ).count()
            
            # Get highest voltage fault for display
            highest_voltage_fault = active_faults.filter(voltage__isnull=False).first()
            max_voltage_display = highest_voltage_fault.get_voltage_display() if highest_voltage_fault else "No voltage data"
            
            # 2. CLIENT IMPACT ANALYSIS (Priority 2)
            total_clients_affected = active_faults.aggregate(
                total=models.Sum('clients_affected')
            )['total'] or 0
            
            high_impact_faults = active_faults.filter(
                clients_affected__gte=100  # 100+ clients affected
            ).count()
            
            # Get highest client impact fault
            highest_impact_fault = active_faults.filter(clients_affected__isnull=False).order_by('-clients_affected').first()
            max_clients_affected = highest_impact_fault.clients_affected if highest_impact_fault else 0
            
            # 3. URGENCY ANALYSIS (Priority 3 - Date)
            from datetime import timedelta
            now = timezone.now()
            urgent_faults = active_faults.filter(
                reported_at__lt=now - timedelta(hours=4)  # Over 4 hours old
            ).count()
            
            very_urgent_faults = active_faults.filter(
                reported_at__lt=now - timedelta(hours=8)  # Over 8 hours old
            ).count()
            
            # Get oldest unassigned fault
            oldest_fault = active_faults.filter(status='requested').order_by('reported_at').first()
            
            # 4. PRIORITY LEVEL ANALYSIS (Priority 4)
            critical_faults = active_faults.filter(priority=4).count()
            high_priority_faults = active_faults.filter(priority=3).count()
            
            # COMBINED PRIORITY SCORE CALCULATION
            # Using your priority order weighting
            priority_score = 0
            
            # Voltage weight (40% of score)
            voltage_weight = (high_voltage_faults * 10) + (medium_voltage_faults * 5)
            priority_score += voltage_weight * 0.4
            
            # Client impact weight (30% of score)
            client_weight = min(total_clients_affected / 10, 50)  # Cap at 50 points
            priority_score += client_weight * 0.3
            
            # Urgency weight (20% of score)
            urgency_weight = (very_urgent_faults * 8) + (urgent_faults * 4)
            priority_score += urgency_weight * 0.2
            
            # Priority level weight (10% of score)
            priority_weight = (critical_faults * 10) + (high_priority_faults * 5)
            priority_score += priority_weight * 0.1
            
            # Get basic fault statistics
            total_faults = Fault.objects.filter(depot=depot).count()
            pending_faults = active_faults.filter(status='requested').count()
            in_progress_faults = active_faults.filter(status='assigned').count()
            
            # Get teams currently deployed to this depot
            deployed_teams = FaultLocatorTeam.objects.filter(current_depot=depot)
            team_count = deployed_teams.count()
            
            # Adjust score based on team availability
            if team_count == 0 and active_faults.exists():
                priority_score *= 1.8  # Major increase if no teams and active faults
            elif team_count == 1 and active_faults.count() > 3:
                priority_score *= 1.3  # Moderate increase if overwhelmed single team
            
            # Determine deployment recommendation
            if priority_score >= 30:
                recommendation = 'URGENT DEPLOYMENT NEEDED'
                recommendation_class = 'text-red-600 bg-red-50 border-red-200'
                recommendation_icon = '🚨'
            elif priority_score >= 20:
                recommendation = 'HIGH PRIORITY DEPLOYMENT'
                recommendation_class = 'text-orange-600 bg-orange-50 border-orange-200'
                recommendation_icon = '⚠️'
            elif priority_score >= 10:
                recommendation = 'CONSIDER DEPLOYMENT'
                recommendation_class = 'text-yellow-600 bg-yellow-50 border-yellow-200'
                recommendation_icon = '⚡'
            else:
                recommendation = 'LOW PRIORITY'
                recommendation_class = 'text-green-600 bg-green-50 border-green-200'
                recommendation_icon = '✅'
            
            # Get team details
            team_details = []
            for team in deployed_teams:
                active_assignments = FaultAssignment.objects.filter(
                    team=team, 
                    located_at__isnull=True
                ).count()
                
                team_details.append({
                    'name': team.name,
                    'members': team.members.count(),
                    'active_assignments': active_assignments,
                    'status': 'busy' if active_assignments > 0 else 'available'
                })
            
            # Calculate time since oldest fault
            oldest_fault_hours = 0
            if oldest_fault:
                time_diff = timezone.now() - oldest_fault.reported_at
                oldest_fault_hours = int(time_diff.total_seconds() / 3600)
            
            # Calculate recent resolution statistics
            from datetime import timedelta
            week_ago = timezone.now() - timedelta(days=7)
            recent_closed_faults = Fault.objects.filter(
                depot=depot,
                status='closed',
                reported_at__gte=week_ago
            )
            
            depot_info.append({
                'depot': depot,
                'depot_name': depot.depot,
                'total_faults': total_faults,
                'pending_faults': pending_faults,
                'in_progress_faults': in_progress_faults,
                'active_faults_count': active_faults.count(),
                
                # Priority Analysis Data (your requested order)
                'max_voltage_display': max_voltage_display,
                'high_voltage_count': high_voltage_faults,
                'medium_voltage_count': medium_voltage_faults,
                'total_clients_affected': total_clients_affected,
                'max_clients_affected': max_clients_affected,
                'high_impact_count': high_impact_faults,
                'urgent_faults': urgent_faults,
                'very_urgent_faults': very_urgent_faults,
                'oldest_fault_hours': oldest_fault_hours,
                'critical_faults': critical_faults,
                'high_priority_faults': high_priority_faults,
                
                # Scoring and Recommendations
                'priority_score': round(priority_score, 1),
                'recommendation': recommendation,
                'recommendation_class': recommendation_class,
                'recommendation_icon': recommendation_icon,
                
                # Team Information
                'team_count': team_count,
                'team_details': team_details,
                'deployed_teams': list(deployed_teams.values('name', 'team_leader__first_name', 'team_leader__last_name')),
                
                # Performance Data
                'recent_closed_count': recent_closed_faults.count(),
                'oldest_unassigned': oldest_fault,
                
                # Additional Context Flags
                'has_critical_voltage': high_voltage_faults > 0,
                'has_high_client_impact': high_impact_faults > 0,
                'has_urgent_timing': urgent_faults > 0,
                'needs_immediate_attention': priority_score >= 30,
                'needs_team': team_count == 0 and active_faults.exists(),
                'overwhelmed': team_count > 0 and active_faults.count() > (team_count * 3),
            })
        
        # Sort depots by priority score (highest first) to help senior forepersons prioritize
        depot_info.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return depot_info
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting depot priority information: {e}")
        return []

@login_required
@transaction.atomic
def deploy_team(request, team_id=None):
    # Force console output to see if view is called
    import sys
    sys.stdout.write("🚨 DEPLOY_TEAM VIEW CALLED! 🚨\n")
    sys.stdout.flush()
    
    try:
        # Debug: Print request.user information
        print(f"Deploy team: request.user type: {type(request.user)}")
        print(f"Deploy team: request.user has is_authenticated: {hasattr(request.user, 'is_authenticated')}")
        
        # Check if user is authenticated
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            messages.error(request, "You must be logged in to deploy teams")
            return redirect('fault_locator_dashboard')
            
        print(f"Deploy team: request.user.id: {request.user.id}")
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        if not user_profile:
            messages.error(request, "User profile not found")
            return redirect('fault_locator_dashboard')
        
        # Debug: Print user profile type and attributes
        print(f"Deploy team: user_profile type: {type(user_profile)}")
        print(f"Deploy team: user_profile has get_user_role_for_application: {hasattr(user_profile, 'get_user_role_for_application')}")
        
        # Check permissions - allow both senior foreman and senior foreperson
        print("Deploy team: Checking permissions...")
        try:
            is_senior = is_senior_foreman(user_profile)
            print(f"Deploy team: is_senior_foreman result: {is_senior}")
        except Exception as e:
            print(f"Deploy team: Error in is_senior_foreman: {e}")
            messages.error(request, "Permission checking error")
            return redirect('fault_locator_dashboard')
            
        try:
            can_manage = can_manage_devices(user_profile)
            print(f"Deploy team: can_manage_devices result: {can_manage}")
        except Exception as e:
            print(f"Deploy team: Error in can_manage_devices: {e}")
            messages.error(request, "Permission checking error")
            return redirect('fault_locator_dashboard')
            
        if not (is_senior or can_manage):
            messages.error(request, "Only senior forepersons can deploy teams")
            return redirect('fault_locator_dashboard')

        team = None
        if team_id:
            team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
            
            # Check if team already deployed
            if team.current_depot:
                messages.warning(request, f"Team '{team.name}' is already deployed to {team.current_depot.depot}")
                return redirect('team_overview')
            
            # Check if team has a working device assigned
            is_valid, error_message = validate_team_device_for_deployment(team)
            if not is_valid:
                messages.error(request, error_message)
                return redirect('team_overview')

        if request.method == "POST":
            # Get user region safely
            user_region = None
            if user_profile and hasattr(user_profile, 'region') and user_profile.region:
                user_region = user_profile.region
                
            form = TeamDeploymentForm(request.POST, user_region=user_region)
            if form.is_valid():
                # Use atomic transaction for deployment
                with transaction.atomic():
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
            
            # Get user region safely
            user_region = None
            if user_profile and hasattr(user_profile, 'region') and user_profile.region:
                user_region = user_profile.region
            
            form = TeamDeploymentForm(initial=initial_data, user_region=user_region)
        
        # Get depot priority information to help with decision making
        depot_priority_info = get_depot_priority_information(user_profile)
        
        context = {
            'form': form,
            'selected_team': team,
            'user_profile': user_profile,
            'page_title': 'Deploy Team to Depot',
            'depot_priority_info': depot_priority_info,
        }
        
        return render(request, "fault_locator/deploy_team.html", context)
    except (IntegrityError, ValidationError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Deploy team error: {e}")
        messages.error(request, "An error occurred deploying the team.")
        return redirect('team_overview')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Deploy team error: {e}")
        messages.error(request, "An error occurred deploying the team.")
        return redirect('team_overview')

@login_required
@transaction.atomic
def recall_team(request, team_id):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check permissions - allow senior foreman and depot foreperson for their depot
        user_depot = get_user_depot(user_profile)
        can_recall_team = False
        
        if is_senior_foreman(user_profile) or can_manage_devices(user_profile):
            can_recall_team = True
        elif is_depot_foreperson(user_profile, user_depot):
            # Depot foreperson can only recall teams from their depot
            team = get_object_or_404(FaultLocatorTeam, id=team_id)
            can_recall_team = (team.current_depot == user_depot)
        
        if not can_recall_team:
            messages.error(request, "You don't have permission to recall this team")
            return redirect('fault_locator_dashboard')
        
        team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
        
        if not team.current_depot:
            messages.warning(request, f"Team '{team.name}' is not currently deployed")
            return redirect('team_overview')
        
        # Check for active assignments (not yet located)
        active_assignments = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        )
        
        if request.method == "POST":
            if active_assignments.exists() and not request.POST.get('force_recall'):
                messages.error(request, "Team has active fault assignments. Use force recall if necessary.")
                return redirect('recall_team', team_id=team.id)
            # Handle reassign after faults
            reassign_after_faults = request.POST.get('reassign_after_faults') == 'on'
            reassign_depot_id = request.POST.get('reassign_depot')
            recall_notes = request.POST.get('recall_notes', '')
            
            reassign_depot = None
            if reassign_after_faults and reassign_depot_id:
                try:
                    from it.users.models import Depots
                    reassign_depot = Depots.objects.get(id=reassign_depot_id)
                except Depots.DoesNotExist:
                    reassign_depot = None
            
            # Use atomic transaction for recall operations
            with transaction.atomic():
                # Find current deployment
                current_deployment = TeamDeployment.objects.filter(
                    team=team,
                    recalled_at__isnull=True
                ).first()
                
                if current_deployment:
                    current_deployment.recalled_at = timezone.now()
                    current_deployment.recalled_by = user_profile
                    
                    # Store recall notes and reassign intent
                    recall_notes_text = recall_notes
                    if reassign_after_faults and reassign_depot:
                        reassign_info = f"REASSIGN_TO:{reassign_depot.id}:{reassign_depot.depot}"
                        recall_notes_text = f"{recall_notes}\n{reassign_info}" if recall_notes else reassign_info
                    
                    current_deployment.recall_notes = recall_notes_text
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
            # Success message
            success_message = f"Team '{team.name}' recalled from {depot_name}"
            if reassign_after_faults and reassign_depot:
                success_message += f" and will be redeployed to {reassign_depot.depot} after current faults are completed"
            
            messages.success(request, success_message)
            return redirect('team_overview')
    
        from it.users.models import Depots
        
        # Filter depots by user's region
        depots = Depots.objects.all().order_by('depot')
        if user_profile and user_profile.region:
            depots = depots.filter(region=user_profile.region)
        
        context = {
            'team': team,
            'active_assignments': active_assignments,
            'user_profile': user_profile,
            'depots': depots,
        }
        return render(request, "fault_locator/recall_team.html", context)
    except (IntegrityError, ValidationError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Recall team error: {e}")
        messages.error(request, "An error occurred recalling the team.")
        return redirect('team_overview')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Recall team error: {e}")
        messages.error(request, "An error occurred recalling the team.")
        return redirect('team_overview')

@login_required
def debug_user(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        context = {
            'user_profile': user_profile,
            'is_senior_foreman': is_senior_foreman(user_profile),
            'can_manage_devices': can_manage_devices(user_profile),
            'can_deploy_teams': can_deploy_teams(user_profile),
            'can_recall_teams': is_senior_foreman(user_profile) or can_manage_devices(user_profile),
        }
        
        return render(request, "fault_locator/debug_user.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Debug user error: {e}")
        messages.error(request, "An error occurred loading debug info.")
        return redirect('fault_locator_dashboard')

@login_required
def role_troubleshooting(request):
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()

        # Get role information
        from fault_locator.central_roles import FaultLocatorRoleManager
        user_role = FaultLocatorRoleManager.get_user_role(user_profile)
        user_role_display = FaultLocatorRoleManager.get_user_role_display(user_profile)
        has_any_role = FaultLocatorRoleManager.has_any_role(user_profile)

        # Get available roles
        available_roles = FaultLocatorRoleManager.get_available_roles()

        # Check permissions
        permissions = {
            'is_senior_foreman': is_senior_foreman(user_profile),
            'can_manage_devices': can_manage_devices(user_profile),
            'can_deploy_teams': can_deploy_teams(user_profile),
            'can_create_teams': can_create_teams(user_profile),
        }

        context = {
            'user_profile': user_profile,
            'user_role': user_role,
            'user_role_display': user_role_display,
            'has_any_role': has_any_role,
            'available_roles': available_roles,
            'permissions': permissions,
            'page_title': 'Role Troubleshooting',
        }

        return render(request, "fault_locator/role_troubleshooting.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Role troubleshooting error: {e}")
        messages.error(request, "An error occurred loading role troubleshooting info.")
        return redirect('fault_locator_dashboard')

# ADVANCED FAULT ASSIGNMENT

@login_required
@transaction.atomic
def advanced_fault_assignment(request):
    try:
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
        
        # Get available teams with working devices
        available_teams = FaultLocatorTeam.objects.filter(
            faultlocatordeviceassignment__isnull=False,
            faultlocatordeviceassignment__device__status__in=['available', 'assigned']
        ).prefetch_related('members', 'faultlocatordeviceassignment_set__device')
        
        # Add team availability info
        team_data = []
        for team in available_teams:
            device = team.faultlocatordeviceassignment_set.first().device
            
            # Skip teams with non-working devices
            if device.status not in ['available', 'assigned']:
                continue
                
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
            
            # Use atomic transaction for bulk assignment operations
            with transaction.atomic():
                team = get_object_or_404(FaultLocatorTeam.objects.select_for_update(), id=team_id)
                device_assignment = FaultLocatorDeviceAssignment.objects.select_for_update().filter(team=team).first()
                
                if not device_assignment:
                    messages.error(request, f"Team '{team.name}' doesn't have a device assigned")
                    return redirect('advanced_fault_assignment')
                
                # Check if assigned device is in working condition
                if device_assignment.device.status not in ['available', 'assigned']:
                    messages.error(request, f"Team '{team.name}' cannot be assigned faults. Device '{device_assignment.device.serial_number}' is {device_assignment.device.get_status_display()}")
                    return redirect('advanced_fault_assignment')
                
                assigned_count = 0
                for fault_id in fault_ids:
                    try:
                        # Lock fault for update to prevent concurrent assignments
                        fault = get_object_or_404(Fault.objects.select_for_update(), id=fault_id)
                        
                        # Re-check fault status under lock
                        if fault.status != 'requested':
                            continue
                        
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
                    except IntegrityError:
                        # Fault may have been assigned by another user
                        continue
                    except ValidationError:
                        # Invalid data in assignment
                        continue
                
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Advanced fault assignment error: {e}")
        messages.error(request, "An error occurred assigning faults.")
        return redirect('fault_locator_dashboard')

# HELPER FUNCTIONS FOR DEVICE VALIDATION

def validate_team_device_for_deployment(team):
    """
    Validate that a team has a working device assigned for deployment.
    Returns (is_valid, error_message)
    """
    device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
    
    if not device_assignment:
        return False, f"Team '{team.name}' must have a device assigned before deployment"
    
    if device_assignment.device.status not in ['available', 'assigned']:
        return False, f"Team '{team.name}' cannot be deployed. Device '{device_assignment.device.serial_number}' is {device_assignment.device.get_status_display()}"
    
    return True, None

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
    """Check if user is a senior foreman/foreperson - can delegate machines to depots"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        # Check for senior + (foreman OR foreperson)
        has_senior = 'senior' in designation_desc
        has_foreman_role = ('foreman' in designation_desc or 'foreperson' in designation_desc)
        return has_senior and has_foreman_role
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

def can_user_be_added_to_team(user_profile, team=None):
    """Check if a user can be added to a team"""
    if not user_profile:
        return False, "Invalid user"
    
    # Check if user is already in another team
    existing_teams = user_profile.fault_locator_teams.all()
    if team:
        # If editing existing team, exclude the current team from the check
        existing_teams = existing_teams.exclude(id=team.id)
    
    if existing_teams.exists():
        existing_team = existing_teams.first()
        return False, f"User is already a member of team '{existing_team.name}'. A person can only be in one team at a time."
    
    # Check if user is a team leader of another team
    led_teams = FaultLocatorTeam.objects.filter(team_leader=user_profile)
    if team:
        # If editing existing team, exclude the current team from the check
        led_teams = led_teams.exclude(id=team.id)
    
    if led_teams.exists():
        led_team = led_teams.first()
        return False, f"User is the team leader of team '{led_team.name}'. A person can only be in one team at a time."
    
    # Check if user is a depot foreperson or senior foreperson
    if is_depot_foreperson(user_profile):
        return False, "Depot forepersons cannot be added to teams. They manage teams from their depot."
    
    if is_senior_foreman(user_profile):
        return False, "Senior forepersons cannot be added to teams. They manage teams system-wide."
    
    return True, "User can be added to team"

def get_user_current_team(user_profile):
    """Get the current team a user is part of (either as leader or member)"""
    if not user_profile:
        return None
    
    # Check if user is team leader
    team_as_leader = FaultLocatorTeam.objects.filter(team_leader=user_profile).first()
    if team_as_leader:
        return team_as_leader
    
    # Check if user is team member
    return user_profile.fault_locator_teams.first()

@login_required
def change_fault_priority(request, fault_id):
    """Allow fault creators to change fault priority"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        fault = get_object_or_404(Fault, id=fault_id)
        
        # Check if user is the fault creator
        if fault.reported_by != user_profile:
            messages.error(request, "You can only change priority for faults you created")
            return redirect('simple_fault_list')
        
        # Check if fault is still in a state where priority can be changed
        if fault.status in ['closed', 'resolved']:
            messages.error(request, "Priority cannot be changed for closed or resolved faults")
            return redirect('simple_fault_list')
        
        if request.method == "POST":
            form = FaultPriorityForm(request.POST, instance=fault)
            if form.is_valid():
                old_priority = fault.priority
                new_priority = form.cleaned_data['priority']
                
                # Save priority change
                fault.priority = new_priority
                fault.prioritized_by = user_profile
                fault.prioritized_at = timezone.now()
                fault.save()
                
                # Notify relevant users about priority change
                notify_priority_change(fault, old_priority, new_priority, user_profile, request)
                
                messages.success(request, f"✅ Fault priority changed from {old_priority} to {new_priority}")
                return redirect('simple_fault_list')
        else:
            form = FaultPriorityForm(instance=fault)
        
        context = {
            'fault': fault,
            'form': form,
            'user_profile': user_profile,
        }
        
        return render(request, "fault_locator/change_priority.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Change priority error: {e}")
        messages.error(request, "An error occurred while changing fault priority.")
        return redirect('simple_fault_list')

def notify_priority_change(fault, old_priority, new_priority, changed_by, request):
    """Notify relevant users about fault priority change"""
    try:
        # Get priority display names
        priority_choices = dict(Fault.PRIORITY_CHOICES)
        old_priority_name = priority_choices.get(old_priority, f"Priority {old_priority}")
        new_priority_name = priority_choices.get(new_priority, f"Priority {new_priority}")
        
        # Create notification message
        if new_priority > old_priority:
            # Priority increased (more urgent)
            message = f"⬆️ PRIORITY INCREASED: Fault #{fault.id} at {fault.depot.depot} changed from {old_priority_name} to {new_priority_name} by {changed_by.get_full_name()}"
            notification_type = "Priority Increased"
        else:
            # Priority decreased (less urgent)
            message = f"⬇️ Priority Changed: Fault #{fault.id} at {fault.depot.depot} changed from {old_priority_name} to {new_priority_name} by {changed_by.get_full_name()}"
            notification_type = "Priority Changed"
        
        # Get users to notify
        users_to_notify = []
        
        # 1. Notify depot forepersons at the fault location
        depot_forepersons = UserProfile.objects.filter(
            depot=fault.depot.code,
            designation__description__icontains='foreperson'
        ).exclude(id=changed_by.id)
        users_to_notify.extend(depot_forepersons)
        
        # 2. If priority is high (3+), notify senior forepersons
        if new_priority >= 3:
            senior_forepersons = UserProfile.objects.filter(
                designation__description__icontains='senior foreperson'
            ).exclude(id=changed_by.id)
            users_to_notify.extend(senior_forepersons)
        
        # 3. Notify assigned team members if fault is assigned
        current_assignment = FaultAssignment.objects.filter(
            fault=fault,
            located_at__isnull=True
        ).first()
        
        if current_assignment and current_assignment.team:
            team_members = current_assignment.team.members.all()
            users_to_notify.extend(team_members)
        
        # Remove duplicates and the person who made the change
        users_to_notify = list(set(users_to_notify))
        if changed_by in users_to_notify:
            users_to_notify.remove(changed_by)
        
        # Send notifications
        for user in users_to_notify:
            # Create in-app notification
            Notification.objects.create(
                user=user,
                message=message,
                notification_type=notification_type,
                created_at=timezone.now()
            )
            
            # Send email notification
            try:
                email_subject = f"Fault Priority Changed - #{fault.id}"
                email_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="color: #333; margin-top: 0;">Fault Priority Changed</h2>
                        <p style="color: #666; font-size: 14px; margin-bottom: 0;">
                            {message}
                        </p>
                    </div>
                    
                    <div style="background-color: #fff; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px;">
                        <h3 style="color: #495057; margin-top: 0;">Fault Details</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="margin-bottom: 8px;"><strong>Fault ID:</strong> #{fault.id}</li>
                            <li style="margin-bottom: 8px;"><strong>Location:</strong> {fault.depot.depot}</li>
                            <li style="margin-bottom: 8px;"><strong>Description:</strong> {fault.description}</li>
                            <li style="margin-bottom: 8px;"><strong>Old Priority:</strong> {old_priority_name}</li>
                            <li style="margin-bottom: 8px;"><strong>New Priority:</strong> {new_priority_name}</li>
                            <li style="margin-bottom: 8px;"><strong>Changed By:</strong> {changed_by.get_full_name()}</li>
                            <li style="margin-bottom: 8px;"><strong>Changed At:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                        <p style="margin: 0; color: #155724;">
                            <strong>Next Steps:</strong> {"Review and take appropriate action based on the new priority level." if new_priority > old_priority else "Note the priority adjustment for your records."}
                        </p>
                    </div>
                </div>
                """
                
                if user.email:
                    ms_exhange_send_html(
                        to_email=user.email,
                        subject=email_subject,
                        body=email_body
                    )
            except Exception as email_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send priority change email to {user.email}: {email_error}")
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Priority change notification error: {e}")


# =====================================
# FAULT REPORTER SPECIFIC VIEWS
# =====================================

@login_required
def fault_reporter_dashboard(request):
    """Dashboard specifically for fault reporters to manage their reported faults"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check if user is a fault reporter
        if not is_fault_reporter(user_profile):
            messages.error(request, "Access denied. This dashboard is for fault reporters only.")
            return redirect('fault_locator_dashboard')
        
        # Check if user has a depot assigned
        if not hasattr(user_profile, 'depot') or not user_profile.depot:
            messages.error(request, "You must be assigned to a depot to access fault reporting features.")
            return redirect('fault_locator_dashboard')
        
        # Get faults reported by this user from their assigned depot only
        my_faults = Fault.objects.filter(
            reported_by=user_profile,
            depot=user_profile.depot
        ).select_related('depot')
        
        # Filter by status if requested
        status_filter = request.GET.get('status', 'all')
        if status_filter != 'all':
            my_faults = my_faults.filter(status=status_filter)
        
        # Filter by priority if requested
        priority_filter = request.GET.get('priority', 'all')
        if priority_filter != 'all':
            my_faults = my_faults.filter(priority=int(priority_filter))
        
        # Order by priority and date
        my_faults = my_faults.order_by('-vvip', '-priority', '-reported_at')
        
        # Get statistics
        from datetime import timedelta
        today = timezone.now().date()
        this_week = timezone.now() - timedelta(days=7)
        this_month = timezone.now() - timedelta(days=30)
        
        stats = {
            'total_reported': my_faults.count(),
            'pending': my_faults.filter(status='requested').count(),
            'in_progress': my_faults.filter(status='assigned').count(),
            'located': my_faults.filter(status='located').count(),
            'completed': my_faults.filter(status='closed').count(),
            'today': my_faults.filter(reported_at__date=today).count(),
            'this_week': my_faults.filter(reported_at__gte=this_week).count(),
            'this_month': my_faults.filter(reported_at__gte=this_month).count(),
            'high_priority': my_faults.filter(priority__gte=3).count(),
            'vvip': my_faults.filter(vvip=True).count(),
        }
        
        # Get current assignments for each fault
        fault_data = []
        for fault in my_faults:
            current_assignment = FaultAssignment.objects.filter(
                fault=fault, 
                located_at__isnull=True
            ).select_related('team', 'device').first()
            
            # Calculate time elapsed
            time_elapsed = timezone.now() - fault.reported_at
            urgency = 'normal'
            if fault.priority >= 3:
                urgency = 'critical'
            elif time_elapsed.total_seconds() > 14400:  # 4 hours
                urgency = 'urgent'
            
            fault_data.append({
                'fault': fault,
                'current_assignment': current_assignment,
                'urgency': urgency,
                'time_elapsed': time_elapsed,
                'hours_elapsed': int(time_elapsed.total_seconds() / 3600),
            })
        
        # Filter options for the UI
        status_options = [
            ('all', 'All Statuses'),
            ('requested', 'Pending Assignment'),
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
            'user_profile': user_profile,
            'fault_data': fault_data,
            'stats': stats,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'status_options': status_options,
            'priority_options': priority_options,
            'total_count': len(fault_data),
        }
        
        return render(request, "fault_locator/fault_reporter_dashboard.html", context)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fault reporter dashboard error: {e}")
        messages.error(request, "An error occurred loading your fault reports.")
        return redirect('fault_locator_dashboard')

@login_required
def bulk_fault_report(request):
    """View for reporting multiple faults at once"""
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
            messages.error(request, "You don't have permission to report faults.")
            return redirect('fault_locator_dashboard')
        
        # Check depot assignment for fault reporters
        if is_fault_reporter(user_profile) and (not hasattr(user_profile, 'depot') or not user_profile.depot):
            messages.error(request, "You must be assigned to a depot to report faults.")
            return redirect('fault_locator_dashboard')
        
        if request.method == "POST":
            # Process bulk fault reporting
            fault_count = int(request.POST.get('fault_count', 1))
            successful_reports = 0
            failed_reports = []
            
            for i in range(1, fault_count + 1):
                description = request.POST.get(f'fault_{i}_description')
                depot_id = request.POST.get(f'fault_{i}_depot')
                priority = request.POST.get(f'fault_{i}_priority', 2)
                voltage = request.POST.get(f'fault_{i}_voltage', '')
                clients_affected = request.POST.get(f'fault_{i}_clients_affected', '')
                vvip = bool(request.POST.get(f'fault_{i}_vvip'))
                backfeed = bool(request.POST.get(f'fault_{i}_backfeed'))
                
                # Skip empty descriptions
                if not description or not description.strip():
                    continue
                
                try:
                    depot = Depots.objects.get(id=depot_id)
                    
                    # Validate depot access for fault reporters
                    if is_fault_reporter(user_profile):
                        if not hasattr(user_profile, 'depot') or not user_profile.depot or user_profile.depot != depot:
                            failed_reports.append(f"Fault {i}: You can only report faults for your assigned depot ({user_profile.depot.depot if user_profile.depot else 'None assigned'})")
                            continue
                    
                    # Create the fault
                    fault = Fault.objects.create(
                        description=description.strip(),
                        depot=depot,
                        reported_by=user_profile,
                        priority=int(priority),
                        voltage=voltage if voltage else None,
                        clients_affected=int(clients_affected) if clients_affected else None,
                        vvip=vvip,
                        backfeed=backfeed
                    )
                    
                    # Send notifications for high priority faults
                    if fault.priority >= 3:
                        notify_high_priority_fault(fault, request)
                    
                    successful_reports += 1
                    
                except Exception as e:
                    failed_reports.append(f"Fault {i}: {str(e)}")
            
            # Show results
            if successful_reports > 0:
                messages.success(request, f"Successfully reported {successful_reports} fault(s)!")
            
            if failed_reports:
                for error in failed_reports:
                    messages.error(request, error)
            
            if successful_reports > 0:
                return redirect('fault_reporter_dashboard' if is_fault_reporter(user_profile) else 'simple_fault_list')
        
        # GET request - show bulk report form
        
        # Get available depots for the user
        available_depots = Depots.objects.all().order_by('depot')
        
        # Apply restrictions based on user role
        if is_fault_reporter(user_profile):
            # Fault reporters can only report for their assigned depot
            if hasattr(user_profile, 'depot') and user_profile.depot:
                available_depots = available_depots.filter(id=user_profile.depot.id)
            else:
                available_depots = Depots.objects.none()
        elif user_profile and user_profile.region:
            # Other roles filter by region
            available_depots = available_depots.filter(region=user_profile.region)
        
        context = {
            'user_profile': user_profile,
            'available_depots': available_depots,
            'priority_choices': Fault._meta.get_field('priority').choices,
            'voltage_choices': Fault._meta.get_field('voltage').choices,
        }
        
        return render(request, "fault_locator/bulk_fault_report.html", context)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Bulk fault report error: {e}")
        messages.error(request, "An error occurred with bulk fault reporting.")
        return redirect('fault_locator_dashboard')

@login_required
def my_fault_reports(request):
    """View for fault reporters to see their reported faults with enhanced details"""
    try:
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        # Check if user can view their reports
        can_view = (
            is_fault_reporter(user_profile) or 
            is_team_member(user_profile) or 
            is_team_leader(user_profile) or 
            is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None) or 
            is_senior_foreman(user_profile)
        )
        
        if not can_view:
            messages.error(request, "You don't have permission to view fault reports.")
            return redirect('fault_locator_dashboard')
        
        # Check depot assignment for fault reporters
        if is_fault_reporter(user_profile) and (not hasattr(user_profile, 'depot') or not user_profile.depot):
            messages.error(request, "You must be assigned to a depot to view fault reports.")
            return redirect('fault_locator_dashboard')
        
        # Get faults reported by this user
        my_faults = Fault.objects.filter(
            reported_by=user_profile
        ).select_related('depot').prefetch_related(
            'faultassignment_set__team',
            'faultassignment_set__device'
        )
        
        # Apply depot restriction for fault reporters
        if is_fault_reporter(user_profile) and hasattr(user_profile, 'depot') and user_profile.depot:
            my_faults = my_faults.filter(depot=user_profile.depot)
        
        my_faults = my_faults.order_by('-reported_at')
        
        # Apply filters
        status_filter = request.GET.get('status', 'all')
        if status_filter != 'all':
            my_faults = my_faults.filter(status=status_filter)
        
        depot_filter = request.GET.get('depot', 'all')
        if depot_filter != 'all':
            my_faults = my_faults.filter(depot_id=depot_filter)
        
        # Search functionality
        search_query = request.GET.get('q', '')
        if search_query:
            my_faults = my_faults.filter(
                Q(description__icontains=search_query) |
                Q(depot__depot__icontains=search_query)
            )
        
        # Enhanced fault data with assignment tracking
        fault_data = []
        for fault in my_faults:
            # Get all assignments for this fault
            assignments = FaultAssignment.objects.filter(
                fault=fault
            ).select_related('team', 'device').order_by('assigned_at')
            
            current_assignment = assignments.filter(located_at__isnull=True).first()
            
            # Calculate time metrics
            time_elapsed = timezone.now() - fault.reported_at
            
            # Time to assignment
            time_to_assignment = None
            if assignments.exists():
                first_assignment = assignments.first()
                time_to_assignment = first_assignment.assigned_at - fault.reported_at
            
            # Time to completion
            time_to_completion = None
            completed_assignment = assignments.filter(located_at__isnull=False).first()
            if completed_assignment:
                time_to_completion = completed_assignment.located_at - fault.reported_at
            
            fault_data.append({
                'fault': fault,
                'current_assignment': current_assignment,
                'all_assignments': assignments,
                'time_elapsed': time_elapsed,
                'time_to_assignment': time_to_assignment,
                'time_to_completion': time_to_completion,
                'assignment_count': assignments.count(),
                'is_overdue': time_elapsed.total_seconds() > 28800 and fault.status != 'closed',  # 8 hours
            })
        
        # Get filter options
        available_depots = Depots.objects.filter(
            id__in=my_faults.values_list('depot_id', flat=True).distinct()
        ).order_by('depot')
        
        status_options = [
            ('all', 'All Statuses'),
            ('requested', 'Pending Assignment'),
            ('assigned', 'In Progress'),
            ('located', 'Located'),
            ('closed', 'Completed'),
        ]
        
        context = {
            'user_profile': user_profile,
            'fault_data': fault_data,
            'available_depots': available_depots,
            'status_options': status_options,
            'status_filter': status_filter,
            'depot_filter': depot_filter,
            'search_query': search_query,
            'total_count': len(fault_data),
        }
        
        return render(request, "fault_locator/my_fault_reports.html", context)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"My fault reports error: {e}")
        messages.error(request, "An error occurred loading your fault reports.")
        return redirect('fault_locator_dashboard')
