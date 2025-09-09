from django.db import models
from it.users.models import Sections
from BatteryMaintenance.models import Substation

class EquipmentRecord(models.Model):
    district = models.CharField(max_length=100)
    substation = models.ForeignKey(Substation, on_delete=models.CASCADE)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    action_taken = models.CharField(max_length=100,choices=[('Insalation', 'Installation'), ('Removal', 'Removal'), ('Change', 'Change')])
    type_of_equipment = models.CharField(max_length=100, choices=[('Transformer', 'Transformer'), ('Switchgear','Switchgear'), ('Condenser','Condenser'),('Panel','Panel'),('Relay','Relay'),('Battery','Battery'),('Inverter','Inverter'),('Charger','Charger'),('Other','Other')])
    make = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    kva_or_ampere_rating_installed = models.CharField(max_length=50, blank=True, null=True)
    kva_or_ampere_rating_removed = models.CharField(max_length=50, blank=True, null=True)
    voltage_rating_installed = models.CharField(max_length=50, blank=True, null=True)
    voltage_rating_removed = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    vote_job_no = models.CharField(max_length=100, blank=True, null=True)
    signed_by = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    signed_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.substation_name} - {self.equipment_installed} ({self.date_of_installation})"
