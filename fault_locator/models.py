from django.db import models
from it.users.models import UserProfile, Depots

class FaultLocatorDevice(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.serial_number

class FaultLocatorTeam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(UserProfile, related_name='fault_locator_teams')

    def __str__(self):
        return self.name

class Fault(models.Model):
    description = models.CharField(max_length=255)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE)
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=[
        ('requested', 'Requested'),
        ('assigned', 'Assigned'),
        ('located', 'Located'),
        ('closed', 'Closed'),
    ], default='requested')

    def __str__(self):
        return f"Fault at {self.depot.depot}: {self.description[:30]}"

class FaultAssignment(models.Model):
    fault = models.ForeignKey(Fault, on_delete=models.CASCADE)
    team = models.ForeignKey(FaultLocatorTeam, on_delete=models.CASCADE)
    device = models.ForeignKey(FaultLocatorDevice, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    located_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.fault} assigned to {self.team} with {self.device}"