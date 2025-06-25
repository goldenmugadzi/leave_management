from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from it.users.helpers import DEPOTS
from .models import *
from django.db.models import F, ExpressionWrapper, DurationField, Sum
from .forms import FaultForm, FaultLocatorDeviceForm, FaultLocatorTeamForm, FaultLocatorTeamNameForm, AddTeamMemberForm, AssignDeviceToTeamForm, AssignFaultForm
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

def fault_locator_home(request):
    return render(request, "fault_locator/landing.html")

def assign_fault(request):
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
                FaultAssignment.objects.create(
                    fault=fault,
                    team=team,
                    device=assignment.device
                )
                return redirect('fault_list')  # Or another relevant view
    else:
        form = AssignFaultForm()
    return render(request, "fault_locator/assign_fault.html", {"form": form})

def edit_team(request, team_id):
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    from it.users.models import UserProfile
    users = UserProfile.objects.exclude(id__in=team.members.values_list('id', flat=True))
    if request.method == "POST":
        form = FaultLocatorTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = FaultLocatorTeamForm(instance=team)
    return render(request, "fault_locator/edit_team.html", {"form": form, "team": team, "users": users})

def remove_team_member(request, team_id, member_id):
    team = get_object_or_404(FaultLocatorTeam, id=team_id)
    member = get_object_or_404(UserProfile, id=member_id)
    team.members.remove(member)
    return redirect('edit_team', team_id=team.id)

def assign_device_to_team(request):
    team_id = request.GET.get('team_id')
    initial = {'team': team_id} if team_id else {}
    if request.method == "POST":
        form = AssignDeviceToTeamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = AssignDeviceToTeamForm(initial=initial)
    return render(request, "fault_locator/assign_device_to_team.html", {"form": form})

def unassign_device(request, device_id):
    assignment = FaultLocatorDeviceAssignment.objects.filter(device_id=device_id).first()
    if assignment:
        assignment.delete()
    return redirect('device_list')

def fault_list(request):
    faults = Fault.objects.all()
    return render(request, "fault_locator/fault_list.html", {"faults": faults})
