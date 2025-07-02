from django.db import models
from it.users.models import *

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('leave for national events', 'leave for national events'),
        ('sick leave', 'sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('special leave', 'special Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('vacation','vacation'),
        ('occassional leave', 'occasional leave'),
        ('study leave','study leave')
        
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    
    ]

    ecnumber = models.PositiveIntegerField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="leave")
    type_of_leave = models.CharField(max_length=200, choices=LEAVE_TYPES)
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES)
    position = models.ForeignKey(Designations, on_delete=models.DO_NOTHING , blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    number_of_days = models.PositiveIntegerField()
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    

    def __str__(self):
        return f"{self.user} - {self.type_of_leave} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.number_of_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

class LeaveTypes(models.Model):
    leave_for_national_events = models.IntegerField(null=True, blank=True)
    sick_leave = models.IntegerField(null=True, blank=True)
    maternity_leave = models.IntegerField(null=True, blank=True)
    special_leave = models.IntegerField(null=True, blank=True)
    unpaid_leave = models.IntegerField(null=True, blank=True)
    vacation_leave = models.IntegerField(null=True, blank=True)
    study_leave = models.IntegerField(null=True, blank=True)
    occasional_leave = models.IntegerField(null=True, blank=True)
    mandatory_leave = models.IntegerField(null=True, blank=True)
