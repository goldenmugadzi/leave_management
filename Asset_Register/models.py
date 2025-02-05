from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from it.users.models import *


class ProductType(models.Model):
    product_type = models.CharField(max_length=100)
    model = models.CharField(max_length=100)


class ZetdcAssets(models.Model):
    product_type = models.ForeignKey(ProductType, on_delete=models.DO_NOTHING, blank=True, null=True)
    asset_state = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    asset_number = models.CharField(max_length=100)
    department = models.CharField(max_length=400)
    user_name = models.CharField(max_length=100)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    purchase_cost = models.CharField(max_length=100)
    designations = models.ForeignKey(Designations, on_delete=models.DO_NOTHING , blank=True, null=True)
    sections = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_purchased =models.DateField()
    model = models.CharField(max_length=100)
    warrant = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)

