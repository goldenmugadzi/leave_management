from django.db import models
from it.users.models import *
from datetime import timedelta

class AttendanceRecord(models.Model):
    REASON_CHOICES = [
        ('sick_leave', 'Sick Leave'),
        ('occasional_leave', 'Occasional Leave'),
        ('vacation_leave', 'Vacation Leave'),
        ('away_on_business', 'Away on Business'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="register")
    status = models.CharField(max_length=7, choices=STATUS_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, blank=True, null=True)
    date = models.DateField()

    def clean(self):
        from django.core.exceptions import ValidationError
        # If status is absent, reason must be set
        if self.status == 'absent' and not self.reason:
            raise ValidationError('Reason must be provided if user is absent.')
        # If status is present, reason must be empty
        if self.status == 'present' and self.reason:
            raise ValidationError('Reason must be empty if user is present.')

    def __str__(self):
        return f"{self.date} - {self.user} ({self.section}): {self.status}"

