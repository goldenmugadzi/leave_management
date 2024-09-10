from django.db import models
from django.db.models import fields
import random
import time
from approve.models import Process
from it.users.models import *


# Create your models here.

class Pettycash(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('USD Cash', 'USD Cash'),
        ('USD Swipe', 'USD Swipe'),
        ('ZIG Cash', 'ZIG Cash'),
        ('ZIG Transfer', 'ZIG Transfer'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('ZIG', 'ZIG'),
        ('ZWL', 'ZWL'),
    ]

    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    payment_mode = models.CharField(max_length=100, blank=True, null=True, choices=PAYMENT_MODE_CHOICES)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True, null=True, db_index=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True, db_index=True)
    petty_id = models.CharField(max_length=60, db_index=True)
    pettycash_id = models.AutoField(primary_key=True)
    process = models.ForeignKey(Process, on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    old_version = models.BooleanField(default=False, db_index=True)
    currency = models.CharField(max_length=100, blank=True, null=True, choices=CURRENCY_CHOICES)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    amount_disbursed = models.FloatField(blank=True, null=True)
    receipt_file = models.FileField(upload_to='uploads/pettycash', blank=True, null=True)
    amount_used = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.petty_id


class Quotation(models.Model):
    pettycash = models.ForeignKey(Pettycash, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/pettycash')

    def __str__(self):
        return str(self.pk)

class PettycashReport(models.Model):
    report_id = models.AutoField(primary_key=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return str(self.report_id)
