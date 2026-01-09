from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date, datetime
from django.contrib.auth.models import User
from django.conf import settings
from it.users.models import *


class TransportAssets(models.Model):
    depot = models.ForeignKey(Depots,on_delete=models.DO_NOTHING, blank=True, null=True)
    stf = models.CharField(max_length=300)
    fleet_number = models.CharField(max_length=300)
    reg_number = models.CharField(max_length=400)
    opening_speedo_reading = models.PositiveIntegerField(default=0)
    driver = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,)
    closing_speedo_reading = models.PositiveIntegerField(default=0)
    make = models.CharField(max_length=500)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    trip_distance = models.PositiveIntegerField(default=0)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    fuel_drawn = models.PositiveIntegerField(default=0)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    fuel_type = models.CharField(max_length=100, help_text="Type", choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel')])
    year = models.CharField(max_length=200)
    details_of_journey = models.TextField(max_length=800)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    model = models.CharField(max_length=500)
    oil_drawn = models.PositiveIntegerField(default=0)
    date = models.DateField(default=datetime.today)
    place_drawn = models.CharField(max_length=100, help_text="Location", choices=[('Chitungwiza', 'Chitungwiza'), ('Transport Yard', 'Transport Yard'),('Coupon', 'Coupon'),('Other', 'Other')])
    defects_and_repairs_carried_out= models.TextField(max_length=800)
    average_consumption = models.PositiveIntegerField(default=0)
    total_fuel = models.PositiveIntegerField(default=0)
    total_km = models.PositiveIntegerField(default=0)
    total_oil = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Calculate trip_distance before saving
        if self.closing_speedo_reading is not None and self.opening_speedo_reading is not None:
            self.trip_distance = max(0, self.closing_speedo_reading - self.opening_speedo_reading)
        # Calculate average_consumption before saving
        if self.fuel_drawn and self.fuel_drawn > 0:
            self.average_consumption = self.trip_distance / self.fuel_drawn
        else:
            self.average_consumption = 0
        super().save(*args, **kwargs)

class Vehicle(models.Model):
    reg_number = models.CharField(max_length=400)
    fleet_number = models.CharField(max_length=300)
    make = models.CharField(max_length=500)
    model = models.CharField(max_length=500)
    year = models.CharField(max_length=200)
    fuel_drawn = models.PositiveIntegerField(default=0)
    oil_drawn = models.PositiveIntegerField(default=0)
    fuel_type = models.CharField(
        max_length=100,
        help_text="Type",
        choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel')]
    )


    def __str__(self):
        return f"{self.model} - {self.reg_number}"

class TripRecord(models.Model):
    vehicle_details = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='trips',
        verbose_name="fleet_Number/Make/Reg_Number"
    )
    date = models.DateTimeField()
    depot = models.ForeignKey(
        Depots,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name="Depot/Center"
    )
    drivers_name = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    opening_speedo_reading = models.PositiveIntegerField(default=0)
    closing_speedo_reading = models.PositiveIntegerField(default=0)
    stf_number= models.CharField(max_length=500)
    allocation_code= models.CharField(max_length=500)
    trip_distance = models.PositiveIntegerField(default=0)
    trip_reference = models.CharField(max_length=50, unique=True, blank=True, null=True)

    # ✅ rename for display
    region = models.ForeignKey(
        Regions,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name="Dept/Region"
    )
    # ✅ rename for display
    department = models.ForeignKey(
        Sections,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name="District/Section"
    )

    # ✅ rename for display
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Depot/Center"
    )
    fuel_drawn = models.PositiveIntegerField(default=0)
    place_drawn = models.CharField(
        max_length=100,
        help_text="Location",
        choices=[
            ('Chitungwiza', 'Chitungwiza'),
            ('Transport Yard', 'Transport Yard'),
            ('Coupon', 'Coupon'),
            ('Other', 'Other')
        ]
    )
    oil_drawn = models.PositiveIntegerField(default=0)
    details_of_journey = models.TextField(max_length=800, verbose_name="Details of journey (local) is not accepted")
    defects_and_repairs_carried_out = models.TextField(max_length=800)
    average_consumption = models.FloatField(default=0)
    total_fuel = models.PositiveIntegerField(default=0)
    total_km = models.PositiveIntegerField(default=0)
    total_oil = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Calculate trip_distance before saving
        if self.closing_speedo_reading is not None and self.opening_speedo_reading is not None:
            self.trip_distance = max(0, self.closing_speedo_reading - self.opening_speedo_reading)
        # Calculate average_consumption before saving
        if hasattr(self, "fuel_drawn") and self.fuel_drawn and self.fuel_drawn > 0:
            self.average_consumption = self.trip_distance / self.fuel_drawn
        else:
            self.average_consumption = 0
        super().save(*args, **kwargs)
        # Auto-generate trip_reference if not set
        if not self.trip_reference:
            date_part = self.date.strftime('%Y%m%d') if self.date else datetime.now().strftime('%Y%m%d')
            self.trip_reference = f"TRIP-{date_part}-{self.pk}"
            super().save(update_fields=['trip_reference'])

    def __str__(self):
        return f"Trip on {self.date} for {self.vehicle_details}"
class Tyres(models.Model):
    quantity = models.CharField(max_length=400)
    name= models.CharField(max_length=300)
    size = models.PositiveIntegerField(default=0)
    date_fitted = models.DateField(default=datetime.today)

    def __str__(self):
        return f"{self.model} - {self.name}"
    
class Battery(models.Model):
    name= models.CharField(max_length=300)
    number = models.PositiveIntegerField(default=0)
    date_fitted = models.DateField(default=datetime.today)

    def __str__(self):
        return f"{self.model} - {self.name}"

class Allocation(models.Model):
    kms= models.CharField(max_length=300)
    job_number = models.PositiveIntegerField(default=0)
    amount =  models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.model} - {self.amount}"
