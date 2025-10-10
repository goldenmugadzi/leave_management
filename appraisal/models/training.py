from helpers.models import TimeStamp
from django.db import models
from it.users.models import Designations
from .departmental_workplan import DepartmentOutputCompetency
from .appraisal import Appraisal
from .helpers import YearQuarter
from loguru import logger

INTERVENTION_CATEGORY_CHOICES = [
    ("TRAINING", "TRAINING"),
    ("COUNSELLING", "COUNSELLING"),
    ("TRANSFER", "TRANSFER"),
]

class Competency(TimeStamp):
    name = models.CharField(max_length=500, blank=False, null=False)
        
    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name_plural = "Competencies"
    
    
class JobCompetency(TimeStamp):
    designation = models.ForeignKey(Designations, on_delete=models.CASCADE)
    required_competency = models.CharField(max_length=255, null=True, default=None)
    
    def __str__(self):
        return f"{self.required_competency}"
    
    class Meta:
        verbose_name_plural = "JobCompetencies"
        
class InterventionStrategy(TimeStamp):
    description = models.CharField(max_length=500, blank=False, null=False)
    category = models.CharField(max_length=20, choices=INTERVENTION_CATEGORY_CHOICES, blank=False, null=False)
    
    def __str__(self):
        return f"{self.category}"
    
    class Meta:
        verbose_name_plural = "InterventionStrategies"
    
     
class TrainingAndDevelopment(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE)
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT, null=True, blank=True)
    existence_competencies = models.ManyToManyField(JobCompetency, related_name="required_competencies")
    intervention_strategies = models.ManyToManyField(InterventionStrategy)
    action_recommended = models.TextField(null=True, blank=True)
    action_taken = models.TextField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.appraisal} - Q{self.quarter}"