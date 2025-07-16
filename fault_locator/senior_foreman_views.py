"""
Senior Foreman specific views for fault locator system
Provides comprehensive management interface for:
- Team deployment to depots
- Device assignment to teams
- Performance monitoring
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import json

from .models import (
    FaultLocatorTeam, FaultLocatorDevice, FaultLocatorDeviceAssignment,
    TeamDeployment, Fault, FaultAssignment
)
from .forms import TeamDeploymentForm, SeniorForepersonDeviceAssignmentForm
from .central_roles import is_senior_foreman
from .decorators import senior_foreman_required
from it.users.models import UserProfile, Depots


@login_required
@senior_foreman_required
def senior_foreman_dashboard(request):
    """Comprehensive Senior Foreman Dashboard"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get system statistics
    stats = get_system_statistics()
    
    # Get teams and their current status
    teams_data = get_teams_overview()
    
    # Get devices and their assignment status
    devices_data = get_devices_overview()
    
    # Get depot deployment status
    depot_status = get_depot_deployment_status(user_profile)
    
    # Get performance metrics
    performance_data = get_performance_metrics()
    
    # Get recent activities
    recent_activities = get_recent_activities()
    
    context = {
        'user_profile': user_profile,
        'stats': stats,
        'teams_data': teams_data,
        'devices_data': devices_data,
        'depot_status': depot_status,
        'performance_data': performance_data,
        'recent_activities': recent_activities,
        'page_title': 'Senior Foreman Dashboard',
    }
    
    return render(request, "fault_locator/senior_foreman_dashboard.html", context)


@login_required
@senior_foreman_required
def team_depot_management(request):
    """Team to Depot Assignment Management"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get all teams with their current deployment status
    teams = FaultLocatorTeam.objects.annotate(
        device_count=Count('faultlocatordeviceassignment'),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True))
    ).prefetch_related('members', 'faultlocatordeviceassignment_set__device')
    
    # Get all depots with deployment info (filtered by user's region)
    depots_query = Depots.objects.annotate(
        deployed_teams=Count('faultlocatorteam', filter=Q(faultlocatorteam__current_depot__isnull=False))
    )
    
    # Filter by user's region if available
    if user_profile and hasattr(user_profile, 'region') and user_profile.region:
        depots_query = depots_query.filter(region=user_profile.region)
    
    depots = depots_query.order_by('depot')
    
    # Get deployment history
    recent_deployments = TeamDeployment.objects.select_related(
        'team', 'depot', 'deployed_by'
    ).order_by('-deployed_at')[:10]
    
    context = {
        'user_profile': user_profile,
        'teams': teams,
        'depots': depots,
        'recent_deployments': recent_deployments,
        'page_title': 'Team Depot Management',
    }
    
    return render(request, "fault_locator/team_depot_management.html", context)


@login_required
@senior_foreman_required
def device_team_management(request):
    """Device to Team Assignment Management"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get all devices with assignment status
    devices = FaultLocatorDevice.objects.annotate(
        assignment_count=Count('faultlocatordeviceassignment'),
        active_faults=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True))
    ).prefetch_related('faultlocatordeviceassignment_set__team')
    
    # Get all teams with device assignment status
    teams = FaultLocatorTeam.objects.annotate(
        device_count=Count('faultlocatordeviceassignment'),
        member_count=Count('members')
    ).prefetch_related('members', 'faultlocatordeviceassignment_set__device')
    
    # Get assignment history
    recent_assignments = FaultLocatorDeviceAssignment.objects.select_related(
        'device', 'team', 'assigned_by'
    ).order_by('-assigned_at')[:10]
    
    context = {
        'user_profile': user_profile,
        'devices': devices,
        'teams': teams,
        'recent_assignments': recent_assignments,
        'page_title': 'Device Team Management',
    }
    
    return render(request, "fault_locator/device_team_management.html", context)


@login_required
@senior_foreman_required
def performance_monitoring(request):
    """Performance Monitoring Dashboard"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Get date range from request (default to last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
    
    # Team Performance
    team_performance = get_team_performance_data(start_date, end_date)
    
    # Depot Performance
    depot_performance = get_depot_performance_data(start_date, end_date, user_profile)
    
    # Device Utilization
    device_utilization = get_device_utilization_data(start_date, end_date)
    
    # Fault Resolution Trends
    fault_trends = get_fault_resolution_trends(start_date, end_date)
    
    # Response Time Analysis
    response_times = get_response_time_analysis(start_date, end_date)
    
    context = {
        'user_profile': user_profile,
        'start_date': start_date,
        'end_date': end_date,
        'team_performance': team_performance,
        'depot_performance': depot_performance,
        'device_utilization': device_utilization,
        'fault_trends': fault_trends,
        'response_times': response_times,
        'page_title': 'Performance Monitoring',
    }
    
    return render(request, "fault_locator/performance_monitoring.html", context)


# AJAX endpoints for real-time updates
@csrf_exempt
@login_required
@senior_foreman_required
def quick_deploy_team(request):
    """Quick AJAX endpoint for team deployment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            team_id = data.get('team_id')
            depot_id = data.get('depot_id')
            notes = data.get('notes', '')
            
            user_profile = UserProfile.objects.filter(id=request.user.id).first()
            team = get_object_or_404(FaultLocatorTeam, id=team_id)
            
            # Get depot and validate it's in user's region
            depot_query = Depots.objects.filter(id=depot_id)
            if user_profile and hasattr(user_profile, 'region') and user_profile.region:
                depot_query = depot_query.filter(region=user_profile.region)
            
            depot = get_object_or_404(depot_query, id=depot_id)
            
            # Check if team already deployed
            if team.current_depot:
                return JsonResponse({
                    'success': False,
                    'message': f"Team '{team.name}' is already deployed to {team.current_depot.depot}"
                })
            
            # Check if team has device
            device_assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
            if not device_assignment:
                return JsonResponse({
                    'success': False,
                    'message': f"Team '{team.name}' must have a device assigned before deployment"
                })
            
            # Create deployment
            deployment = TeamDeployment.objects.create(
                team=team,
                depot=depot,
                deployed_by=user_profile,
                deployment_notes=notes
            )
            
            # Update team
            team.current_depot = depot
            team.assigned_at = deployment.deployed_at
            team.assigned_by = user_profile
            team.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Team '{team.name}' deployed to {depot.depot}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@senior_foreman_required
def quick_assign_device(request):
    """Quick AJAX endpoint for device assignment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            team_id = data.get('team_id')
            
            user_profile = UserProfile.objects.filter(id=request.user.id).first()
            device = get_object_or_404(FaultLocatorDevice, id=device_id)
            team = get_object_or_404(FaultLocatorTeam, id=team_id)
            
            # Check if device already assigned
            if FaultLocatorDeviceAssignment.objects.filter(device=device).exists():
                return JsonResponse({
                    'success': False,
                    'message': f"Device '{device.serial_number}' is already assigned"
                })
            
            # Create assignment
            assignment = FaultLocatorDeviceAssignment.objects.create(
                device=device,
                team=team,
                assigned_by=user_profile
            )
            
            return JsonResponse({
                'success': True,
                'message': f"Device '{device.serial_number}' assigned to team '{team.name}'"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@senior_foreman_required
def quick_recall_team(request):
    """Quick AJAX endpoint for team recall"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            team_id = data.get('team_id')
            notes = data.get('notes', '')
            
            user_profile = UserProfile.objects.filter(id=request.user.id).first()
            team = get_object_or_404(FaultLocatorTeam, id=team_id)
            
            if not team.current_depot:
                return JsonResponse({
                    'success': False,
                    'message': f"Team '{team.name}' is not currently deployed"
                })
            
            # Check for active assignments
            active_assignments = FaultAssignment.objects.filter(team=team, located_at__isnull=True)
            if active_assignments.exists():
                return JsonResponse({
                    'success': False,
                    'message': f"Team has {active_assignments.count()} active fault assignments"
                })
            
            # Find current deployment and update it
            current_deployment = TeamDeployment.objects.filter(
                team=team,
                recalled_at__isnull=True
            ).first()
            
            if current_deployment:
                current_deployment.recalled_at = timezone.now()
                current_deployment.recalled_by = user_profile
                current_deployment.recall_notes = notes
                current_deployment.save()
            
            # Update team
            depot_name = team.current_depot.depot
            team.current_depot = None
            team.assigned_at = None
            team.assigned_by = None
            team.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Team '{team.name}' recalled from {depot_name}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


# Helper functions for data aggregation
def get_system_statistics():
    """Get overall system statistics"""
    total_teams = FaultLocatorTeam.objects.count()
    deployed_teams = FaultLocatorTeam.objects.filter(current_depot__isnull=False).count()
    total_devices = FaultLocatorDevice.objects.count()
    assigned_devices = FaultLocatorDeviceAssignment.objects.count()
    active_faults = FaultAssignment.objects.filter(located_at__isnull=True).count()
    
    return {
        'total_teams': total_teams,
        'deployed_teams': deployed_teams,
        'available_teams': total_teams - deployed_teams,
        'total_devices': total_devices,
        'assigned_devices': assigned_devices,
        'available_devices': total_devices - assigned_devices,
        'active_faults': active_faults,
        'deployment_rate': round((deployed_teams / total_teams * 100) if total_teams > 0 else 0, 1),
        'device_utilization': round((assigned_devices / total_devices * 100) if total_devices > 0 else 0, 1),
    }


def get_teams_overview():
    """Get detailed teams overview"""
    return FaultLocatorTeam.objects.annotate(
        device_count=Count('faultlocatordeviceassignment'),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True)),
        member_count=Count('members')
    ).prefetch_related('members', 'faultlocatordeviceassignment_set__device')


def get_devices_overview():
    """Get detailed devices overview"""
    return FaultLocatorDevice.objects.annotate(
        assignment_count=Count('faultlocatordeviceassignment'),
        active_faults=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True))
    ).prefetch_related('faultlocatordeviceassignment_set__team')


def get_depot_deployment_status(user_profile=None):
    """Get depot deployment status filtered by user's region"""
    depots_query = Depots.objects.annotate(
        deployed_teams=Count('faultlocatorteam', filter=Q(faultlocatorteam__current_depot__isnull=False)),
        active_faults=Count('fault', filter=Q(fault__status__in=['requested', 'assigned']))
    )
    
    # Filter by user's region if provided
    if user_profile and hasattr(user_profile, 'region') and user_profile.region:
        depots_query = depots_query.filter(region=user_profile.region)
    
    return depots_query.order_by('depot')


def get_performance_metrics():
    """Get performance metrics for the last 30 days"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Fault resolution metrics
    total_faults = Fault.objects.filter(reported_at__gte=thirty_days_ago).count()
    resolved_faults = Fault.objects.filter(
        reported_at__gte=thirty_days_ago,
        status='closed'
    ).count()
    
    # Average resolution time
    avg_resolution_time = FaultAssignment.objects.filter(
        assigned_at__gte=thirty_days_ago,
        located_at__isnull=False
    ).aggregate(
        avg_time=Avg(F('located_at') - F('assigned_at'))
    )['avg_time']
    
    return {
        'total_faults': total_faults,
        'resolved_faults': resolved_faults,
        'resolution_rate': round((resolved_faults / total_faults * 100) if total_faults > 0 else 0, 1),
        'avg_resolution_time': avg_resolution_time,
    }


def get_recent_activities():
    """Get recent system activities"""
    activities = []
    
    # Recent deployments
    recent_deployments = TeamDeployment.objects.select_related(
        'team', 'depot', 'deployed_by'
    ).order_by('-deployed_at')[:5]
    
    for deployment in recent_deployments:
        activities.append({
            'type': 'deployment',
            'description': f"Team '{deployment.team.name}' deployed to {deployment.depot.depot}",
            'timestamp': deployment.deployed_at,
            'user': deployment.deployed_by.get_full_name() if deployment.deployed_by else 'System'
        })
    
    # Recent device assignments
    recent_assignments = FaultLocatorDeviceAssignment.objects.select_related(
        'device', 'team', 'assigned_by'
    ).order_by('-assigned_at')[:5]
    
    for assignment in recent_assignments:
        activities.append({
            'type': 'assignment',
            'description': f"Device '{assignment.device.serial_number}' assigned to team '{assignment.team.name}'",
            'timestamp': assignment.assigned_at,
            'user': assignment.assigned_by.get_full_name() if assignment.assigned_by else 'System'
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:10]


def get_team_performance_data(start_date, end_date):
    """Get team performance data for the specified period"""
    teams = FaultLocatorTeam.objects.annotate(
        total_assignments=Count('faultassignment', filter=Q(
            faultassignment__assigned_at__date__range=[start_date, end_date]
        )),
        completed_assignments=Count('faultassignment', filter=Q(
            faultassignment__assigned_at__date__range=[start_date, end_date],
            faultassignment__located_at__isnull=False
        ))
    ).prefetch_related('members')
    
    return teams


def get_depot_performance_data(start_date, end_date, user_profile=None):
    """Get depot performance data for the specified period filtered by user's region"""
    depots_query = Depots.objects.annotate(
        total_faults=Count('fault', filter=Q(
            fault__reported_at__date__range=[start_date, end_date]
        )),
        resolved_faults=Count('fault', filter=Q(
            fault__reported_at__date__range=[start_date, end_date],
            fault__status='closed'
        ))
    )
    
    # Filter by user's region if provided
    if user_profile and hasattr(user_profile, 'region') and user_profile.region:
        depots_query = depots_query.filter(region=user_profile.region)
    
    return depots_query.order_by('depot')


def get_device_utilization_data(start_date, end_date):
    """Get device utilization data for the specified period"""
    devices = FaultLocatorDevice.objects.annotate(
        usage_count=Count('faultassignment', filter=Q(
            faultassignment__assigned_at__date__range=[start_date, end_date]
        ))
    ).prefetch_related('faultlocatordeviceassignment_set__team')
    
    return devices


def get_fault_resolution_trends(start_date, end_date):
    """Get fault resolution trends over time"""
    # This would typically return daily/weekly aggregated data
    # For now, return basic trend information
    faults = Fault.objects.filter(
        reported_at__date__range=[start_date, end_date]
    ).values('reported_at__date').annotate(
        count=Count('id')
    ).order_by('reported_at__date')
    
    return faults


def get_response_time_analysis(start_date, end_date):
    """Get response time analysis data"""
    assignments = FaultAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date],
        located_at__isnull=False
    ).annotate(
        response_time=F('located_at') - F('assigned_at')
    ).values('response_time', 'team__name')
    
    return assignments
