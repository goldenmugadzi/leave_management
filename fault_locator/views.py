from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import FaultLocatorDevice, DeviceAssignment, Depot
from django.db.models import F, ExpressionWrapper, DurationField, Sum

def device_list(request):
    devices = FaultLocatorDevice.objects.all()
    assignments = DeviceAssignment.objects.filter(returned_at__isnull=True)
    assigned_device_ids = assignments.values_list('device_id', flat=True)
    device_status = []
    for device in devices:
        assignment = DeviceAssignment.objects.filter(device=device, returned_at__isnull=True).first()
        if assignment:
            status = f"Assigned to {assignment.depot.name} since {assignment.assigned_at.strftime('%Y-%m-%d %H:%M')}"
        else:
            status = "Available"
        device_status.append({
            "device": device,
            "status": status,
            "assigned": bool(assignment),
            "assignment": assignment,
        })
    depots = Depot.objects.all()
    return render(request, "fault_locator/device_list.html", {
        "device_status": device_status,
        "depots": depots,
    })

def assign_device(request):
    if request.method == "POST":
        device_id = request.POST.get("device_id")
        depot_id = request.POST.get("depot_id")
        device = get_object_or_404(FaultLocatorDevice, id=device_id)
        depot = get_object_or_404(Depot, id=depot_id)
        # Only assign if not already assigned
        if not DeviceAssignment.objects.filter(device=device, returned_at__isnull=True).exists():
            DeviceAssignment.objects.create(device=device, depot=depot)
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
