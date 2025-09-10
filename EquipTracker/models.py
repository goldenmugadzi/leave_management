from django.db import models
from it.users.models import Sections
from it.users.models import Substation

class TrackEquipment(models.Model):
    type_of_equipment = models.CharField(max_length=100, choices=[('Transformer', 'Transformer'), ('Switchgear','Switchgear'), ('Condenser','Condenser'),('Panel','Panel'),('Relay','Relay'),('Battery','Battery'),('Inverter','Inverter'),('Charger','Charger'),('Other','Other')])
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    def __str__(self):
        return f"{self.type_of_equipment} ({self.id})"
    
class EquipmentChange(models.Model):
    district = models.CharField(max_length=100)
    substation = models.ForeignKey(Substation, on_delete=models.CASCADE)
    equipment_tracker = models.ForeignKey(TrackEquipment, on_delete=models.CASCADE)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    action_taken = models.CharField(max_length=100,choices=[('Insalation', 'Installation'), ('Removal', 'Removal'), ('Change', 'Change')])
    date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    signed_by = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return f" {self.id}"

