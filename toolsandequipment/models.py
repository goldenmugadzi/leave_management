from django.db import models
import random
import time
from it.users.models import UserProfile, CostCenter

class ToolOrEquipment(models.Model):
      cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='te_toolsandequipment')
      name = models.CharField(help_text="Name of the tool or equipment", max_length=100)
      quantity = models.PositiveIntegerField(help_text="Quantity issued")
      value = models.DecimalField(help_text="Value of the tool or equipment", max_digits=10, decimal_places=2, null=True, blank=True)
      asset_number = models.CharField(help_text="Asset number of the tool or equipment", max_length=50, null=True, blank=True)
   
      def __str__(self):
         return f"{self.name} ({self.quantity})"
      
class ToolsAndEquipmentForm(models.Model):
   id = models.CharField(primary_key=True, max_length=20, editable=False)
   artisan = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='te_forms_toolsandequipment')
   issued_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='te_issued_tools_toolsandequipment')
   issued_at = models.DateTimeField(auto_now_add=True)

   class Meta:
      verbose_name = "Tools and Equipment Form"
      verbose_name_plural = "Tools and Equipment Forms"

   def __str__(self):
      return f"Tools & Equipment Form #{self.id} - {self.artisan.get_full_name()}"
  
   def save(self, *args, **kwargs):
      if not self.id:
         date_str = time.strftime("%Y%m%d")
         random_number = str(random.randint(1000, 9999))
         self.id = f"TEF{date_str}{random_number}"
      super().save(*args, **kwargs)

class AssignedToolOrEquipment(models.Model):
    form = models.ForeignKey(ToolsAndEquipmentForm, on_delete=models.CASCADE, related_name='assigned_tools')
    tool_or_equipment = models.ForeignKey(ToolOrEquipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(help_text="Quantity assigned")
    remarks = models.CharField(help_text="Name of the tool or equipment", max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "Assigned Tool or Equipment"
        verbose_name_plural = "Assigned Tools or Equipment"

    def __str__(self):
        return f"{self.tool_or_equipment.name} ({self.quantity})"
