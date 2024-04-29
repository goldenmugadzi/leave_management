import random
import time
from django.db import models
from approve.models import Process
from finance.Ace.models import Ace
from it.users.models import UserProfile, Sections, Regions, Districts, Depots
class ProcurementPlanReference(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,blank=True, null=True)
    def __str__(self):
        return f"{self.id} - {self.name}"

class PurchaseRequest(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE,blank=True, null=True)
    # cost_centre = models.ForeignKey(CostCentre, on_delete=models.CASCADE,blank=True, null=True)
    pr_no = models.CharField(max_length=100)
    procurement_plan_reference = models.ForeignKey(ProcurementPlanReference, on_delete=models.CASCADE,blank=True, null=True)
    # payment_mode = models.CharField(max_length=100, choices=[('Cash','Cash'),('Transfare','Transfare'),('Swipe','Swipe'),('Usd Cash','Usd Cash'),('Usd Transfare','Usd Transfare')],default='Transfare')
    requested_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    ace = models.ForeignKey(Ace, on_delete=models.SET_NULL, blank=True, null=True)
    is_processed = models.BooleanField(default=False, editable=False) 
    # process = models.ForeignKey(Process, on_delete=models.SET_NULL, blank=True, null=True)
    scope_of_work = models.TextField(blank=True, null=True, help_text="Description for the purchase request")
    def __str__(self):
        return self.pr_no

    def save(self, *args, **kwargs):
        if not self.id: 
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "PR" + timestamp + random_number
        super().save(*args, **kwargs)

class Attachment(models.Model):
    file = models.FileField(upload_to='uploads/purchase_request')
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE,blank=True, null=True)
    
    def __str__(self):
        return self.file.name
    
class CostCentre(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
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
    def __str__(self):
        return self.name

class PrItem(models.Model):
    item_required = models.CharField(max_length=100)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement, on_delete=models.CASCADE,blank=True, null=True)
    quantity = models.IntegerField(default=1)
    purchase_request = models.ForeignKey(PurchaseRequest, models.CASCADE, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.item_required}  {self.quantity} {self.unit_of_measurement}"



# class Quotation(models.Model):
#     id = models.CharField(primary_key=True, max_length=20, editable=False)
#     purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE,blank=True, null=True)
#     file = models.FileField(upload_to='uploads/purchase_request')
#     supplier = models.CharField(max_length=100, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,blank=True, null=True)   
#     vat = models.CharField(max_length=100, choices=[('inc','Inclusive'),('excl','Exclusive')],verbose_name='VAT',default='excl')
#     def __str__(self):
#         return f'{self.purchase_request} - {self.supplier}'
#     def save(self, *args, **kwargs):
#         timestamp = str(int(time.time()))
#         random_number = str(random.randint(10000, 99999))
#         self.id = "QT" + timestamp + random_number
#         super().save(*args, **kwargs)

# class QuoteItem(models.Model):
#     pr_item = models.ForeignKey(PrItem, models.CASCADE, blank=True, null=True)
#     quantity = models.DecimalField(max_digits=40, decimal_places=2)
#     unit_price = models.DecimalField(max_digits=40, decimal_places=2)
#     quotation = models.ForeignKey(Quotation, models.CASCADE, blank=True, null=True)
#     def __str__(self):
#         return str(self.pk)
