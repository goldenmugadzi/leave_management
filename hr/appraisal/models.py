from django.db import models
from django.db.models import Model

from it.users.models import UserProfile, Sections, Designations, Regions


# Create your models here.
class Appraisal(models.Model):
    choices = [
        ('grade_b', 'grade_b'),
        ('grade_c+', 'grade_c+'),
    ]
    appraisal_id = models.AutoField(primary_key=True)
    employee_id = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    appraisal_date = models.DateField(blank=True, null=True)
    period = models.CharField(max_length=100, blank=True, null=True)
    appraisal_type = models.CharField(max_length=100, blank=True, null=True, choices=choices)
    appraisal_form = models.FileField(upload_to='uploads/appraisal')
    created_date = models.DateField(blank=True, null=True)
    date_of_appointment_into_service = models.DateField(blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    appraiser = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return str(self.appraisal_id)


class AppraisalEvaluation(models.Model):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.DO_NOTHING, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    weighted_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.appraisal)


class key_result_areas(models.Model):
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    kras = models.TextField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.kras)


class activity(models.Model):
    kras = models.ForeignKey(key_result_areas, on_delete=models.DO_NOTHING, blank=True, null=True)
    activity = models.TextField(max_length=1000, blank=True, null=True)
    quantity_description = models.TextField(max_length=1000, blank=True, null=True)
    quality_description = models.TextField(max_length=1000, blank=True, null=True)
    time_description = models.TextField(max_length=1000, blank=True, null=True)
    cost_description = models.TextField(max_length=1000, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    agreed_target = models.FloatField(blank=True, null=True)
    standard = models.TextField(max_length=1000, blank=True, null=True)
    actual_performance = models.FloatField(blank=True, null=True)
    allowable_variance = models.FloatField(blank=True, null=True)
    actual_variance = models.FloatField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    weighted_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.activity)


class standard_dimensions(models.Model):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.DO_NOTHING, blank=True, null=True)
    strengths = models.TextField(max_length=1000, blank=True, null=True)
    areas_of_improvement = models.TextField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.appraisal)


class AppraisalValidation(models.Model):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.DO_NOTHING, blank=True, null=True)
    strenths = models.TextField(max_length=1000, blank=True, null=True)
    areas_of_improvement = models.TextField(max_length=1000, blank=True, null=True)
    competencies = models.TextField(max_length=1000, blank=True, null=True)
    existing_competencies = models.TextField(max_length=1000, blank=True, null=True)
    competency_gaps = models.TextField(max_length=1000, blank=True, null=True)
    intervention_strategies = models.TextField(max_length=1000, blank=True, null=True)
    intervention = models.TextField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.appraisal)
