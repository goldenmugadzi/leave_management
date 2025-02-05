from django.db import models
from datetime import timezone
from django.db import models
from it.users.models import *

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
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class TD(models.Model):
    name = models.CharField(max_length=80, blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class UPO(models.Model):
    description = models.CharField(max_length=80, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class Inspections(models.Model):
    location = models.CharField(max_length=100, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
        
class Maintenance(models.Model):
    location = models.CharField(max_length=100, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    
class File(models.Model):
    file = models.FileField(upload_to='files/')
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    content = models.TextField(blank=True)

class NetMeteringRegister(models.Model):
    name_of_customer = models.CharField(max_length=255)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    date_applied = models.DateField()
    address = models.CharField(max_length=255)
    date_commissioned = models.DateField(null=True, blank=True)
    progress = models.CharField(max_length=50)
    installed_capacity = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=100)
    inverter_type = models.CharField(max_length=100)
    solar_panel_type = models.CharField(max_length=100)
    customer_category = models.CharField(max_length=50)
    phases = models.CharField(max_length=50)
    email_address = models.EmailField()
    cell_number = models.CharField(max_length=20)
    meter_number = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name_of_customer} - {self.meter_number}"

    class Meta:
        verbose_name = "Net Metering Register"
        verbose_name_plural = "Net Metering Registers"
        
class NetMeteringBilling(models.Model):
    commissioned_points = models.IntegerField()
    billed_points = models.IntegerField()
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DSMAudits(models.Model):
    client = models.CharField(max_length=255)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} - {self.region}"
    
    class Meta:
        verbose_name = "DSM Audit"
        verbose_name_plural = "DSM Audits"
        
class VirtualPowerStats(models.Model):
    dsm_initiative = models.CharField(max_length=255)
    initiative_type = models.CharField(max_length=255)
    initiative_value = models.IntegerField()
    demand_curtailed = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        