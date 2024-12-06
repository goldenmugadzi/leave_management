from helpers.models import TimeStamp
from django.db import models
from it.users.models import Designations
from .appraisal import Appraisal
from .helpers import QuarterChoices

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
    competencies = models.ManyToManyField(Competency, related_name="competencies")
    
    def __str__(self):
        return f"{self.designation.description}"
    
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
    quarter = models.PositiveIntegerField(choices=QuarterChoices.choices)
    required_competencies = models.ManyToManyField(Competency, related_name="required_competencies")
    competency_gaps = models.ManyToManyField(Competency, related_name="competency_gaps")
    intervention_strategies = models.ManyToManyField(InterventionStrategy)
    action_recommended = models.TextField(null=True, blank=True)
    action_taken = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.appraisal} - Q{self.quarter}"
