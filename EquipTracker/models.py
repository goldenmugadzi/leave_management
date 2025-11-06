from django.db import models
from it.users.models import Sections, Substation, UserProfile, Districts

class Equipment(models.Model):
    EQUIPMENT_CHOICES = [('Transformer', 'Transformer'),('Switchgear', 'Switchgear'),('Condenser', 'Condenser'),('Panel', 'Panel'),('Relay', 'Relay'),('Battery', 'Battery'),('Inverter', 'Inverter'),('Charger', 'Charger'),('Other', 'Other'),]
    type_of_equipment = models.CharField(max_length=100, choices=EQUIPMENT_CHOICES)
    created_at = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type_of_equipment} ({self.id})"


class EquipmentChange(models.Model):
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    substation = models.ForeignKey(Substation, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"Change {self.id} in {self.district}"

class EquipmentParticulars(models.Model):
    equipment_change = models.ForeignKey(EquipmentChange, on_delete=models.CASCADE, related_name='particulars', blank=True, null=True)
    make = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    kva_or_ampere_rating = models.CharField(max_length=100, blank=True, null=True)
    voltage_rating = models.CharField(max_length=100, blank=True, null=True)

    ACTION_CHOICES = [
        ('Installation', 'Installation'),
        ('Removal', 'Removal'),
    ]
    
    action_taken = models.CharField(max_length=100, choices=ACTION_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.make} ({self.serial_number})"