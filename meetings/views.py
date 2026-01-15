from django.views.decorators.http import require_GET
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect
from .forms import MeetingsForm,MeetingsUpdateForm, VenueBookingForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Meetings, VenueBooking, Venue
from it.users.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from exchangelib import Credentials, Account, Configuration, Message, Mailbox
from exchangelib import HTMLBody
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from datetime import timedelta ,datetime


@login_required
def create_meeting(request, booking_id=None):
    
    booking = None
    initial_data = {}

    if booking_id:
        booking = get_object_or_404(VenueBooking, id=booking_id)
        initial_data = {
            'venue': booking.venue,
            'department': booking.department,
            'start_date': booking.start_date,
            'end_date':booking.end_date,
            'start_time': booking.start_time,
            'end_time': booking.end_time,
            'type_of_meeting': booking.type_of_meeting,
        }

    if request.method == 'POST':
        form = MeetingsForm(request.POST, request.FILES)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.user = request.user
            meeting.confirm_status = 'Pending'
            meeting.save()
            form.save_m2m()  # Save many-to-many fields (like attendees)

            # ✅ Get emails of selected users (adjust field name as per your model)
            employees_invited  = meeting.employees_invited.all()  # or meeting.participants.all()
            to_emails = [user.email for user in employees_invited  if user.email]

            if to_emails:
                subject = f"Meeting Invitation: {meeting.type_of_meeting}"
                body = f"""
                <h3>You have been invited to a meeting</h3>
                <p><strong>Meeting Type:</strong> {meeting.type_of_meeting}</p>
                <p><strong>Venue:</strong> {meeting.venue}</p>
                <p><strong>Date:</strong> {meeting.start_date}</p>
                <p><strong>Time:</strong> {meeting.start_time} - {meeting.end_time}</p>
                <p><strong>Requested By:</strong> {request.user.get_full_name()}</p>
                """

                try:
                    ms_exhange_send(subject, body, to_emails, [])
                    messages.success(request, "Meeting request submitted and notifications sent successfully.")
                except Exception as e:
                    print("Email error:", e)
                    messages.warning(request, "Meeting created but failed to send email notifications.")
            else:
                messages.info(request, "Meeting created, but no attendees have valid email addresses.")

            return redirect('meetings_dashboard')
    else:
        form = MeetingsForm(initial=initial_data)

    return render(request, 'Meetings/create_meeting.html', {
        'form': form,
        'booking': booking
    })

def meetings_datatable(request):
    
    try:
        user_roles = request.user.get_user_role_for_application("meeting")
        role_name = getattr(user_roles, "name", None)
        print(f"User role for Meetings: {role_name}")
    except AttributeError as e:
        print(f"Role error: {e}")
        role_name = None
        
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
    qs = qs.order_by('-start_date')[start:start+length]


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
                "start_date": meeting.start_date.strftime("%Y-%m-%d") if meeting.start_date else "",
                "end_date": meeting.end_date.strftime("%Y-%m-%d") if meeting.end_date else "",
                "start_time": meeting.start_time.strftime('%H:%M') if meeting.start_time else "",
                "end_time": meeting.end_time.strftime('%H:%M') if meeting.end_time else "",
                "venue": str(meeting.venue) if meeting.venue else "",  
                "attach_previous_minutes": meeting.attach_previous_minutes.url if meeting.attach_previous_minutes else "",
                "list_of_agenda_items": meeting.list_of_agenda_items,
                "cost_center": str(meeting.cost_center) if meeting.cost_center else "",
                "estimated_cost_of_meeting": meeting.estimated_cost_of_meeting,
                "actual_cost_of_meeting": meeting.actual_cost_of_meeting,
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
    try:
        user = UserProfile.objects.filter(id=request.user.id).first()
        print('user',user)
        user_roles = user.get_user_role_for_application("meeting")
        print('user_roles',user_roles)
        role_name = getattr(user_roles, "name", None)
        print(f"User role for Meetings: {role_name}")
        is_requester = user_roles.name == 'Requester'
        print('requester',is_requester)
    except AttributeError as e:
        print(f"Role error: {e}")
        is_requester = False
        
    user = request.user
    qs = Meetings.objects.filter(user=user)    
        
    return render(request,'Meetings/table_meetings.html',{
        'is_requester': is_requester,
    })

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
    try:
        user = UserProfile.objects.filter(id=request.user.id).first()
        user_roles = user.get_user_role_for_application("meeting")
        role_name = getattr(user_roles, "name", None)
        is_requester = user_roles.name == 'Requester'
    except AttributeError as e:
        is_requester = False

    return render(request, 'Meetings/meeting_dashboard.html', {
        'is_requester': is_requester,
    })

def create_venue_booking(request):
    if request.method == 'POST':
        form = VenueBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)

            # Check for overlapping bookings
            if VenueBooking.objects.filter(
                venue=booking.venue,
                start_date__lte=booking.end_date,
                end_date__gte=booking.start_date
            ).exists():
                messages.error(request, "This venue is already booked for one or more of the selected days.")
                return render(request, 'Meetings/book_venue.html', {'form': form})
            
            booking.created_by = request.user
            booking.status = "Pending"
            booking.save()
            # Only one success message should be shown
            return redirect("meetings_dashboard")

        # Form invalid → re-render page with errors
        return render(request, 'Meetings/book_venue.html', {'form': form})

    # GET request → show blank form
    form = VenueBookingForm()
    return render(request, 'Meetings/book_venue.html', {'form': form})

def venues_datatable(request):
    today = now().date()

    booked = VenueBooking.objects.filter(
        venue=OuterRef('pk'),
        end_date__gte=today,
        status__in=["Pending", "Confirmed"]
    )

    venues = Venue.objects.all()

    data = []
    for v in venues:
        is_booked = VenueBooking.objects.filter(
            venue=v,
            end_date__gte=today,
            status__in=["Pending","Confirmed"]
        ).exists()
        data.append({
            "id": v.id,
            "name": str(v),
            "capacity": v.capacity,
            "status": "Booked" if is_booked else "Available"
        })

    return JsonResponse({"data": data})

def booked_venues_datatable(request):
    bookings = VenueBooking.objects.all().order_by('-start_date', 'start_time')  # optional ordering

    data = []
    for b in bookings:
        data.append({
            "id": b.id,
            "venue": str(b.venue),
            "department": str(b.department),
            "created_by": str(b.created_by),
            "start_time": b.start_time.strftime("%H:%M"),
            "end_time": b.end_time.strftime("%H:%M"),
            "start_date": b.start_date.strftime("%Y-%m-%d"),
            "end_date": b.end_date.strftime("%Y-%m-%d"),
            "capacity": b.capacity,
            "type_of_meeting": b.type_of_meeting,
            "status": b.status,
        })

    return JsonResponse({"data": data})
 
def get_exchange_account():
  ## changed mail password
  ## password change
    from decouple import config as cnf
    print(cnf)
    credentials = Credentials(
        username='bexcel@zedc.co.zw',
        password='Iphone@123456789'
    )
    print("Credentials: ", credentials)
    config = Configuration(
        server='mail.zesaholdings.co.zw',
        credentials=credentials,
    )
    print("Config: ", config)
    account = Account(
        primary_smtp_address='bexcel@zedc.co.zw',
        config=config,
        autodiscover=False,
        access_type='delegate'
    )
    print("Successfully connected to Exchange server.")
    return account

@login_required
def ms_exhange_test(request):
    account = get_exchange_account()
    message = Message(
        account=account,
        folder=account.sent,
        subject="Test Email",
        body="This is a test email",
        to_recipients=[Mailbox(email_address='goldenmugadzi@gmail.com')]
    )
    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})

def ms_exhange_send(subject, body, to_recipients, cc_recipients):
    account = get_exchange_account()
    print("account",account),

    message = Message(
        account=account,
        folder=account.sent,
        subject=subject,
        body=HTMLBody(body), 
        to_recipients=[Mailbox(email_address=recipient) for recipient in to_recipients],
        cc_recipients=[Mailbox(email_address=recipient) for recipient in cc_recipients]
    )
    print("message",message),
    message.send()
    return JsonResponse({"status": "success", "message": "Email sent successfully"})

def booked_venue (request):
    try:
        user = UserProfile.objects.filter(id=request.user.id).first()
        print('user',user)
        user_roles = user.get_user_role_for_application("meeting")
        print('user_roles',user_roles)
        role_name = getattr(user_roles, "name", None)
        print(f"User role for Meetings: {role_name}")
        is_requester = user_roles.name == 'Requester'
        print('requester',is_requester)
    except AttributeError as e:
        print(f"Role error: {e}")
        is_requester = False
        
    return render(request,'Meetings/booked_venue.html',{
        'is_requester': is_requester,
        
    })

from django.utils.timezone import now

def update_venue_booking(request, pk):
    booking = get_object_or_404(VenueBooking, pk=pk)

    old_status = booking.status

    if request.method == "POST":
        form = VenueBookingForm(request.POST, instance=booking)
        if form.is_valid():
            updated_booking = form.save()

            creator = updated_booking.created_by

            status_messages = {
                "Cancelled": "has been cancelled",
                "Postponed": "has been postponed",
                "Confirmed": "has been confirmed",
                "Transferred to Another Venue": "has been transferred to another venue",
            }

            # Handle transfer logic in view
            if updated_booking.status == "Transferred to Another Venue":
                new_venue_id = request.POST.get("new_venue_id")
                if new_venue_id:
                    from meetings.models import Venue
                    try:
                        new_venue = Venue.objects.get(pk=new_venue_id)
                        # Check if the new venue is already booked for the same period
                        overlap = VenueBooking.objects.filter(
                            venue=new_venue,
                            start_date__lte=updated_booking.end_date,
                            end_date__gte=updated_booking.start_date,
                            status__in=["Pending", "Approved"]
                        ).exists()
                        if not overlap:
                            # Create a new booking for the new venue with same dates/user
                            VenueBooking.objects.create(
                                venue=new_venue,
                                start_date=updated_booking.start_date,
                                end_date=updated_booking.end_date,
                                created_by=updated_booking.created_by,
                                status="Pending"
                            )
                            # Optionally, cancel the old booking
                            updated_booking.status = "Cancelled"
                            updated_booking.save()
                        else:
                            messages.error(request, "The selected venue is already booked for the chosen period.")
                            return render(request, 'Meetings/venue_booking_update.html', {"form": form, "booking": booking})
                    except Venue.DoesNotExist:
                        messages.error(request, "Selected venue does not exist.")
                        return render(request, 'Meetings/venue_booking_update.html', {"form": form, "booking": booking})

            if creator and old_status != updated_booking.status:
                action = status_messages.get(
                    updated_booking.status,
                    "has been updated"
                )

                msg = (
                    f"Your venue booking for {updated_booking.venue} {action}.\n"
                    f"Booking period: {updated_booking.start_date} "
                    f"to {updated_booking.end_date}"
                )

                notify_user(
                    user_=creator,
                    msg=msg,
                    notification_type="Venue Booking Update",
                    url="/meetings/booked-venues/",
                    id=updated_booking.id,
                    request=request
                )

            messages.success(request, "Venue booking updated successfully.")
            return redirect("booked_venue")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VenueBookingForm(instance=booking)

    return render(
        request,
        "Meetings/venue_booking_update.html",
        {"form": form, "booking": booking}
    )


@login_required
def scheduled_meetings(request):
    """Render the scheduled meetings page with DataTable."""
    return render(request, 'Meetings/scheduled_meetings.html', {
        'is_requester': hasattr(request.user, 'is_requester') and request.user.is_requester,
        'user': request.user,
    })

def available_venues(request):
    """Render the available venues page with DataTable."""
    return render(request, 'Meetings/available_venues.html', {
        'user': request.user,
    })
    
def notify_user(user_, msg, notification_type, url, id, request):
    try:
        Notification.objects.create(
            user=user_,
            message=msg,
            notification_type=notification_type,
            notification_id=id,
            url=url,
            created_at=datetime.now(),
        )
        
        return True
    except Exception as e:
        print("error: ", str(e))
        return False

def notification_update(user, id):
    notification = Notification.objects.filter(user=user, notification_id=id).first()
    if notification:
        notification.is_read = True
        notification.save()
    return True


# AJAX endpoint to return VenueBooking details for auto-population
@require_GET
def booking_details(request):
    booking_id = request.GET.get('booking_id')
    if not booking_id:
        return JsonResponse({'error': 'No booking_id provided'}, status=400)
    try:
        booking = VenueBooking.objects.select_related('venue', 'department').get(pk=booking_id)
        data = {
            'venue': booking.venue.id if booking.venue else None,
            'venue_name': str(booking.venue) if booking.venue else '',
            'department': booking.department.id if booking.department else None,
            'department_name': str(booking.department) if booking.department else '',
            'start_date': booking.start_date.strftime('%Y-%m-%d') if booking.start_date else '',
            'end_date': booking.end_date.strftime('%Y-%m-%d') if booking.end_date else '',
            'start_time': booking.start_time.strftime('%H:%M') if booking.start_time else '',
            'end_time': booking.end_time.strftime('%H:%M') if booking.end_time else '',
            'type_of_meeting': booking.type_of_meeting,
        }
        return JsonResponse(data, encoder=DjangoJSONEncoder)
    except VenueBooking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)