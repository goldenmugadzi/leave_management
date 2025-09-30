from django.shortcuts import render, redirect
from .forms import MeetingsForm,MeetingsUpdateForm, VenueBookingForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Meetings, VenueBooking, Venue
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now


def create_meeting(request, booking_id=None):
    booking = None
    meeting_instance = None

    if booking_id:
        booking = get_object_or_404(VenueBooking, id=booking_id)
        
        meeting_instance = Meetings(
            venue=booking.venue,
            department=booking.department,
            date_of_meeting=booking.date_of_meeting,
            start_time=booking.start_time,
            end_time=booking.end_time,
            type_of_meeting=booking.type_of_meeting
        )

    if request.method == 'POST':
        form = MeetingsForm(request.POST, request.FILES, instance=meeting_instance)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.user = request.user
            meeting.confirm_status = 'Pending'
            meeting.save()
            form.save_m2m()
            messages.success(request, "Meeting request submitted successfully.")
            return redirect('meetings_dashboard')
    else:
        form = MeetingsForm(instance=meeting_instance)

    return render(request, 'Meetings/create_meeting.html', {
        'form': form,
        'booking': booking
    })



def meetings_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs_all = Meetings.objects.all()
    records_total = qs_all.count()

    qs = qs_all
    if search_value:
        qs = qs.filter(
            Q(employees_invited__user__username__icontains=search_value) |
            Q(employees_invited__user__first_name__icontains=search_value) |
            Q(employees_invited__user__last_name__icontains=search_value) |
            Q(department__section__icontains=search_value) |
            Q(regions__region__icontains=search_value) |
            Q(type_of_meeting__icontains=search_value) |
            Q(list_of_agenda_items__icontains=search_value)
        ).distinct()

    records_filtered = qs.count()
    qs = qs.order_by('-date_of_meeting')[start:start+length]


    data = []
    for meeting in qs:
            employees = meeting.employees_invited.all()
            # Adjust depending on your model structure
            employees_str = ", ".join([
                getattr(e.user, 'get_full_name', lambda: str(e))() if hasattr(e, 'user') else str(e)
                for e in employees
            ]) if employees.exists() else "None"

            data.append({
                "id": meeting.id,
                "employees_invited": employees_str,
                "department": str(meeting.department) if meeting.department else "",
                "regions": str(meeting.regions) if meeting.regions else "",
                "type_of_meeting": meeting.type_of_meeting,
                "date_of_meeting": meeting.date_of_meeting.strftime('%Y-%m-%d') if meeting.date_of_meeting else "",
                "start_time": meeting.start_time.strftime('%H:%M') if meeting.start_time else "",
                "end_time": meeting.end_time.strftime('%H:%M') if meeting.end_time else "",
                "venue": str(meeting.venue) if meeting.venue else "",  
                "attach_previous_minutes": meeting.attach_previous_minutes.url if meeting.attach_previous_minutes else "",
                "list_of_agenda_items": meeting.list_of_agenda_items,
                "cost_center": str(meeting.cost_center) if meeting.cost_center else "",
                "confirm_status": meeting.confirm_status,
                "comments": meeting.comments,
                "depot": str(meeting.depot) if meeting.depot else "",
            })


    return JsonResponse({
        "draw": draw,
       "recordsTotal": records_total,
       "recordsFiltered": records_filtered,
        "data": data
    })
   
def table_meetings (request):
  return render(request,'Meetings/table_meetings.html')

def update_meeting(request, id):
    meetings = Meetings.objects.filter(id=id).first()
    if not meetings:
        return render(request, '404.html', status=404)

    if request.method == 'POST':
        form = MeetingsUpdateForm(request.POST, request.FILES, instance=meetings)
        if form.is_valid():
            form.save()
            return redirect('/meetings_dashboard')  
    else:
        form = MeetingsUpdateForm(instance=meetings)

    return render(request, 'Meetings/create_meeting.html', {
        'form': form,
        'meetings': meetings,
    })

def meetings_dashboard(request):
    return render(request, 'Meetings/meeting_dashboard.html')

def create_venue_booking(request):
    if request.method == 'POST':
        form = VenueBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            
            # Mark the venue as booked
            venue = booking.venue
            venue.is_available = False
            venue.status = 'Booked'
            venue.save()
            
            booking.save()
            return redirect('meetings_dashboard')
        else:
            print('Form errors:', form.errors)
    else:
        form = VenueBookingForm()
    return render(request, 'Meetings/book_venue.html', {'form': form})

def venues_datatable(request):
    current_time = now()
    current_date = current_time.date()
    current_time_only = current_time.time()

    venues = Venue.objects.all()
    data = []

    for v in venues:
        # Check if this venue has any ACTIVE or UPCOMING booking today
        active_booking = VenueBooking.objects.filter(
            venue=v,
            date_of_meeting=current_date,
            end_time__gte=current_time_only  # exclude past bookings
        ).exists()

        if not active_booking:
            data.append({
                "id": v.id,
                "name": str(v),
                "capacity": v.capacity,
                "status": "Available"
            })

    return JsonResponse({"data": data})

def booked_venues_datatable(request):
    current_time = now()
    current_date = current_time.date()
    current_time_only = current_time.time()

    # Show all bookings for today, including ones that have not started yet
    bookings = VenueBooking.objects.filter(
        date_of_meeting=current_date,
        end_time__gte=current_time_only  # exclude bookings already finished
    )

    data = []
    for b in bookings:
        data.append({
            "id": b.id,
            "venue": str(b.venue),
            "department": str(b.department),
            "start_time": b.start_time.strftime("%H:%M"),
            "end_time": b.end_time.strftime("%H:%M"),
            "date_of_meeting": b.date_of_meeting.strftime("%Y-%m-%d"),
            "capacity": b.capacity,
            "type_of_meeting": b.type_of_meeting,
        })

    return JsonResponse({"data": data})

def booked_venue (request):
  return render(request,'Meetings/booked_venue.html')

def update_venue_booking(request, pk):
    booking = get_object_or_404(VenueBooking, pk=pk)

    if request.method == "POST":
        form = VenueBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, "Venue booking updated successfully.")
            return redirect("booked_venue") 
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VenueBookingForm(instance=booking)

    return render(request, "Meetings/venue_booking_update.html", {"form": form, "booking": booking})