from django.db import models
from datetime import timezone
from django.db import models

# Create your models here.
class PBNC(models.Model):
    reciept_no = models.CharField(max_length=150, blank=True, null=True)
    ics_ref = models.CharField(max_length=150, blank=True, null=True)
    ndm_ref = models.CharField(max_length=150, blank=True, null=True)
    name = models.CharField(max_length=80, blank=True, null=True)
    address = models.CharField(max_length=150, blank=True, null=True)
    capacity = models.CharField(max_length=100, blank=True, null=True)
    project_type = models.CharField(max_length=50, blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class TD(models.Model):
    name = models.CharField(max_length=80, blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class UPO(models.Model):
    description = models.CharField(max_length=80, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class Inspections(models.Model):
    location = models.CharField(max_length=100, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
        
class Maintenance(models.Model):
    location = models.CharField(max_length=100, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
