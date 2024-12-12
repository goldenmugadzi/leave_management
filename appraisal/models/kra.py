from django.db import models
from helpers.models.timestamp import TimeStamp
from django.contrib.auth import get_user_model
from .helpers import YearQuarter

User = get_user_model()

class KeyResultArea(TimeStamp):
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    name = models.CharField(max_length=255)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    def __str__(self):
        return f"{self.created_by} - {self.quarter}"
    
class Activity(TimeStamp):
    kra = models.ForeignKey(KeyResultArea, on_delete=models.CASCADE)
    assigned_user = models.ForeignKey(User, on_delete=models.RESTRICT)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.assigned_user}"
    
    class Meta:
        verbose_name_plural = "Activities"
    
METRIC_TYPES = [
        ('Quantity', 'Quantity'),
        ('Quality', 'Quality'),
        ('Timeliness', 'Timeliness'),
        ('Cost', 'Cost'),
    ]

class Target(TimeStamp):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    name = models.CharField(max_length=255, blank=False, null=False)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    allowance_variance = models.DecimalField(max_digits=10, decimal_places=2)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)  
    unit = models.CharField(max_length=30, blank=True, null=True)  

    def __str__(self):
        return f"{self.activity}"


class TargetScore(TimeStamp):
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    actual_performance = models.DecimalField(max_digits=10, decimal_places=2)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    actual_variance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comments = models.TextField()

    def __str__(self):
        return f"{self.target}"
    