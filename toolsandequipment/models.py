from django.db import models
import random
import time
from it.users.models import UserProfile,Depots

class ToolOrEquipment(models.Model):
      name = models.CharField(help_text="Name of the tool or equipment", max_length=100)
      total_quantity = models.PositiveIntegerField(null=True, blank=True)
      value = models.DecimalField(help_text="Value of the tool or equipment", max_digits=10, decimal_places=2, null=True, blank=True)
      asset_number = models.CharField(help_text="Asset number of the tool or equipment", max_length=50, null=True, blank=True)
   
      def __str__(self):
         return f"{self.name}"
    
class ToolsAndEquipmentRegister(models.Model):
   artisan = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='registers')
   undertaking = models.ForeignKey(Depots, on_delete=models.SET_NULL, null=True, related_name='deopt_registers')
   issued_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='tes_issued')
   certified_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='tes_certified')
   date_issued = models.DateTimeField(auto_now_add=True)
   certified_date = models.DateField(blank=True, null=True)

   def __str__(self):
      return f"Register {self.name} - {self.date_issued}"

class ToolsAndEquipmentRegisterItem(models.Model):
    register = models.ForeignKey(ToolsAndEquipmentRegister, on_delete=models.CASCADE, related_name='items')
    tool_or_equipment = models.ForeignKey(ToolOrEquipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    so_or_invoice_no = models.CharField(max_length=50, blank=True, null=True)
    so_or_invoice_date = models.DateField(blank=True, null=True)
    initials = models.CharField(max_length=10, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.id} "

class Remarks(models.Model):
   register = models.ForeignKey(ToolsAndEquipmentRegister, on_delete=models.CASCADE, related_name='remarks')
   comment = models.TextField()
   author = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
   created_at = models.DateTimeField(auto_now_add=True)
 
   def __str__(self):
      return f"{self.id} "