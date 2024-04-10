from django.db import models
from django.db.models import fields
from users.models import User
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

    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    payment_mode = models.CharField(max_length=100, blank=True, null=True, choices=PAYMENT_MODE_CHOICES)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    petty_id = models.CharField(max_length=60)
    pettycash_id = models.AutoField(primary_key=True)
    process = models.OneToOneField(Process, on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.petty_id:  # Generate rfq_id only if it doesn't exist
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "PC" + timestamp + random_number
        super().save(*args, **kwargs)

    def __str__(self):
        return self.petty_id


class Quotation(models.Model):
    pettycash = models.ForeignKey(Pettycash, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/pettycash')

    def __str__(self):
        return str(self.pk)
