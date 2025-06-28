from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, ExpressionWrapper, DurationField, Sum

from it.users.helpers import DEPOTS
from .models import *
from .forms import FaultForm, FaultLocatorDeviceForm, FaultLocatorTeamForm, FaultLocatorTeamNameForm, AddTeamMemberForm, AssignDeviceToTeamForm, AssignFaultForm, TeamDeploymentForm, SeniorForepersonDeviceAssignmentForm
from it.users.models import UserProfile

def device_list(request):
    devices = FaultLocatorDevice.objects.all()
    # assignments = DeviceAssignment.objects.filter(returned_at__isnull=True)
    return render(request, "fault_locator/device_list.html", {
        "devices": devices,
        # "assignments": assignments
    })

def assign_device(request):
    if request.method == "POST":
        device_id = request.POST.get("device_id")
        depot_id = request.POST.get("depot_id")
        device = get_object_or_404(FaultLocatorDevice, id=device_id)
        depot = get_object_or_404(DEPOTS, id=depot_id)
        # Only assign if not already assigned
        # if not DeviceAssignment.objects.filter(device=device, returned_at__isnull=True).exists():
        #     DeviceAssignment.objects.create(device=device, depot=depot)
    return redirect('device_list')

def return_device(request, assignment_id):
    assignment = get_object_or_404(DeviceAssignment, id=assignment_id, returned_at__isnull=True)
    assignment.returned_at = timezone.now()
    assignment.save()
    return redirect('device_list')

def usage_report(request):
    # Total usage time per depot
    assignments = DeviceAssignment.objects.annotate(
        duration=ExpressionWrapper(
            (F('returned_at') - F('assigned_at')),
            output_field=DurationField()
        )
    ).values('depot__name').annotate(
        total_time=Sum('duration')
    )
    return render(request, "fault_locator/usage_report.html", {"assignments": assignments})

def create_fault(request):
    if request.method == "POST":
        form = FaultForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fault_list')  # Redirect to fault list after creation
    else:
        form = FaultForm()
    return render(request, "fault_locator/create_fault.html", {"form": form})

def create_device(request):
    if request.method == "POST":
        form = FaultLocatorDeviceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('device_list')
    else:
        form = FaultLocatorDeviceForm()
    return render(request, "fault_locator/create_device.html", {"form": form})

def create_team(request):
    if request.method == "POST":
        form = FaultLocatorTeamNameForm(request.POST)
        if form.is_valid():
            team = form.save()
            return redirect('add_team_member', team_id=team.id)
    else:
        form = FaultLocatorTeamNameForm()
    return render(request, "fault_locator/create_team.html", {"form": form})

def device_detail(request, device_id):
    device = get_object_or_404(FaultLocatorDevice, id=device_id)
    # Get current assignment (not yet located/closed)
    assignment = FaultAssignment.objects.filter(device=device, located_at__isnull=True).first()
    return render(request, "fault_locator/device_detail.html", {
        "device": device,
        "assignment": assignment,
    })

def team_list(request):
    teams = FaultLocatorTeam.objects.all()
    return render(request, "fault_locator/team_list.html", {"teams": teams})

def add_team_member(request, team_id):
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    if request.method == "POST":
        member_id = request.POST.get('member')
        if member_id:
            from it.users.models import UserProfile
            member = get_object_or_404(UserProfile, id=member_id)
            team.members.add(member)
    return redirect('edit_team', team_id=team.id)

@login_required
def deploy_team_to_depot(request):
    """Senior Foreperson deploys teams to depots"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not user_profile or not is_senior_foreperson(user_profile):
        messages.error(request, "Access denied. Senior Foreperson role required.")
        return redirect('fault_locator_home')
        
    if request.method == "POST":
        form = TeamDeploymentForm(request.POST)
        if form.is_valid():
            deployment = form.save(commit=False)
            deployment.deployed_by = user_profile
            deployment.save()
            
            # Update team's current depot
            team = deployment.team
            team.current_depot = deployment.depot
            team.assigned_at = timezone.now()
            team.assigned_by = user_profile
            team.save()
            
            messages.success(request, f"Team {team.name} deployed to {deployment.depot.depot}")
            return redirect('team_deployments')
    else:
        form = TeamDeploymentForm()
    
    return render(request, "fault_locator/deploy_team.html", {"form": form})

@login_required 
def recall_team_from_depot(request, deployment_id):
    """Senior Foreperson recalls teams from depots"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not user_profile or not is_senior_foreperson(user_profile):
        messages.error(request, "Access denied. Senior Foreperson role required.")
        return redirect('fault_locator_home')
        
    deployment = get_object_or_404(TeamDeployment, id=deployment_id, recalled_at__isnull=True)
    deployment.recalled_at = timezone.now()
    deployment.save()
    
    # Clear team's current depot assignment
    team = deployment.team
    team.current_depot = None
    team.assigned_at = None
    team.assigned_by = None
    team.save()
    
    messages.success(request, f"Team {team.name} recalled from {deployment.depot.depot}")
    return redirect('team_deployments')

@login_required
def depot_fault_priority(request, depot_id):
    """Depot Foreperson sets fault priorities"""
    depot = get_object_or_404(Depots, id=depot_id)
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if not user_profile or not is_depot_foreperson(user_profile, depot):
        messages.error(request, "Access denied. Depot Foreperson role required.")
        return redirect('fault_locator_home')
    
    faults = Fault.objects.filter(depot=depot, status__in=['requested', 'assigned']).order_by('-priority', 'reported_at')
    
    if request.method == "POST":
        fault_id = request.POST.get('fault_id')
        priority = request.POST.get('priority')
        
        fault = get_object_or_404(Fault, id=fault_id, depot=depot)
        fault.priority = priority
        fault.prioritized_by = user_profile
        fault.prioritized_at = timezone.now()
        fault.save()
        
        messages.success(request, f"Fault priority updated to {fault.get_priority_display()}")
        return redirect('depot_fault_priority', depot_id=depot_id)
    
    return render(request, "fault_locator/depot_fault_priority.html", {
        "depot": depot,
        "faults": faults
    })

@login_required
def team_deployments(request):
    """View all team deployments"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Filter deployments based on user role
    if is_senior_foreperson(user_profile):
        # Senior forepersons can see all deployments
        active_deployments = TeamDeployment.objects.filter(recalled_at__isnull=True).select_related('team', 'depot', 'deployed_by')
        recent_deployments = TeamDeployment.objects.filter(recalled_at__isnull=False).order_by('-recalled_at')[:10]
    else:
        # Other users can only see deployments they made or at their depot
        active_deployments = TeamDeployment.objects.filter(
            recalled_at__isnull=True,
            deployed_by=user_profile
        ).select_related('team', 'depot', 'deployed_by')
        recent_deployments = TeamDeployment.objects.filter(
            recalled_at__isnull=False,
            deployed_by=user_profile
        ).order_by('-recalled_at')[:10]
    
    return render(request, "fault_locator/team_deployments.html", {
        "active_deployments": active_deployments,
        "recent_deployments": recent_deployments,
        "user_profile": user_profile
    })

def is_senior_foreperson(user_profile):
    """Check if user profile belongs to a senior foreperson"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    designation_desc = user_profile.designation.description.lower()
    return 'senior' in designation_desc and 'foreperson' in designation_desc

def is_depot_foreperson(user_profile, depot):
    """Check if user profile is foreperson for specific depot"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    if not hasattr(user_profile, 'depot') or not user_profile.depot:
        return False
    
    designation_desc = user_profile.designation.description.lower()
    # Check if user is a foreperson and assigned to the specific depot
    return 'foreperson' in designation_desc and user_profile.depot == depot.code

@login_required
def senior_device_assignment(request):
    """Senior Foreperson assigns devices to teams"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not user_profile or not is_senior_foreperson(user_profile):
        messages.error(request, "Access denied. Senior Foreperson role required.")
        return redirect('fault_locator_home')
    
    if request.method == "POST":
        form = SeniorForepersonDeviceAssignmentForm(request.POST, user=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Device assigned to team successfully")
            return redirect('device_list')
    else:
        form = SeniorForepersonDeviceAssignmentForm(user=user_profile)
    
    return render(request, "fault_locator/senior_device_assignment.html", {
        "form": form,
        "user_profile": user_profile
    })

# Add a new view to check user permissions and display appropriate dashboard
@login_required
def fault_locator_home(request):
    """Enhanced home page with role-based content"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    context = {
        'user_profile': user_profile,
        'is_senior_foreperson': is_senior_foreperson(user_profile),
        'is_depot_foreperson': is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None),
    }
    
    # Add depot-specific data for depot forepersons
    if context['is_depot_foreperson'] and user_profile.depot:
        depot = Depots.objects.filter(code=user_profile.depot).first()
        if depot:
            context['user_depot'] = depot
            context['depot_faults_count'] = Fault.objects.filter(
                depot=depot, 
                status__in=['requested', 'assigned']
            ).count()
    
    # Add team deployment data for senior forepersons
    if context['is_senior_foreperson']:
        context['active_deployments_count'] = TeamDeployment.objects.filter(recalled_at__isnull=True).count()
        context['available_teams_count'] = FaultLocatorTeam.objects.filter(current_depot__isnull=True).count()
    
    return render(request, "fault_locator/landing.html", context)

# Enhanced assign_fault to use UserProfile
@login_required
def assign_fault(request):
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if request.method == "POST":
        form = AssignFaultForm(request.POST)
        if form.is_valid():
            fault = form.cleaned_data['fault']
            team = form.cleaned_data['team']
            
            # Get the device assigned to this team
            assignment = FaultLocatorDeviceAssignment.objects.filter(team=team).first()
            if not assignment:
                form.add_error('team', "This team does not have a device assigned.")
            else:
                fault_assignment = FaultAssignment.objects.create(
                    fault=fault,
                    team=team,
                    device=assignment.device
                )
                
                # Update fault status
                fault.status = 'assigned'
                fault.save()
                
                messages.success(request, f"Fault assigned to team {team.name} with device {assignment.device.serial_number}")
                return redirect('fault_list')
    else:
        form = AssignFaultForm()
        
        # Filter faults based on user role
        if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
            # Depot forepersons can only assign faults at their depot
            depot = Depots.objects.filter(code=user_profile.depot).first()
            if depot:
                form.fields['fault'].queryset = Fault.objects.filter(
                    depot=depot, 
                    status='requested'
                )
    
    return render(request, "fault_locator/assign_fault.html", {
        "form": form,
        "user_profile": user_profile
    })
