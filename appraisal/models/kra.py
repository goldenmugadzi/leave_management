from django.db import models
from helpers.models.timestamp import TimeStamp
from django.contrib.auth import get_user_model
from .helpers import YearQuarter
from .appraisal import Appraisal

User = get_user_model()

class KeyResultArea(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="appraisal_kra", null=True, blank=True)
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    name = models.CharField(max_length=255)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    def __str__(self):
        return f"{self.created_by} - {self.quarter}"
    
class Activity(TimeStamp):
    kra = models.ForeignKey(KeyResultArea, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.name}"
    
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
    agreed_target = models.DecimalField(max_digits=5, decimal_places=2)
    allowable_variance = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=30, blank=True, null=True)  

    def __str__(self):
        return f"{self.activity}"


class TargetScore(TimeStamp):
    target = models.OneToOneField(Target, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comments = models.TextField()
    is_scored = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.target}"
    