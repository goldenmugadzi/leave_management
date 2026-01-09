from django.db import models
from it.users.models import *
from django.conf import settings

# # Create your models here.
class Venue(models.Model):
    VENUE_TYPE_CHOICES = [
     ('Virtual','Virtual'),('Function Room 3','Function Room 3'),('Function Room 4','Function Room 4'),('Fourth Floor Boardroom','Fourth Floor Boardroom'),('Fithy Floor Kitchen','Fithy Floor Kitchen'),('GIS Drones','GIS Drones')]
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=[('Available', 'Available'), ('Booked', 'Booked')],
        default='Available'
    )

    def __str__(self):
        return f"{self.name}"

class VenueBooking(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING,  verbose_name="Department/Region")
    start_time = models.TimeField()
    start_date = models.DateField()
    end_time = models.TimeField()
    end_date = models.DateField()
    type_of_meeting = models.CharField(max_length=100,help_text="Meeting Type",  choices=[('RMT Meeting', 'RMT Meeting') ,('Emergency Meeting', 'Emergency Meeting'), ('SHE Meeting', 'SHE Meeting'),('Section Meeting', 'Section Meeting'), ('DMT Meeting', 'DMT Meeting'),('Productivity Meeting', 'Productivity Meeting'),('Works Council Meeting', 'Works Council Meeting'),('Operational Meeting', 'Operational Meeting'), ('Depot Morning Meeting', 'Depot Morning Meeting'), ('Audit Meeting', 'Audit Meeting'), ('Other Meeting', 'Other Meeting'),])
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'),('Transferred to Another Venue', 'Transferred to Another Venue'), ('Cancelled', 'Cancelled')], default='Pending')
    
class Meetings(models.Model):
     booking = models.ForeignKey(
     VenueBooking,
     on_delete=models.CASCADE,
     null=True,
     blank=True,
     related_name='meetings'
     )
     employees_invited = models.ManyToManyField(UserProfile, blank=True, related_name="meetings")
     department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True, verbose_name="Department/Region")
     regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
     type_of_meeting = models.CharField(max_length=100,help_text="Meeting Type",  choices=[('RMT Meeting', 'RMT Meeting') ,('Emergency Meeting', 'Emergency Meeting'), ('SHE Meeting', 'SHE Meeting'),('Section Meeting', 'Section Meeting'), ('DMT Meeting', 'DMT Meeting'),('Productivity Meeting', 'Productivity Meeting'),('Works Council Meeting', 'Works Council Meeting'),('Operational Meeting', 'Operational Meeting'), ('Depot Morning Meeting', 'Depot Morning Meeting'), ('Audit Meeting', 'Audit Meeting'), ('Other Meeting', 'Other Meeting'),])
     meeting_number = models.PositiveIntegerField(default=0)
     start_date = models.DateField()
     end_date = models.DateField()
     list_of_invited_attendees= models.CharField(max_length=900)
     list_of_agenda_items=models.CharField(max_length=900)
     cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Depot/Center")
     venue = models.ForeignKey('Venue', on_delete=models.SET_NULL, null=True, blank=True)
     start_time =models.TimeField()
     attach_previous_minutes = models.FileField(upload_to='meetings/', blank=True, null=True)
     end_time =models.TimeField()
     confirm_status = models.CharField(max_length=400,help_text="Status",choices=[('Postponed','Postponed'),('Held','Held'),('Cancelled','Cancelled ')])
     comments = models.TextField(max_length=500)
     depot = models.ForeignKey(Depots,on_delete=models.DO_NOTHING, blank=True, null=True)
     estimated_cost_of_meeting = models.PositiveIntegerField(default=0)
     actual_cost_of_meeting = models.PositiveIntegerField(default=0)
     special_invitations = models.TextField(max_length=900)
     comments = models.TextField(max_length=500)








