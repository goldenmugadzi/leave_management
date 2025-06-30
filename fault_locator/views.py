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
    """Enhanced device list with role-based actions"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    devices = FaultLocatorDevice.objects.select_related().prefetch_related('faultlocatordeviceassignment_set__team')
    
    # Role-based filtering if needed
    if not is_senior_foreperson(user_profile):
        # Regular users might only see devices at their depot
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            # Filter devices based on assignments to teams at their depot
            depot = Depots.objects.filter(code=user_profile.depot).first()
            if depot:
                # Show devices assigned to teams currently at this depot
                devices = devices.filter(
                    faultlocatordeviceassignment_set__team__current_depot=depot
                ).distinct()
    
    # Get device statistics
    total_devices = FaultLocatorDevice.objects.count()
    assigned_devices = FaultLocatorDeviceAssignment.objects.count()
    available_devices = total_devices - assigned_devices
    
    context = {
        "devices": devices,
        "user_profile": user_profile,
        "can_create_device": can_create_device(user_profile),
        "is_senior_foreperson": is_senior_foreperson(user_profile),
        "device_stats": {
            "total": total_devices,
            "assigned": assigned_devices,
            "available": available_devices
        }
    }
    
    return render(request, "fault_locator/device_list.html", context)

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

@login_required
def fault_list(request):
    """Enhanced fault list view with role-based filtering and search"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Base queryset
    faults = Fault.objects.select_related('depot', 'prioritized_by').prefetch_related('faultassignment_set__team', 'faultassignment_set__device')
    
    # Role-based filtering
    if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
        # Depot forepersons only see faults at their depot
        depot = Depots.objects.filter(code=user_profile.depot).first()
        if depot:
            faults = faults.filter(depot=depot)
    elif not is_senior_foreperson(user_profile):
        # Regular users only see faults they can access based on their depot/region
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            depot = Depots.objects.filter(code=user_profile.depot).first()
            if depot:
                faults = faults.filter(depot=depot)
    
    # Filter parameters from GET request
    depot_filter = request.GET.get('depot')
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search_query = request.GET.get('search')
    
    # Apply filters
    if depot_filter:
        faults = faults.filter(depot_id=depot_filter)
    
    if status_filter:
        faults = faults.filter(status=status_filter)
    
    if priority_filter:
        faults = faults.filter(priority=priority_filter)
    
    if search_query:
        faults = faults.filter(description__icontains=search_query)
    
    # Order by priority (high to low) and then by reported date
    faults = faults.order_by('-priority', '-reported_at')
    
    # Get filter options for the template
    available_depots = Depots.objects.all()
    if is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
        # Depot forepersons only see their depot in filter
        depot = Depots.objects.filter(code=user_profile.depot).first()
        if depot:
            available_depots = [depot]
    
    status_choices = Fault._meta.get_field('status').choices
    priority_choices = Fault._meta.get_field('priority').choices
    
    context = {
        'faults': faults,
        'user_profile': user_profile,
        'is_senior_foreperson': is_senior_foreperson(user_profile),
        'is_depot_foreperson': is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None),
        'available_depots': available_depots,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'current_filters': {
            'depot': depot_filter,
            'status': status_filter,
            'priority': priority_filter,
            'search': search_query,
        }
    }
    
    return render(request, "fault_locator/fault_list.html", context)

@login_required
def fault_detail(request, fault_id):
    """Detailed view of a specific fault"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    fault = get_object_or_404(Fault, id=fault_id)
    
    # Check permissions
    can_view = False
    if is_senior_foreperson(user_profile):
        can_view = True
    elif is_depot_foreperson(user_profile, user_profile.depot if user_profile and hasattr(user_profile, 'depot') and user_profile.depot else None):
        depot = Depots.objects.filter(code=user_profile.depot).first()
        can_view = depot and fault.depot == depot
    elif user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
        depot = Depots.objects.filter(code=user_profile.depot).first()
        can_view = depot and fault.depot == depot
    
    if not can_view:
        messages.error(request, "You don't have permission to view this fault.")
        return redirect('fault_list')
    
    # Get fault assignments
    assignments = FaultAssignment.objects.filter(fault=fault).select_related('team', 'device')
    current_assignment = assignments.filter(located_at__isnull=True).first()
    
    # Get available teams for assignment (only for authorized users)
    available_teams = []
    if is_senior_foreperson(user_profile) or is_depot_foreperson(user_profile, fault.depot):
        # Get teams with devices that are either unassigned or at this depot
        teams_with_devices = FaultLocatorDeviceAssignment.objects.select_related('team').values_list('team', flat=True)
        available_teams = FaultLocatorTeam.objects.filter(
            id__in=teams_with_devices
        ).exclude(
            id__in=assignments.filter(located_at__isnull=True).values_list('team', flat=True)
        )
    
    context = {
        'fault': fault,
        'user_profile': user_profile,
        'current_assignment': current_assignment,
        'assignments': assignments,
        'available_teams': available_teams,
        'can_assign': is_senior_foreperson(user_profile) or is_depot_foreperson(user_profile, fault.depot),
        'can_prioritize': is_depot_foreperson(user_profile, fault.depot),
        'priority_choices': Fault._meta.get_field('priority').choices,
    }
    
    return render(request, "fault_locator/fault_detail.html", context)

@login_required
def update_fault_status(request, fault_id):
    """Update fault status (for team members in the field)"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    fault = get_object_or_404(Fault, id=fault_id)
    
    # Check if user is part of a team assigned to this fault
    user_teams = user_profile.fault_locator_teams.all() if user_profile else []
    assigned_teams = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).values_list('team', flat=True)
    
    can_update = any(team.id in assigned_teams for team in user_teams)
    
    if not can_update and not is_senior_foreperson(user_profile):
        messages.error(request, "You don't have permission to update this fault.")
        return redirect('fault_detail', fault_id=fault_id)
    
    if request.method == "POST":
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in ['located', 'closed']:
            fault.status = new_status
            fault.save()
            
            # Update assignment if fault is located
            if new_status == 'located':
                assignment = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).first()
                if assignment:
                    assignment.located_at = timezone.now()
                    assignment.save()
            
            messages.success(request, f"Fault status updated to {fault.get_status_display()}")
        
        return redirect('fault_detail', fault_id=fault_id)
    
    return redirect('fault_detail', fault_id=fault_id)

# Enhanced create_fault to use UserProfile
@login_required
def create_fault(request):
    """Create a new fault report"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    if request.method == "POST":
        form = FaultForm(request.POST)
        if form.is_valid():
            fault = form.save(commit=False)
            
            # Set default depot based on user's depot if not specified
            if not fault.depot and user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
                depot = Depots.objects.filter(code=user_profile.depot).first()
                if depot:
                    fault.depot = depot
            
            fault.save()
            messages.success(request, "Fault reported successfully")
            return redirect('fault_detail', fault_id=fault.id)
    else:
        form = FaultForm()
        
        # Pre-select user's depot if available
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            depot = Depots.objects.filter(code=user_profile.depot).first()
            if depot:
                form.initial['depot'] = depot
    
    return render(request, "fault_locator/create_fault.html", {
        "form": form,
        "user_profile": user_profile
    })

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

@login_required
def create_device(request):
    """Create a new fault locator device with role-based access control"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check if user has permission to create devices
    if not can_create_device(user_profile):
        messages.error(request, "Access denied. You don't have permission to create devices.")
        return redirect('fault_locator_home')
    
    if request.method == "POST":
        form = FaultLocatorDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            
            # Check for duplicate serial numbers
            if FaultLocatorDevice.objects.filter(serial_number=device.serial_number).exists():
                form.add_error('serial_number', 'A device with this serial number already exists.')
                return render(request, "fault_locator/create_device.html", {
                    "form": form,
                    "user_profile": user_profile
                })
            
            device.save()
            messages.success(request, f"Device {device.serial_number} created successfully")
            
            # Redirect based on user role
            if is_senior_foreperson(user_profile):
                # Senior forepersons might want to assign the device immediately
                messages.info(request, "You can now assign this device to a team.")
                return redirect('senior_device_assignment')
            else:
                return redirect('device_list')
                
    else:
        form = FaultLocatorDeviceForm()
    
    # Get statistics for the template
    total_devices = FaultLocatorDevice.objects.count()
    assigned_devices = FaultLocatorDeviceAssignment.objects.count()
    available_devices = total_devices - assigned_devices
    
    context = {
        "form": form,
        "user_profile": user_profile,
        "is_senior_foreperson": is_senior_foreperson(user_profile),
        "device_stats": {
            "total": total_devices,
            "assigned": assigned_devices,
            "available": available_devices
        }
    }
    
    return render(request, "fault_locator/create_device.html", context)

def can_create_device(user_profile):
    """Check if user has permission to create devices"""
    if not user_profile:
        return False
    
    # Senior forepersons can create devices
    if is_senior_foreperson(user_profile):
        return True
    
    # IT personnel can create devices
    if hasattr(user_profile, 'section') and user_profile.section:
        if 'it' in user_profile.section.lower() or 'information technology' in user_profile.section.lower():
            return True
    
    # Administrators can create devices
    if hasattr(user_profile, 'designation') and user_profile.designation:
        designation_desc = user_profile.designation.description.lower()
        if 'administrator' in designation_desc or 'manager' in designation_desc:
            return True
    
    return False

def is_senior_foreperson(user_profile):
    """Check if user profile belongs to a senior foreperson"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    designation_desc = user_profile.designation.description.lower()
    return 'senior' in designation_desc and 'foreperson' in designation_desc

def is_foreperson(user_profile):
    """Check if user profile belongs to any foreperson (senior or depot)"""
    if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
        return False
    
    designation_desc = user_profile.designation.description.lower()
    return 'foreperson' in designation_desc

def get_user_depot(user_profile):
    """Get the depot object for a user profile"""
    if not user_profile or not hasattr(user_profile, 'depot') or not user_profile.depot:
        return None
    
    return Depots.objects.filter(code=user_profile.depot).first()

def has_fault_locator_permissions(user_profile):
    """Check if user has any fault locator system permissions"""
    if not user_profile:
        return False
    
    return (is_senior_foreperson(user_profile) or 
            is_foreperson(user_profile) or 
            can_create_device(user_profile))

def device_detail(request, device_id):
    """Detailed view of a specific device"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    device = get_object_or_404(FaultLocatorDevice, id=device_id)
    
    # Check permissions - users can only view devices they have access to
    can_view = False
    if is_senior_foreperson(user_profile):
        # Senior forepersons can view all devices
        can_view = True
    elif user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
        # Regular users can view devices at their depot
        depot = get_user_depot(user_profile)
        if depot:
            # Check if device is assigned to a team at this depot
            device_assignment = FaultLocatorDeviceAssignment.objects.filter(
                device=device, 
                team__current_depot=depot
            ).first()
            can_view = device_assignment is not None
    
    if not can_view and not is_senior_foreperson(user_profile):
        # Allow IT personnel and administrators to view devices
        if not can_create_device(user_profile):
            messages.error(request, "You don't have permission to view this device.")
            return redirect('device_list')
    
    # Get current assignment (device to team)
    current_assignment = FaultLocatorDeviceAssignment.objects.filter(device=device).first()
    
    # Get current fault assignment (if device is currently working on a fault)
    current_fault_assignment = None
    if current_assignment:
        current_fault_assignment = FaultAssignment.objects.filter(
            device=device, 
            located_at__isnull=True
        ).select_related('fault', 'team').first()
    
    # Get assignment history
    assignment_history = FaultAssignment.objects.filter(
        device=device
    ).select_related('fault', 'team').order_by('-assigned_at')[:10]
    
    # Device statistics
    total_assignments = FaultAssignment.objects.filter(device=device).count()
    completed_assignments = FaultAssignment.objects.filter(
        device=device, 
        located_at__isnull=False
    ).count()
    
    context = {
        'device': device,
        'user_profile': user_profile,
        'current_assignment': current_assignment,
        'current_fault_assignment': current_fault_assignment,
        'assignment_history': assignment_history,
        'is_senior_foreperson': is_senior_foreperson(user_profile),
        'can_assign': is_senior_foreperson(user_profile),
        'device_stats': {
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'success_rate': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        }
    }
    
    return render(request, "fault_locator/device_detail.html", context)

# Add these additional views that might be missing:

def team_list(request):
    """List all fault locator teams"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    teams = FaultLocatorTeam.objects.prefetch_related('members', 'faultlocatordeviceassignment_set__device')
    
    # Role-based filtering
    if not is_senior_foreperson(user_profile):
        # Regular users might only see teams at their depot
        if user_profile and hasattr(user_profile, 'depot') and user_profile.depot:
            depot = get_user_depot(user_profile)
            if depot:
                teams = teams.filter(current_depot=depot)
    
    context = {
        'teams': teams,
        'user_profile': user_profile,
        'is_senior_foreperson': is_senior_foreperson(user_profile),
        'can_create_team': is_senior_foreperson(user_profile) or can_create_device(user_profile)
    }
    
    return render(request, "fault_locator/team_list.html", context)

def create_team(request):
    """Create a new fault locator team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or can_create_device(user_profile)):
        messages.error(request, "Access denied. You don't have permission to create teams.")
        return redirect('fault_locator_home')
    
    if request.method == "POST":
        form = FaultLocatorTeamNameForm(request.POST)
        if form.is_valid():
            team = form.save()
            messages.success(request, f"Team {team.name} created successfully")
            return redirect('add_team_member', team_id=team.id)
    else:
        form = FaultLocatorTeamNameForm()
    
    return render(request, "fault_locator/create_team.html", {
        "form": form,
        "user_profile": user_profile
    })

def add_team_member(request, team_id):
    """Add a member to a team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or can_create_device(user_profile)):
        messages.error(request, "Access denied. You don't have permission to manage team members.")
        return redirect('team_list')
    
    if request.method == "POST":
        member_id = request.POST.get('member')
        if member_id:
            member = get_object_or_404(UserProfile, id=member_id)
            team.members.add(member)
            messages.success(request, f"{member.get_full_name()} added to team {team.name}")
    
    return redirect('edit_team', team_id=team.id)

def edit_team(request, team_id):
    """Edit team details and members"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or can_create_device(user_profile)):
        messages.error(request, "Access denied. You don't have permission to edit teams.")
        return redirect('team_list')
    
    # Get users not in this team
    users = UserProfile.objects.exclude(id__in=team.members.values_list('id', flat=True))
    
    if request.method == "POST":
        form = FaultLocatorTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f"Team {team.name} updated successfully")
            return redirect('team_list')
    else:
        form = FaultLocatorTeamForm(instance=team)
    
    return render(request, "fault_locator/edit_team.html", {
        "form": form, 
        "team": team, 
        "users": users,
        "user_profile": user_profile
    })

def remove_team_member(request, team_id, member_id):
    """Remove a member from a team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or can_create_device(user_profile)):
        messages.error(request, "Access denied. You don't have permission to manage team members.")
        return redirect('team_list')
    
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    member = get_object_or_404(UserProfile, id=member_id)
    team.members.remove(member)
    
    messages.success(request, f"{member.get_full_name()} removed from team {team.name}")
    return redirect('edit_team', team_id=team.id)

def assign_device_to_team(request):
    """Assign a device to a team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or can_create_device(user_profile)):
        messages.error(request, "Access denied. You don't have permission to assign devices.")
        return redirect('device_list')
    
    team_id = request.GET.get('team_id')
    initial = {'team': team_id} if team_id else {}
    
    if request.method == "POST":
        form = AssignDeviceToTeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Device assigned to team successfully")
            return redirect('team_list')
    else:
        form = AssignDeviceToTeamForm(initial=initial)
    
    return render(request, "fault_locator/assign_device_to_team.html", {
        "form": form,
        "user_profile": user_profile
    })

def unassign_device(request, device_id):
    """Unassign a device from its current team"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions
    if not (is_senior_foreperson(user_profile) or can_create_device(user_profile)):
        messages.error(request, "Access denied. You don't have permission to unassign devices.")
        return redirect('device_list')
    
    assignment = FaultLocatorDeviceAssignment.objects.filter(device_id=device_id).first()
    if assignment:
        team_name = assignment.team.name
        assignment.delete()
        messages.success(request, f"Device unassigned from team {team_name}")
    else:
        messages.warning(request, "Device is not currently assigned to any team")
    
    return redirect('device_list')

def deploy_team_to_depot(request):
    """Deploy a team to a specific depot (Senior Foreperson only)"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions - only senior forepersons can deploy teams
    if not is_senior_foreperson(user_profile):
        messages.error(request, "Access denied. Only senior forepersons can deploy teams.")
        return redirect('fault_locator_home')
    
    if request.method == "POST":
        form = TeamDeploymentForm(request.POST)
        if form.is_valid():
            deployment = form.save(commit=False)
            deployment.deployed_by = user_profile
            deployment.save()
            
            # Update the team's current depot
            team = deployment.team
            team.current_depot = deployment.depot
            team.assigned_at = timezone.now()
            team.assigned_by = user_profile
            team.save()
            
            messages.success(request, f"Team {team.name} deployed to {deployment.depot.depot} successfully")
            return redirect('team_deployments')
    else:
        form = TeamDeploymentForm()
    
    return render(request, "fault_locator/deploy_team.html", {
        "form": form,
        "user_profile": user_profile
    })

def recall_team_from_depot(request, deployment_id):
    """Recall a team from their current deployment (Senior Foreperson only)"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions - only senior forepersons can recall teams
    if not is_senior_foreperson(user_profile):
        messages.error(request, "Access denied. Only senior forepersons can recall teams.")
        return redirect('fault_locator_home')
    
    deployment = get_object_or_404(TeamDeployment, id=deployment_id, recalled_at__isnull=True)
    
    if request.method == "POST":
        # Recall the team
        deployment.recalled_at = timezone.now()
        deployment.save()
        
        # Update team's current depot to None
        team = deployment.team
        team.current_depot = None
        team.assigned_at = None
        team.assigned_by = None
        team.save()
        
        messages.success(request, f"Team {team.name} recalled from {deployment.depot.depot} successfully")
        return redirect('team_deployments')
    
    return render(request, "fault_locator/recall_team.html", {
        "deployment": deployment,
        "user_profile": user_profile
    })

def team_deployments(request):
    """View all team deployments (Senior Foreperson only)"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    
    # Check permissions - only senior forepersons can view all deployments
    if not is_senior_foreperson(user_profile):
        messages.error(request, "Access denied. Only senior forepersons can view team deployments.")
        return redirect('fault_locator_home')
    
    # Get current deployments
    current_deployments = TeamDeployment.objects.filter(
        recalled_at__isnull=True
    ).select_related('team', 'depot', 'deployed_by').order_by('-deployed_at')
    
    # Get deployment history
    deployment_history = TeamDeployment.objects.filter(
        recalled_at__isnull=False
    ).select_related('team', 'depot', 'deployed_by').order_by('-recalled_at')[:20]
    
    # Get teams available for deployment (teams with devices but not currently deployed)
    teams_with_devices = FaultLocatorDeviceAssignment.objects.values_list('team_id', flat=True)
    available_teams = FaultLocatorTeam.objects.filter(
        id__in=teams_with_devices,
        current_depot__isnull=True
    )
    
    context = {
        'current_deployments': current_deployments,
        'deployment_history': deployment_history,
        'available_teams': available_teams,
        'user_profile': user_profile,
        'is_senior_foreperson': is_senior_foreperson(user_profile)
    }
    
    return render(request, "fault_locator/team_deployments.html", context)

def depot_fault_priority(request, depot_id):
    """Set fault priorities for a specific depot (Depot Foreperson only)"""
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    depot = get_object_or_404(Depots, id=depot_id)
    
    # Check permissions - depot forepersons can only prioritize faults at their depot
    if not is_depot_foreperson(user_profile, depot):
        messages.error(request, "Access denied. You can only prioritize faults at your assigned depot.")
        return redirect('fault_locator_home')
    
    # Get faults at this depot that are requested or assigned
    faults = Fault.objects.filter(
        depot=depot,
        status__in=['requested', 'assigned']
    ).order_by('-reported_at')
    
    if request.method == "POST":
        # Process priority updates
        for fault in faults:
            priority_key = f"priority_{fault.id}"
            if priority_key in request.POST:
                new_priority = request.POST[priority_key]
                if new_priority and fault.priority != int(new_priority):
                    fault.priority = int(new_priority)
                    fault.prioritized_by = user_profile
                    fault.prioritized_at = timezone.now()
                    fault.save()
        
        messages.success(request, "Fault priorities updated successfully")
        return redirect('depot_fault_priority', depot_id=depot_id)
    
    context = {
        'depot': depot,
        'faults': faults,
        'user_profile': user_profile,
        'priority_choices': Fault._meta.get_field('priority').choices
    }
    
    return render(request, "fault_locator/depot_fault_priority.html", context)
