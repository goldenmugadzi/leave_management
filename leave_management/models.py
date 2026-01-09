from django.db import models
from it.users.models import *
from datetime import timedelta
from approve.models import Process,Step,Workflow,Approval

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
   
    EMPLOYEE_TYPES  = [
        ('Permanent','Permanent'),
        ('Apprentice','Apprentice'),
        ('PGT','PGT'),
        ('Contract','Contract'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waiting for encashment','waiting for encashment'),
        ('encashed', 'encashed')
    ]

    ecnumber = models.PositiveIntegerField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="leave")
    type_of_leave = models.CharField(max_length=200, choices=LEAVE_TYPES)
    position = models.ForeignKey(Designations, on_delete=models.DO_NOTHING , blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    number_of_days = models.PositiveIntegerField(blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    employee_types = models.CharField(max_length=200, choices=EMPLOYEE_TYPES)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='pending')
    days_taken = models.PositiveIntegerField(default=0, blank=True, null=True)
    days_encashed = models.PositiveIntegerField(default=0, blank=True, null=True)
    total_days = models.PositiveIntegerField(default=0, blank=True, null=True)
    attachments = models.FileField(upload_to='leave_management/', blank=True, null=True)
    process=models.ForeignKey(Process, on_delete=models.CASCADE, blank=True, null=True)
    

    def __str__(self):
        return f"{self.user} - {self.type_of_leave} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            day_count = 0
            current_day = self.start_date
            while current_day <= self.end_date:
                if current_day.weekday() < 5: 
                    day_count += 1
                current_day += timedelta(days=1)
            self.number_of_days = day_count
        super().save(*args, **kwargs)

class LeaveTypes(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='leave_types')
    leave_for_national_events = models.IntegerField(null=True, blank=True)
    sick_leave = models.IntegerField(null=True, blank=True)
    maternity_leave = models.IntegerField(null=True, blank=True)
    special_leave = models.IntegerField(null=True, blank=True)
    unpaid_leave = models.IntegerField(null=True, blank=True)
    vacation_leave = models.FloatField(null=True, blank=True, default=0)
    study_leave = models.IntegerField(null=True, blank=True)
    occasional_leave = models.IntegerField(null=True, blank=True)
    mandatory_leave = models.IntegerField(null=True, blank=True)

    def accumulate_vacation_leave(self, employee_type, months=1):
       
        if self.vacation_leave is None:
            self.vacation_leave = 0
        if employee_type == "Contract":
            rate = 1.833
        else:
            rate = 2.5
        self.vacation_leave = min(self.vacation_leave + rate * months, 240)
        self.save()


class LeaveActivity(models.Model):
    ACTIONS = [
        ("applied", "Applied"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("edited", "Edited"),
        ("encashed", "Encashed"),
    ]

    leave = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_actions")
    action = models.CharField(max_length=50, choices=ACTIONS)
    action_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_action_performed")
    type_of_leave = models.CharField(max_length=200)
    status = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leave.id} - {self.action} by {self.action_by}"
