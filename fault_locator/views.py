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
    """SIMPLIFIED: Main dashboard - role-based and action-oriented"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Determine user role and permissions
    is_senior = is_senior_foreperson(user_profile)
    is_depot_fp = is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)
    can_create = can_create_device(user_profile)
    
    # Get user's depot if applicable
    user_depot = None
    if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
        user_depot = Depots.objects.filter(code=user_profile.depot).first()
    
    # Initialize context
    context = {
        'user_profile': user_profile,
        'is_senior_foreperson': is_senior,
        'is_depot_foreperson': is_depot_fp,
        'can_create_device': can_create,
        'user_depot': user_depot,
        'my_actions': [],
        'quick_stats': {},
        'recent_activity': [],
    }
    
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
            'total_faults': Fault.objects.count(),
            'active_faults': Fault.objects.filter(status__in=['requested', 'assigned']).count(),
            'teams_deployed': TeamDeployment.objects.filter(recalled_at__isnull=True).count(),
            'devices_active': FaultLocatorDeviceAssignment.objects.count(),
        }
    elif is_depot_fp and user_depot:
        # Depot-specific stats
        context['quick_stats'] = {
            'my_depot_faults': Fault.objects.filter(depot=user_depot).count(),
            'pending_assignment': Fault.objects.filter(depot=user_depot, status='requested').count(),
            'in_progress': Fault.objects.filter(depot=user_depot, status='assigned').count(),
            'teams_at_depot': FaultLocatorTeam.objects.filter(current_depot=user_depot).count(),
        }
    elif user_teams.exists():
        # Team member stats
        my_team = user_teams.first()
        context['quick_stats'] = {
            'my_team': my_team.name,
            'current_assignments': FaultAssignment.objects.filter(team=my_team, located_at__isnull=True).count(),
            'completed_today': FaultAssignment.objects.filter(
                team=my_team,
                located_at__date=timezone.now().date()
            ).count(),
            'team_location': my_team.current_depot.depot if my_team.current_depot else 'Not Deployed',
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
    elif not is_senior_foreperson(user_profile):
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
        can_assign = is_senior_foreperson(user_profile) or is_depot_foreperson(user_profile, fault.depot)
        
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
        'is_senior_foreperson': is_senior_foreperson(user_profile),
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
    available_depots = Depots.objects.all()
    user_depot = None
    
    # Pre-select user's depot
    if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
        user_depot = Depots.objects.filter(code=user_profile.depot).first()
        if not is_senior_foreperson(user_profile):
            available_depots = [user_depot] if user_depot else []
    
    context = {
        'user_profile': user_profile,
        'available_depots': available_depots,
        'user_depot': user_depot,
        'priority_choices': Fault._meta.get_field('priority').choices,
    }
    
    return render(request, "fault_locator/quick_fault_report.html", context)

@login_required
def simple_assign_fault(request, fault_id=None):
    """SIMPLIFIED: Easy fault assignment with available teams"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None)):
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
        'is_senior_foreperson': is_senior_foreperson(user_profile),
    }
    
    return render(request, "fault_locator/simple_assign_fault.html", context)

@login_required
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
    
    can_update = can_update or is_senior_foreperson(user_profile)
    
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
    
    # Get teams based on user role
    teams = FaultLocatorTeam.objects.prefetch_related(
        'members', 
        'faultlocatordeviceassignment_set__device'
    ).annotate(
        member_count=Count('members'),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True))
    )
    
    # Role-based filtering
    if not is_senior_foreperson(user_profile):
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
                if is_senior_foreperson(user_profile):
                    actions.append({
                        'text': 'Recall',
                        'url': f'/fault_locator/teams/{team.id}/recall/',
                        'class': 'btn-warning btn-sm'
                    })
            else:
                status = 'available'
                status_class = 'text-blue-600'
                if is_senior_foreperson(user_profile):
                    actions.append({
                        'text': 'Deploy',
                        'url': f'/fault_locator/teams/{team.id}/deploy/',
                        'class': 'btn-primary btn-sm'
                    })
        else:
            if can_create_device(user_profile):
                actions.append({
                    'text': 'Assign Device',
                    'url': f'/fault_locator/assign-device-to-team/?team_id={team.id}',
                    'class': 'btn-success btn-sm'
                })
        
        # Add manage action for authorized users
        if is_senior_foreperson(user_profile) or can_create_device(user_profile):
            actions.append({
                'text': 'Manage',
                'url': f'/fault_locator/teams/{team.id}/edit/',
                'class': 'btn-outline-secondary btn-sm'
            })
        
        team_data.append({
            'team': team,
            'device': device_assignment.device if device_assignment else None,
            'status': status,
            'status_class': status_class,
            'location': team.current_depot.depot if team.current_depot else 'Base',
            'actions': actions,
        })
    
    context = {
        'team_data': team_data,
        'user_profile': user_profile,
        'is_senior_foreperson': is_senior_foreperson(user_profile),
        'can_create_team': is_senior_foreperson(user_profile) or can_create_device(user_profile),
        'total_teams': len(team_data),
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

# Team Management Views
@login_required
def create_team(request):
    """Create a new fault locator team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    from .central_roles import can_create_teams
    if not can_create_teams(user_profile):
        messages.error(request, "You don't have permission to create teams.")
        return redirect('team_overview')
    
    if request.method == 'POST':
        form = FaultLocatorTeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            messages.success(request, f"Team '{team.name}' created successfully.")
            return redirect('team_overview')
    else:
        form = FaultLocatorTeamForm()
    
    context = {
        'form': form,
        'user_profile': user_profile,
        'title': 'Create New Team',
    }
    return render(request, "fault_locator/create_team.html", context)

@login_required
def edit_team(request, team_id):
    """Edit an existing fault locator team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    from .central_roles import can_create_teams
    if not can_create_teams(user_profile):
        messages.error(request, "You don't have permission to edit teams.")
        return redirect('team_overview')
    
    try:
        team = FaultLocatorTeam.objects.get(id=team_id)
    except FaultLocatorTeam.DoesNotExist:
        messages.error(request, "Team not found.")
        return redirect('team_overview')
    
    if request.method == 'POST':
        form = FaultLocatorTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f"Team '{team.name}' updated successfully.")
            return redirect('team_overview')
    else:
        form = FaultLocatorTeamForm(instance=team)
    
    # Get team members for display
    members = team.members.all()
    
    context = {
        'form': form,
        'team': team,
        'members': members,
        'user_profile': user_profile,
        'title': f'Edit Team: {team.name}',
    }
    return render(request, "fault_locator/edit_team.html", context)

@login_required
def add_team_member(request, team_id):
    """Add a member to a team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    from .central_roles import can_create_teams
    if not can_create_teams(user_profile):
        messages.error(request, "You don't have permission to manage team members.")
        return redirect('team_overview')
    
    try:
        team = FaultLocatorTeam.objects.get(id=team_id)
    except FaultLocatorTeam.DoesNotExist:
        messages.error(request, "Team not found.")
        return redirect('team_overview')
    
    if request.method == 'POST':
        form = AddTeamMemberForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data['member']
            
            # Check if member is already in the team
            if team.members.filter(id=member.id).exists():
                messages.warning(request, f"{member.get_full_name()} is already a member of this team.")
            else:
                team.members.add(member)
                messages.success(request, f"{member.get_full_name()} added to team '{team.name}'.")
            
            return redirect('edit_team', team_id=team.id)
    else:
        form = AddTeamMemberForm()
    
    context = {
        'form': form,
        'team': team,
        'user_profile': user_profile,
        'title': f'Add Member to {team.name}',
    }
    return render(request, "fault_locator/add_team_member.html", context)

@login_required
def remove_team_member(request, team_id, member_id):
    """Remove a member from a team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    from .central_roles import can_create_teams
    if not can_create_teams(user_profile):
        messages.error(request, "You don't have permission to manage team members.")
        return redirect('team_overview')
    
    try:
        team = FaultLocatorTeam.objects.get(id=team_id)
        member = UserProfile.objects.get(id=member_id)
    except (FaultLocatorTeam.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "Team or member not found.")
        return redirect('team_overview')
    
    # Check if member is actually in the team
    if not team.members.filter(id=member.id).exists():
        messages.warning(request, f"{member.get_full_name()} is not a member of this team.")
        return redirect('edit_team', team_id=team.id)
    
    # Check if member is the team leader
    if team.team_leader and team.team_leader.id == member.id:
        messages.error(request, "Cannot remove the team leader. Please assign a new leader first.")
        return redirect('edit_team', team_id=team.id)
    
    if request.method == 'POST':
        team.members.remove(member)
        messages.success(request, f"{member.get_full_name()} removed from team '{team.name}'.")
        return redirect('edit_team', team_id=team.id)
    
    context = {
        'team': team,
        'member': member,
        'user_profile': user_profile,
        'title': f'Remove Member from {team.name}',
    }
    return render(request, "fault_locator/remove_team_member.html", context)

@login_required
def delete_team(request, team_id):
    """Delete a team with safety checks"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    from .central_roles import can_create_teams
    if not can_create_teams(user_profile):
        messages.error(request, "You don't have permission to delete teams.")
        return redirect('team_overview')
    
    try:
        team = FaultLocatorTeam.objects.get(id=team_id)
    except FaultLocatorTeam.DoesNotExist:
        messages.error(request, "Team not found.")
        return redirect('team_overview')
    
    # Safety checks before deletion
    safety_issues = []
    
    # Check for active deployments
    active_deployments = TeamDeployment.objects.filter(
        team=team, 
        recalled_at__isnull=True
    )
    if active_deployments.exists():
        safety_issues.append(f"Team is currently deployed to {active_deployments.first().depot.depot}")
    
    # Check for active fault assignments
    active_assignments = FaultAssignment.objects.filter(
        team=team,
        located_at__isnull=True
    )
    if active_assignments.exists():
        safety_issues.append(f"Team has {active_assignments.count()} active fault assignment(s)")
    
    # Check for device assignments
    device_assignments = FaultLocatorDeviceAssignment.objects.filter(team=team)
    if device_assignments.exists():
        safety_issues.append(f"Team has {device_assignments.count()} device assignment(s) that must be unassigned first")
    
    if request.method == 'POST':
        if safety_issues:
            messages.error(request, "Cannot delete team due to safety issues: " + "; ".join(safety_issues))
            return redirect('edit_team', team_id=team.id)
        
        # Proceed with deletion
        team_name = team.name
        team.delete()
        messages.success(request, f"Team '{team_name}' deleted successfully.")
        return redirect('team_overview')
    
    context = {
        'team': team,
        'safety_issues': safety_issues,
        'can_delete': len(safety_issues) == 0,
        'user_profile': user_profile,
        'title': f'Delete Team: {team.name}',
    }
    return render(request, "fault_locator/delete_team.html", context)

# Keep existing utility functions
def can_create_device(user_profile):
    """Check if user has permission to create devices"""
    if not user_profile:
        return False
    
    # Senior forepersons can create devices
    if is_senior_foreperson(user_profile):
        return True
    
    # IT personnel can create devices
    if hasattr(user_profile, 'section') and user_profile.section:
        try:
            # Try different possible field names for section
            section_name = ""
            if hasattr(user_profile.section, 'section'):
                section_name = str(user_profile.section.section).lower()
            elif hasattr(user_profile.section, 'name'):
                section_name = str(user_profile.section.name).lower()
            elif hasattr(user_profile.section, 'description'):
                section_name = str(user_profile.section.description).lower()
            else:
                section_name = str(user_profile.section).lower()
            
            if 'it' in section_name or 'information technology' in section_name:
                return True
        except Exception:
            # If any error occurs, just skip this check
            pass
    
    # Administrators can create devices  
    if hasattr(user_profile, 'designation') and user_profile.designation:
        try:
            designation_desc = str(user_profile.designation.description).lower()
            if 'administrator' in designation_desc or 'manager' in designation_desc:
                return True
        except Exception:
            # If any error occurs, just skip this check
            pass
    
    return False

def is_senior_foreperson(user_profile):
    """Check if user profile belongs to a senior foreperson"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        return 'senior' in designation_desc and 'foreperson' in designation_desc
    except Exception:
        return False

def is_foreperson(user_profile):
    """Check if user profile belongs to any foreperson (senior or depot)"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        return 'foreperson' in designation_desc
    except Exception:
        return False

def is_depot_foreperson(user_profile, depot):
    """Check if user profile is foreperson for specific depot"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    try:
        designation_desc = str(user_profile.designation.description).lower()
        is_foreperson_role = 'foreperson' in designation_desc and 'senior' not in designation_desc
        
        # Check if user's depot matches the specified depot
        if depot and hasattr(user_profile, 'depot') and user_profile.depot:
            if isinstance(depot, str):
                return is_foreperson_role and user_profile.depot == depot
            else:
                return is_foreperson_role and user_profile.depot == depot.code
        
        return is_foreperson_role
    except Exception:
        return False

def get_user_depot(user_profile):
    """Get the depot object for a user profile"""
    if not user_profile or not hasattr(user_profile, 'depot') or not user_profile.depot:
        return None
    
    try:
        from it.users.models import Depots
        return Depots.objects.filter(code=user_profile.depot).first()
    except Exception:
        return None

def has_fault_locator_permissions(user_profile):
    """Check if user has any fault locator system permissions"""
    return (is_senior_foreperson(user_profile) or 
            is_foreperson(user_profile) or 
            can_create_device(user_profile))