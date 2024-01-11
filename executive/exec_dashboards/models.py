from django.db import models
from datetime import timezone
from django.db import models

# Create your models here.
class PBNC(models.Model):
    name = models.CharField(max_length=80, blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
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
