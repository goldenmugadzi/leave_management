from django.db import models
from it.users.models import *
from django.conf import settings

# # Create your models here.
class Meetings(models.Model):
     employees_invited = models.ManyToManyField(UserProfile, blank=True, related_name="meetings")
     department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
     regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
     type_of_meeting = models.CharField(max_length=100,help_text="Meeting Type",  choices=[('RMT Meeting', 'RMT Meeting') ,('Emergency Meeting', 'Emergency Meeting'), ('SHE Meeting', 'SHE Meeting'),('Section Meeting', 'Section Meeting'), ('DMT Meeting', 'DMT Meeting'),('Productivity Meeting', 'Productivity Meeting'),('Works Council Meeting', 'Works Council Meeting'),('Operational Meeting', 'Operational Meeting'), ('Depot Morning Meeting', 'Depot Morning Meeting'), ('Audit Meeting', 'Audit Meeting'), ('Other Meeting', 'Other Meeting'),])
     date_of_meeting= models.DateField() 
     list_of_invited_attendees= models.CharField(max_length=900)
     list_of_agenda_items=models.CharField(max_length=900)
     cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
     venue = models.CharField(max_length=100,help_text="Type of venue" , choices=[('Virtual','Virtual')])
     start_time =models.TimeField()
     attach_previous_minutes = models.FileField(upload_to='meetings/', blank=True, null=True)
     end_time =models.TimeField()
     confirm_status = models.CharField(max_length=400,help_text="Status",choices=[('Postponed','Postponed'),('Held','Held'),('Cancelled','Cancelled ')])
     comments = models.TextField(max_length=500)
     depot = models.ForeignKey(Depots,on_delete=models.DO_NOTHING, blank=True, null=True)


 

