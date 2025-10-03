from django.db import models
from it.users.models import Sections,Substation ,UserProfile

class TrackEquipment(models.Model):
    type_of_equipment = models.CharField(max_length=100, choices=[('Transformer', 'Transformer'), ('Switchgear','Switchgear'), ('Condenser','Condenser'),('Panel','Panel'),('Relay','Relay'),('Battery','Battery'),('Inverter','Inverter'),('Charger','Charger'),('Other','Other')])
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    def __str__(self):
        return f"{self.type_of_equipment} ({self.id})"
    
class EquipmentChange(models.Model):
    district = models.CharField(max_length=100)
    substation = models.ForeignKey(Substation, on_delete=models.CASCADE)
    equipment = models.ForeignKey(TrackEquipment, on_delete=models.CASCADE)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE, blank=True, null=True)
    action_taken = models.CharField(max_length=100,choices=[('Insalation', 'Installation'), ('Removal', 'Removal'), ('Change', 'Change')])
    date = models.DateField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return f" {self.id}"

class ParticularsRequired(models.Model):
    make = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    kva_or_ampere_rating = models.CharField(max_length=100)
    voltage_rating = models.CharField(max_length=100)
    def __str__(self):
        return f" {self.id}"
   
class EquipmentInstalled(models.Model):
    equipmentchange = models.ForeignKey(EquipmentChange, on_delete=models.CASCADE)
    particulars = models.ForeignKey(ParticularsRequired, on_delete=models.CASCADE)
    def __str__(self):
        return f" {self.id}"

class EquipmentRemoved(models.Model):
    equipmentchange = models.ForeignKey(EquipmentChange, on_delete=models.CASCADE)
    particulars = models.ForeignKey(ParticularsRequired, on_delete=models.CASCADE)
    def __str__(self):
        return f" {self.id}"

    



def addEquipment(equipment_type):
    return TrackEquipment.objects.create(type_of_equipment=equipment_type)

def addEquipmentChange(
    district, substation, equipment_tracker, section, action_taken, date, reason=None, created_by=None,
    installed=None, removed=None
):
    # installed/removed: dicts with keys make, serial_number, kva_or_ampere_rating, voltage_rating
    equipment_change = EquipmentChange.objects.create(
        district=district,
        substation=substation,
        equipment_tracker=equipment_tracker,
        section=section,
        action_taken=action_taken,
        date=date,
        reason=reason,
        created_by=created_by
    )

    if installed:
        inst_part = ParticularsRequired.objects.create(**installed)
        EquipmentInstalled.objects.create(equipmentchange=equipment_change, particulars=inst_part)

    if removed:
        rem_part = ParticularsRequired.objects.create(**removed)
        EquipmentRemoved.objects.create(equipmentchange=equipment_change, particulars=rem_part)

    return equipment_change