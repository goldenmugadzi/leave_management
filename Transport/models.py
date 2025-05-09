from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date, datetime
from django.contrib.auth.models import User
from django.conf import settings
from it.users.models import *


class TransportAssets(models.Model):
    jobcardnumber = models.CharField(max_length=300)
    fleet_number = models.CharField(max_length=300)
    reg_number = models.CharField(max_length=400)
    model = models.CharField(max_length=400)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,)
    make = models.CharField(max_length=500)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    engine_number = models.CharField(max_length=400)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    chass_number = models.CharField(max_length=200)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    fuel_type = models.CharField(max_length=100, help_text="Type", choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel')])
    year = models.CharField(max_length=200)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(max_length=100, help_text="Status", choices=[('Active', 'Active'), ('Not Active', 'Not Active')])
    updated_by = models.CharField(max_length=200)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,related_name="creator")

    def save(self, *args, **kwargs):
        if not self.jobcardnumber:
            self.jobcardnumber = "JC" + str(int(datetime.now().timestamp()))
        super(TransportAssets, self).save(*args, **kwargs)

    def __str__(self):
        return self.jobcardnumber



class Fuelcoupons(models.Model):
    Date = models.DateField(default=datetime.now)
    coupon_number=models.CharField(max_length=200)
    litres=models.CharField(max_length=300)
    balance=models.CharField(max_length=300)
    collected_by=models.CharField(max_length=400)
    user_name = models.CharField(max_length=100)

