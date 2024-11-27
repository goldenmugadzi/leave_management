from helpers.models import TimeStamp
from django.db import models
from .appraisal import Appraisal

class QuarterChoices(models.IntegerChoices):
    Q1 = 1, "1st"
    Q2 = 2, "2nd"
    Q3 = 3, "3rd"
    Q4 = 4, "4th"
    
class PerformanceProgressStrength(TimeStamp):
    name = models.CharField(max_length=500, null=False, blank=False, unique=True, db_index=False)
    
    
    def __str__(self) -> str:
        return f"Strength-{self.id}"

class PerformanceProgressWeakness(TimeStamp):
    name = models.CharField(max_length=500, null=False, blank=False, unique=True, db_index=False)
    
    def __str__(self) -> str:
        return f"Weakness-{self.id}"

class PerformanceProgressReview(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE)
    quarter = models.PositiveIntegerField(choices=QuarterChoices.choices)
    strength = models.ManyToManyField(PerformanceProgressStrength)
    areas_of_weakness = models.ManyToManyField(PerformanceProgressWeakness)
    
    def __str__(self) -> str:
        return f"{self.appraisal.user} - {self.quarter}"