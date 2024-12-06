from helpers.models import TimeStamp
from django.db import models
from .appraisal import Appraisal
from .helpers import QuarterChoices
    
class PerformanceProgressStrength(TimeStamp):
    name = models.CharField(max_length=500, null=False, blank=False, unique=True, db_index=False)
    
    
    def __str__(self) -> str:
        return f"{self.id}.  {self.name}"

class PerformanceProgressWeakness(TimeStamp):
    name = models.CharField(max_length=500, null=False, blank=False, unique=True, db_index=False)
    
    def __str__(self) -> str:
        return f"{self.id}.  {self.name}"

class PerformanceProgressReview(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE)
    quarter = models.PositiveIntegerField(choices=QuarterChoices.choices)
    strengths = models.ManyToManyField(PerformanceProgressStrength)
    areas_of_weaknesses = models.ManyToManyField(PerformanceProgressWeakness)
    
    def __str__(self) -> str:
        return f"{self.appraisal.user} - Q{self.quarter}"