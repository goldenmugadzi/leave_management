from django.db import models
from django.contrib.auth import get_user_model

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
        
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    ecnumber = models.CharField(max_length=50)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    type_of_leave = models.CharField(max_length=20, choices=LEAVE_TYPES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.PositiveIntegerField()
    region = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user} - {self.type_of_leave} ({self.start_date} to {self.end_date})"
