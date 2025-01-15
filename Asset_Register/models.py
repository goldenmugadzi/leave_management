from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here
class Designations(models.Model):
    identifier = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)
    chk = models.CharField(max_length=100, blank=True)

class Regions(models.Model):
    region = models.CharField(max_length=100)
    code = models.CharField(max_length=100, blank=True)

class Sections(models.Model):
    section = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district_id = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

class ProductType(models.Model):
    product_type = models.CharField(max_length=100)
    code = models.CharField(max_length=100)


class ZetdcAssets(models.Model):
    product_type = models.ForeignKey(ProductType, on_delete=models.DO_NOTHING, blank=True, null=True)
    asset_state = models.CharField(max_length=100,blank=True, null=True)
    serial_number = models.CharField(max_length=100)
    asset_number = models.CharField(max_length=100)
    department = models.CharField(max_length=400)
    user_name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    purchase_cost = models.CharField(max_length=100)
    designations = models.ForeignKey(Designations, on_delete=models.DO_NOTHING , blank=True, null=True)
    sections = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_purchased =models.DateField()
    warrant = models.CharField(max_length=100,blank=True, null=True)
    model = models.CharField(max_length=100,blank=True, null=True)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)

