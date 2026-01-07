from django.db import models
import random
import time
from it.users.models import UserProfile,Depots,CostCenter

class DepotToolsAndEquipmentRegister(models.Model):
   depot = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, related_name='depot_tools_and_equipment_registers')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='depot_tes_created')
   approved_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='depot_tes_approved')   

   def __str__(self):
      return f"Depot Register {self.depot} - {self.created_at}"

class ToolOrEquipment(models.Model):
      depot_register = models.ForeignKey(DepotToolsAndEquipmentRegister, on_delete=models.CASCADE, related_name='tools_and_equipments')
      name = models.CharField(help_text="Name of the tool or equipment", max_length=100)
      total_quantity = models.PositiveIntegerField(null=True, blank=True)
      so_or_invoice_no = models.CharField(max_length=50, blank=True, null=True)
      so_or_invoice_date = models.DateField(blank=True, null=True)
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
      return f"Tools & Equipment Form #{self.id} - {self.artisan.get_full_name()}" 
  
   def save(self, *args, **kwargs):
      if not self.id:
         date_str = time.strftime("%Y%m%d")
         random_number = str(random.randint(1000, 9999))
         self.id = f"TEF{date_str}{random_number}"
      super().save(*args, **kwargs)

class AssignedToolOrEquipment(models.Model):
    form = models.ForeignKey(ToolsAndEquipmentRegister, on_delete=models.CASCADE, related_name='assigned_tools')
    tool_or_equipment = models.ForeignKey(ToolOrEquipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    so_or_invoice_no = models.CharField(max_length=50, blank=True, null=True)
    so_or_invoice_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.tool_or_equipment.name} ({self.quantity})"
class Comment(models.Model):
    assigned_tool_or_equipment = models.ForeignKey(AssignedToolOrEquipment, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    author = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment on {self.assigned_tool_or_equipment.tool_or_equipment.name} at {self.created_at}"
