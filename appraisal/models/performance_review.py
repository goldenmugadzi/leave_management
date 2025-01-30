from helpers.models import TimeStamp
from django.db import models
from .appraisal import Appraisal
from .helpers import YearQuarter
    
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
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT, null=True, blank=True)
    strengths = models.ManyToManyField(PerformanceProgressStrength)
    areas_of_weaknesses = models.ManyToManyField(PerformanceProgressWeakness)
    
    def __str__(self) -> str:
        return f"{self.appraisal.user} - {self.quarter}"