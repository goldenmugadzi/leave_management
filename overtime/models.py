from django.db import models
from django.conf import settings
from it.users.models import *


class OvertimeEntry(models.Model):
    # Sheet-level fields
    month = models.CharField(max_length=64, blank=True)
    period_from = models.DateField()
    period_to = models.DateField()
    district_station = models.CharField(max_length=255, verbose_name="District/Station")
    designation = models.ForeignKey(Designations, null=True, blank=True,  on_delete=models.SET_NULL)
    ec_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL)
    nature_of_work = models.CharField(max_length=255, blank=True)
    time_out = models.TimeField()
    time_in = models.TimeField()
    hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    job_vote_number = models.CharField(max_length=100, blank=True)

   
