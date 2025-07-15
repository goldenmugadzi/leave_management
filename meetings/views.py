from django.shortcuts import render, redirect
from .forms import MeetingsForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Meetings

def create_meeting(request):
    if request.method == 'POST':
        form = MeetingsForm(request.POST)
        if form.is_valid():
            print('form.employees_invited',form.employees_invited)
            leave = form.save(commit=False)
            leave.user = request.user  
            leave.save()
            messages.success(request, "meeting request submitted successfully.")
            return redirect('table_meeting') 
    else:
        form = MeetingsForm()
    return render(request, 'Meetings/create_meeting.html', {'form': form})

def meetings_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = Meetings.objects.all()
    if search_value:
        qs = qs.filter(
            Q(employees_invited__user__username__icontains=search_value) |
            Q(department__section__icontains=search_value) |
            Q(regions__region__icontains=search_value) |
            Q(type_of_meeting__icontains=search_value) |
            Q(list_of_invited_attendees__icontains=search_value) |
            Q(list_of_agenda_items__icontains=search_value)
        )

    total = qs.count()
    qs = qs.order_by('-date_of_meeting')[start:start+length]

    data = []
    for meeting in qs:
        employees = list(meeting.employees_invited.all())
        employees_str = ", ".join([str(user) for user in employees]) if employees else "None"
        data.append({
            "id": meeting.id,
            "employees_invited": employees_str,
            "department": str(meeting.department) if meeting.department else "",
            "regions": str(meeting.regions) if meeting.regions else "",
            "type_of_meeting": meeting.type_of_meeting,
            "date_of_meeting": meeting.date_of_meeting.strftime('%Y-%m-%d') if meeting.date_of_meeting else "",
            "start_time": meeting.start_time.strftime('%H:%M') if meeting.start_time else "",
            "end_time": meeting.end_time.strftime('%H:%M') if meeting.end_time else "",
            "venue": meeting.venue,
            "attach_previous_minutes": meeting.attach_previous_minutes.url if meeting.attach_previous_minutes else "",
            "list_of_invited_attendees": meeting.list_of_invited_attendees,
            "list_of_agenda_items": meeting.list_of_agenda_items,
            "cost_center": str(meeting.cost_center) if meeting.cost_center else "",
            "confirm_status": meeting.confirm_status,
            "comments": meeting.comments,
            "depot": str(meeting.depot) if meeting.depot else "",
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def table_meetings (request):
  return render(request,'Meetings/table_meetings.html')

