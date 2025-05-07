from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from it.users.models import *
from decimal import Decimal


class ProductType(models.Model):
    product_type = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.product_type} - {self.model}"


class ZetdcAssets(models.Model):
    product_type = models.ForeignKey(ProductType, on_delete=models.DO_NOTHING, blank=True, null=True)
    serial_number = models.CharField(max_length=100,unique=True,blank=True, null=True)
    asset_number = models.CharField(max_length=100,unique=True,blank=True, null=True)
    asset_state = models.CharField(max_length=100,blank=True, null=True,help_text="Asset state",  choices=[('Warrant', 'Warrant') , ('Obsolute state', 'Obsolute state'),('Awaiting New Spares', 'Awaiting New Spares'), ('Awaiting New User', 'Awaiting New User'),('Functioning', 'Functioning'),('Non Functioning', 'Non Functioning')])
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="user")
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING , blank=True, null=True)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_purchased =models.DateField()
    model = models.CharField(max_length=100,help_text="Asset Model",  choices=[('laptop', 'laptop') , ('desktop', 'desktop'),('printer', 'pinter'), ('router', 'router'),('switch', 'switch')])
    warrant = models.CharField(max_length=100, default='Unknown',blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="creat")
    created_at = models.DateField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateField(auto_now=True)
    supplier = models.CharField(max_length=100, default='Unknown',blank=True, null=True)

