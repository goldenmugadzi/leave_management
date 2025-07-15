from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import LeaveRequestForm, LeaveTypesForm
from django.http import JsonResponse
from django.db.models import Q
from .models import LeaveRequest, LeaveTypes
from it.users.models import *
from datetime import timedelta



def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            user_profile = request.user

            leave.user = user_profile
            leave.position = user_profile.designation
            leave.department = user_profile.section
            leave.region = user_profile.region
            leave.status = 'pending'
            leave.ecnumber = user_profile.username

            # --- Calculate number_of_days manually ---
            if leave.start_date and leave.end_date:
                day_count = 0
                current_day = leave.start_date
                while current_day <= leave.end_date:
                    if current_day.weekday() < 5:
                        day_count += 1
                    current_day += timedelta(days=1)
                leave.number_of_days = day_count
            # -----------------------------------------

            # Deduct
            try:
                user = UserProfile.objects.filter(id=user_profile.id).first()
                leave_types = LeaveTypes.objects.filter(user=user).first()
            except LeaveTypes.DoesNotExist:
                messages.error(request, "Your leave balances are not set up")
                return redirect('table_leave')

            days = leave.number_of_days or 0
            leave_type_map = {
                'leave for national events': 'leave_for_national_events',
                'sick leave': 'sick_leave',
                'maternity': 'maternity_leave',
                'special leave': 'special_leave',
                'unpaid': 'unpaid_leave',
                'vacation': 'vacation_leave',
                'occassional leave': 'occasional_leave',
                'study leave': 'study_leave',
            }
            leave_type_field = leave_type_map.get(leave.type_of_leave)
            if leave_type_field:
                current = getattr(leave_types, leave_type_field)
                if current is None:
                    current = 0  

                # Now this will not error
                if current < days:
                    messages.error(request, f"You do not have enough {leave.type_of_leave} days. Available: {current}, Requested: {days}")
                    return redirect('table_leave')

                # Deduct days
                setattr(leave_types, leave_type_field, max(current - days, 0))
                leave_types.save()

            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('table_leave')
    else:
        form = LeaveRequestForm()
    user_profile = request.user
    context = {
        'form': form,
        'user_info': {
            'full_name': f"{getattr(user_profile, 'first_name', '')} {getattr(user_profile, 'last_name', '')}",
            'employee_type': getattr(user_profile, 'employee_types', ''),
            'section': getattr(user_profile, 'section', ''),
            'designation': getattr(user_profile, 'designation', ''),
            'ecnumber': user_profile.username,
        }
    }
    return render(request, 'leave_system/create_leave.html', context)

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
            "status": leave.status,
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

def accumulate_vacation_leave_view(request, pk, employee_type, months=1):
    leave_types = get_object_or_404(LeaveTypes, pk=pk)
    leave_types.accumulate_vacation_leave(employee_type, months)
    messages.success(request, f"Vacation leave accumulated for {employee_type} by {months} month(s).")
    return redirect('leave_types')

def approve_leave (request):
  return render(request,'leave_system/awaiting_my_action.html')