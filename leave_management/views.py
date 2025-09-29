from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import LeaveRequestForm, LeaveTypesForm,  LeaveRequestFullForm
from django.http import JsonResponse
from django.db.models import Q
from .models import LeaveRequest, LeaveTypes
from it.users.models import *
from datetime import timedelta
from django.http import JsonResponse, Http404
from django.db import transaction
from django.utils import timezone

def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)  
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
            print('user_profile',user_profile)
            user = UserProfile.objects.filter(id=user_profile.id).first()
            print('user',user)
            leave_types = LeaveTypes.objects.filter(user=user).first()
            if not leave_types:
                messages.error(request, "Your leave balances are not set up. Please contact HR.")
                return redirect('leave_types')

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
                current = getattr(leave_types, leave_type_field, 0)
                if current is None:
                    current = 0  

                # --- Occasional leave rule ---
                if leave.type_of_leave == 'occassional leave':
                    if days > 3:
                        messages.error(request, "You can only apply for a maximum of 3 days per occasional leave application.")
                        return redirect('leave_types')
                    
                    year = timezone.now().year
                    taken_this_year = LeaveRequest.objects.filter(
                        user=user_profile,
                        type_of_leave='occassional leave',
                        start_date__year=year
                    ).aggregate(models.Sum('number_of_days'))['number_of_days__sum'] or 0
                    if taken_this_year + days > 12:
                        messages.error(request, f"You cannot exceed 12 days of occasional leave per year. Already taken: {taken_this_year}, Requested: {days}")
                        return redirect('leave_types')
                # --- End occasional leave rule ---

                if current < days:
                    messages.error(request, f"You do not have enough {leave.type_of_leave} days. Available: {current}, Requested: {days}")
                    return redirect('leave_types')

                # Deduct days
                setattr(leave_types, leave_type_field, max(current - days, 0))
                leave_types.save()

            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('leave_types')
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
    try:
        user = UserProfile.objects.filter(id=request.user.id).first()
        print('user',user)
        user_roles = user.get_user_role_for_application("leave management")
        print('user_roles',user_roles)
        role_name = getattr(user_roles, "name", None)
        print(f"User role for leave management: {role_name}")
    except AttributeError as e:
        print(f"Role error: {e}")
        role_name = None

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
        # Defensive user string extraction
        try:
            if leave.user:
                # If leave.user is a UserProfile with a related User object
                if hasattr(leave.user, "user") and hasattr(leave.user.user, "get_full_name"):
                    user_str = leave.user.user.get_full_name()
                # If leave.user is a User object
                elif hasattr(leave.user, "get_full_name"):
                    user_str = leave.user.get_full_name()
                else:
                    user_str = str(leave.user)
            else:
                user_str = ""
        except Exception as e:
            user_str = ""
            print(f"UserProfile error for leave id {leave.id}: {e}")


        try:
            attachments_url = leave.attachments.url if leave.attachments else ""
        except Exception as e:
            attachments_url = ""
            print(f"Attachment error for leave id {leave.id}: {e}")

        data.append({
            "id": leave.id,
            "ecnumber": leave.ecnumber,
            "user": user_str,
            "type_of_leave": leave.type_of_leave,
            "gender": leave.gender,
            "position": str(leave.position) if leave.position else "",
            "start_date": leave.start_date.strftime('%Y-%m-%d') if leave.start_date else "",
            "end_date": leave.end_date.strftime('%Y-%m-%d') if leave.end_date else "",
            "department": str(leave.department) if leave.department else "",
            "number_of_days": leave.number_of_days,
            "region": str(leave.region) if leave.region else "",
            "status": leave.status,
            "attachments": attachments_url,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def table_leave(request):
    try:
        user = UserProfile.objects.filter(id=request.user.id).first()
        print('user',user)
        user_roles = user.get_user_role_for_application("leave management")
        print('user_roles',user_roles)
        role_name = getattr(user_roles, "name", None)
        print(f"User role for leave management: {role_name}")
        is_requester = user_roles.name == 'Requester'
        print('requester',is_requester)
    except AttributeError as e:
        print(f"Role error: {e}")
        is_requester = False

    user = request.user
    qs = LeaveRequest.objects.filter(user=user)
    approved_count = qs.filter(status='approved').count()
    rejected_count = qs.filter(status='rejected').count()
    pending_count = qs.filter(status='pending').count()
    total_count = qs.count()

    return render(request, 'leave_system/leave_table.html', {
        'is_requester': is_requester,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'total_count': total_count,
    })

def create_leave_types(request):
    if request.method == 'POST':
        form = LeaveTypesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leave_types') 
    else:
        form = LeaveTypesForm()
    return render(request, 'leave_system/create.html', {'form': form})

def encashment_leave(request):
    form = LeaveRequestFullForm(request.POST or None)
    show_table = False
    leave_requests = None

    # Get current vacation leave
    vacation_leave = 0
    if hasattr(request.user, "leave_types"):
        vacation_leave = getattr(request.user.leave_types, "vacation_leave", 0)

    if request.method == 'POST' and form.is_valid():
        leave = form.save(commit=False)
        user_profile = request.user

        # Set required fields not in the form
        leave.user = user_profile
        leave.ecnumber = user_profile.username 
        leave.position = getattr(user_profile, 'designation', None)
        leave.department = getattr(user_profile, 'section', None)
        leave.region = getattr(user_profile, 'region', None)
        leave.status = 'waiting for encashment'
        leave.employee_types = getattr(user_profile, 'employee_types', '')

        # Calculate number_of_days if needed
        if leave.start_date and leave.end_date:
            day_count = 0
            current_day = leave.start_date
            while current_day <= leave.end_date:
                if current_day.weekday() < 5:
                    day_count += 1
                current_day += timedelta(days=1)
            leave.number_of_days = day_count

        # Save and update vacation leave atomically
        with transaction.atomic():
            leave.save()
            # Subtract total days from vacation leave
            if hasattr(user_profile, "leave_types"):
                leave_type_obj = user_profile.leave_types
                leave_type_obj.vacation_leave = max(0, leave_type_obj.vacation_leave - ((leave.days_encashed or 0) + (leave.days_taken or 0)))
                leave_type_obj.save()
                vacation_leave = leave_type_obj.vacation_leave

        messages.success(request, "Leave encashment request submitted successfully.")

        show_table = True
        leave_requests = LeaveRequest.objects.filter(user=request.user)
        form = LeaveRequestFullForm() 

    return render(request, 'leave_system/encashment.html', {
        'form': form,
        'leave_requests': leave_requests,
        'show_table': show_table,
        'vacation_leave': vacation_leave,  
    })

def leave_types_datatable(request):
    
    try:
        user_roles = request.user.get_user_role_for_application("leave management")
        role_name = getattr(user_roles, "name", None)
        print(f"User role for leave management: {role_name}")
    except AttributeError as e:
        print(f"Role error: {e}")
        role_name = None

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    # Optionally filter or restrict data based on role
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
    try:
        user_roles = request.user.get_user_role_for_application("leave management")
        is_requester= user_roles.name == 'Requester'
    except AttributeError as e:
        print(f"Role error: {e}")
        is_requester = False

    return render(request, 'leave_system/types_table.html', {
        'is_requester': is_requester
    })

def accumulate_vacation_leave_view(request, pk, employee_type, months=1):
    leave_types = get_object_or_404(LeaveTypes, pk=pk)
    leave_types.accumulate_vacation_leave(employee_type, months)
    messages.success(request, f"Vacation leave accumulated for {employee_type} by {months} month(s).")
    return redirect('leave_types')

def approve_leave (request,pk):
    leave = get_object_or_404(LeaveRequest,pk=pk)
    return render(request, 'leave_system/awaiting_my_action.html', {'leave': leave})

def update_leave_request(request, id):
    leave_request = LeaveRequest.objects.filter(id=id).first()
    if not leave_request:
        return render(request, '404.html', status=404)

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES, instance=leave_request)
        if form.is_valid():
            leave = form.save(commit=False)
            # If this is an encashment update, set status
            if leave.type_of_leave == 'vacation' and leave.days_encashed and leave.status == 'waiting for encashment':
                leave.status = 'encashed'
            leave.save()
            return redirect('/leave_table')  
    else:
        form = LeaveRequestForm(instance=leave_request)

    user_profile = request.user
    user_info = {
        'full_name': f"{getattr(user_profile, 'first_name', '')} {getattr(user_profile, 'last_name', '')}",
        'employee_type': getattr(user_profile, 'employee_types', ''),
        'section': getattr(user_profile, 'section', ''),
        'designation': getattr(user_profile, 'designation', ''),
        'ecnumber': user_profile.username,
    }

    return render(request, 'leave_system/update_leave.html', {
        'form': form,
        'user_info': user_info,
        'leave_request': leave_request,
    })

def leave_dashboard(request):
    try:
        user = UserProfile.objects.filter(id=request.user.id).first()
        print('user',user)
        user_roles = user.get_user_role_for_application("leave management")
        print('user_roles',user_roles)
        role_name = getattr(user_roles, "name", None)
        print(f"User role for leave management: {role_name}")
        is_requester = user_roles.name == 'Requester'
        print('requester',is_requester)
    except AttributeError as e:
        print(f"Role error: {e}")
        is_requester = False

    user = request.user
    qs = LeaveRequest.objects.filter(user=user)
    approved_count = qs.filter(status='approved').count()
    rejected_count = qs.filter(status='rejected').count()
    pending_count = qs.filter(status='pending').count()
    total_count = qs.count()
    waiting_for_encashment = qs.filter(status='waiting for encashment').count() 
    encashed = qs.filter(status='encashed').count()
   

    return render(request, 'leave_system/leave_dashboard.html', {
        'is_requester': is_requester,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'total_count': total_count,
        'waiting_for_encashment': waiting_for_encashment,
        'encashed': encashed, 
    })

def recent_leave_activity(request):
    recent_activities = LeaveRequest.objects.all().order_by('-end_date') 
    return render(request, 'leave_system/recent_leave_activity.html', {
        'recent_activities': recent_activities,
    })