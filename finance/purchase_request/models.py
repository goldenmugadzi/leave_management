import random
import time
from django.db import models
from django.core.exceptions import ValidationError
from finance.Ace.models import Ace
from it.users.models import CostCenter, UserProfile, Sections, Regions, Districts, Depots

class ProcurementPlanReference(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,blank=True, null=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return f"{self.name} - [{self.id}]"

def validate_pr_no(value):
    if not value.isdigit():
        if value.startswith("PR"):
            value = value[2:]
        else:
            raise ValidationError("PR Number must have exactly 8 digits")
    if len(value) != 8:
        raise ValidationError("PR Number must be exactly 8 digits")
    return "PR" + value
class PurchaseRequest(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    pr_no = models.CharField( max_length=10, verbose_name="PR Number", validators=[validate_pr_no])
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, blank=True, null=True)
    procurement_plan_reference = models.ForeignKey(ProcurementPlanReference, on_delete=models.CASCADE, blank=True, null=True)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    ace = models.ForeignKey(Ace, on_delete=models.SET_NULL, blank=True, null=True)
    scope_of_work = models.TextField(blank=True, null=True, help_text="Description for the purchase request")
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.id
   
    def save(self, *args, **kwargs):
        if not self.id and not self.pk:
            self.id = "PR" + str(self.pr_no)
        super().save(*args, **kwargs)

class Attachment(models.Model):
    file = models.FileField(upload_to='uploads/purchase_request')
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE,blank=True, null=True)
    
    def __str__(self):
        return self.file.name
    
class CostCentre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "CC" + timestamp + random_number
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        app_label = 'users'
class UnitOfMeasurement(models.Model):
    unit = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,blank=True, null=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

class PrItem(models.Model):
    item_required = models.CharField(max_length=100)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    purchase_request = models.ForeignKey(PurchaseRequest, models.CASCADE, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.item_required}  {self.quantity} {self.unit_of_measurement}"
