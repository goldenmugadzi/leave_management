from django.db import models
from helpers.models.timestamp import TimeStamp
from .helpers import YearQuarter
from .appraisal import Appraisal

class KeyResultArea(TimeStamp):
    name = models.CharField(max_length=255)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name}"

        
class AppraisalKra(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="appraisal_kra", null=True, blank=True)
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT)
    key_result_area = models.ForeignKey(KeyResultArea, on_delete=models.RESTRICT, related_name="key_result_area", null=True, blank=True)
    supervisor_activity = models.ForeignKey("Activity", on_delete=models.RESTRICT, related_name="activity", null=True, blank=True)
    
    def __str__(self):
        return f"{self.appraisal}"
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(key_result_area__isnull=False, supervisor_activity__isnull=True) |
                    models.Q(key_result_area__isnull=True, supervisor_activity__isnull=False)
                ),
                name="only_one_reference_allowed"
            )
        ]
    
    
PERFORMANCE_INDICATOR = [
        ('Quantity', 'Quantity'),
        ('Quality', 'Quality'),
        ('Timeliness', 'Timeliness'),
        ('Cost', 'Cost'),
    ]

class Activity(TimeStamp):
    appraisal_kra = models.ForeignKey(AppraisalKra, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField()
    performance_indicator = models.CharField(max_length=30, choices=PERFORMANCE_INDICATOR, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    agreed_target = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    allowable_variance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    unit = models.CharField(max_length=30, blank=True, null=True)  
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name_plural = "Activities"
    

class TargetScore(TimeStamp):
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comments = models.TextField()
    is_scored = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.activity}"
    