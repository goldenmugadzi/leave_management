from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from it.users.helpers import DEPOTS
from .models import *
from django.db.models import F, ExpressionWrapper, DurationField, Sum
from .forms import FaultForm, FaultLocatorDeviceForm

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
            return redirect('device_list')  # Or another view as needed
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
