from django.db import models
from it.users.models import UserProfile

class Depot(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class FaultLocatorDevice(models.Model):
    serial_number = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.serial_number} - {self.description}"

class DeviceAssignment(models.Model):
    device = models.ForeignKey(FaultLocatorDevice, on_delete=models.CASCADE)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.device} assigned to {self.depot} at {self.assigned_at}"

    @property
    def usage_duration(self):
        from django.utils import timezone
        end_time = self.returned_at or timezone.now()
        return end_time - self.assigned_at

class FaultLocatorTeam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(UserProfile, related_name='fault_locator_teams')

    def __str__(self):
        return self.name

class Fault(models.Model):
    description = models.CharField(max_length=255)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE)
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=[
        ('requested', 'Requested'),
        ('assigned', 'Assigned'),
        ('located', 'Located'),
        ('closed', 'Closed'),
    ], default='requested')

    def __str__(self):
        return f"Fault at {self.depot.name}: {self.description[:30]}"

class FaultAssignment(models.Model):
    fault = models.ForeignKey(Fault, on_delete=models.CASCADE)
    team = models.ForeignKey(FaultLocatorTeam, on_delete=models.CASCADE)
    device = models.ForeignKey(FaultLocatorDevice, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    located_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.fault} assigned to {self.team}"