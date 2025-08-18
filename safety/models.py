from django.db import models
import random
import time
from it.users.models import UserProfile, CostCenter

class ControllersInstructionForm(models.Model):
   id = models.CharField(primary_key=True, max_length=20, editable=False)
   district_station = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
   issued_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='issued_instructions')
   received_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='received_instructions')
   issued_at = models.DateTimeField(auto_now_add=True)

   class Meta:
      verbose_name = "Controller's Instruction Form"
      verbose_name_plural = "Controller's Instruction Forms"

   def __str__(self):
      return f"Instruction Form #{self.id} - {self.district_station}"
   def save(self, *args, **kwargs):
      if not self.id:
         # Format: SAF + YYYYMMDD + 4 random digits, e.g. SAF202504234343
         date_str = time.strftime("%Y%m%d")
         random_number = str(random.randint(1000, 9999))
         self.id = f"SAF{date_str}{random_number}"
      super().save(*args, **kwargs)


class Instruction(models.Model):
    form = models.ForeignKey(ControllersInstructionForm, on_delete=models.CASCADE, related_name='entries')
    instruction = models.CharField(help_text="Instruction issued",max_length=500)
    received= models.TimeField(help_text="Time when the instruction was received", null=True, blank=True)
    completed = models.TimeField(help_text="Time when the instruction was completed", null=True, blank=True)

    def __str__(self):
         return  self.instruction[:50]