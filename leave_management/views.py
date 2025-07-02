from django.shortcuts import render, redirect
from .forms import LeaveRequestForm, LeaveTypesForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import LeaveRequest, LeaveTypes

def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user 
            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('table_leave') 
    else:
        form = LeaveRequestForm()
    return render(request, 'leave_system/create_leave.html', {'form': form})

def leave_request_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = LeaveRequest.objects.all()

    if search_value:
        qs = qs.filter(
            Q(user__user__username__icontains=search_value) |
            Q(type_of_leave__icontains=search_value) |
            Q(gender__icontains=search_value) |
            Q(position__designation__icontains=search_value) |
            Q(department__section__icontains=search_value) |
            Q(region__region__icontains=search_value)
        )

    total = qs.count()
    qs = qs.order_by('-start_date')[start:start+length]

    data = []
    for leave in qs:
        data.append({
            "id": leave.id,
            "ecnumber": leave.ecnumber,
            "user": str(leave.user) if leave.user else "",
            "type_of_leave": leave.type_of_leave,
            "gender": leave.gender,
            "position": str(leave.position) if leave.position else "",
            "start_date": leave.start_date.strftime('%Y-%m-%d') if leave.start_date else "",
            "end_date": leave.end_date.strftime('%Y-%m-%d') if leave.end_date else "",
            "department": str(leave.department) if leave.department else "",
            "number_of_days": leave.number_of_days,
            "region": str(leave.region) if leave.region else "",
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def table_leave (request):
  return render(request,'leave_system/leave_table.html')

def create_leave_types(request):
    if request.method == 'POST':
        form = LeaveTypesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leave_types') 
    else:
        form = LeaveTypesForm()
    return render(request, 'leave_system/create.html', {'form': form})

def leave_types_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    qs = LeaveTypes.objects.all()
    total = qs.count()
    qs = qs.order_by('-id')[start:start+length]

    data = []
    for obj in qs:
        data.append({
            "id": obj.id,
            "leave_for_national_events": obj.leave_for_national_events,
            "sick_leave": obj.sick_leave,
            "maternity_leave": obj.maternity_leave,
            "special_leave": obj.special_leave,
            "unpaid_leave": obj.unpaid_leave,
            "vacation_leave": obj.vacation_leave,
            "study_leave": obj.study_leave,
            "occasional_leave": obj.occasional_leave,
            "mandatory_leave": obj.mandatory_leave,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def leave_types (request):
  return render(request,'leave_system/types_table.html')