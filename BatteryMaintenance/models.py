from django.db import models
from it.users.models import CostCenter


class BatteryInstallation(models.Model):
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING)
    site_name = models.CharField(max_length=100)
    battery_name = models.CharField(max_length=100)
    cell_type = models.CharField(max_length=50, blank=True)
    cell_quantity = models.PositiveIntegerField()
    plates_per_cell = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    battery_application = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.battery_name} ({self.id})"


class Cell(models.Model):
    installation = models.ForeignKey(BatteryInstallation, on_delete=models.CASCADE, related_name='cells')
    specific_gravity = models.FloatField(null=True, blank=True)
    voltage = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Cell {self.id} (Installation {self.installation})"


class BatteryMaintenance(models.Model):  # ✅ Fixed typo
    battery = models.OneToOneField(BatteryInstallation, on_delete=models.CASCADE)
    volts_high = models.FloatField(null=True, blank=True)
    volts_low = models.FloatField(null=True, blank=True)
    volts_avg = models.FloatField(null=True, blank=True)
    sg_high = models.FloatField(null=True, blank=True)
    sg_low = models.FloatField(null=True, blank=True)
    sg_avg = models.FloatField(null=True, blank=True)
    reading_type = models.CharField(
        max_length=10,
        choices=[("daily", "Daily"), ("monthly", "Monthly")],
        default="monthly"
    )
    water_used = models.FloatField(null=True, blank=True)  # ✅ Made nullable
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance for {self.battery}"


class CellReading(models.Model):
    battery_maintenance = models.ForeignKey(BatteryMaintenance, on_delete=models.CASCADE)
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE)
    specific_gravity = models.FloatField(null=True, blank=True)
    voltage = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Reading for Cell {self.cell.id} (Install {self.cell.installation_id})"


class PilotReading(models.Model):
    installation = models.ForeignKey(BatteryInstallation, on_delete=models.CASCADE, related_name='daily_pilot_readings')
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    battery_voltage = models.FloatField(null=True, blank=True)
    specific_gravity = models.FloatField(null=True, blank=True)
    acid_temp = models.FloatField(null=True, blank=True)
    charge_rate = models.FloatField(null=True, blank=True)
    cell_voltage = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Pilot Cell {self.cell.id} on {self.date}"


class EmergencyDischarge(models.Model):
    installation = models.ForeignKey(BatteryInstallation, on_delete=models.CASCADE, related_name='emergency_discharges')
    date = models.DateField(auto_now_add=True)
    amps = models.FloatField()
    for_duration = models.FloatField(help_text="hours")

    def __str__(self):
        return f"Discharge on {self.date}"