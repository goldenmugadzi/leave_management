from django.db import models
from it.users.models import UserProfile

class MeterType(models.Model):
    type_name = models.CharField(max_length=20)

    def __str__(self):
        return self.type_name

class Meter(models.Model):
    meter_number = models.CharField(max_length=11,primary_key=True)
    meter_type = models.ForeignKey(MeterType, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.meter_number)

class Customer(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class TemperToken(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return str(self.meter.meter_number)

class Fault(models.Model):
    temper_token = models.ForeignKey(TemperToken, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return f"Fault: {self.temper_token}"

class Reconnection(models.Model):
    temper_token = models.ForeignKey(TemperToken, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return f"Reconnection: {self.temper_token}"

class Recover(models.Model):
    temper_token = models.ForeignKey(TemperToken, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return f"Recovered: {self.temper_token}"