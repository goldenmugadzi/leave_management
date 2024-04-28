import random
import time
from django.db import models
from approve.models import Process
from finance.Ace.models import Ace
from it.users.models import UserProfile, Sections


class PurchaseRequest(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    description = models.TextField()
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True,help_text='optional')
    scope_of_work = models.CharField(max_length=100, blank=True, null=True,help_text='optional')
    sap_pr_number = models.CharField(max_length=100)
    PAYMENT_MODE_CHOICES = [('USD Cash', 'USD Cash'),('USD Swipe', 'USD Swipe'),('ZIG Cash', 'ZIG Cash'),('ZIG Transfer', 'ZIG Transfer'),]
    payment_mode = models.CharField(max_length=100, blank=True, null=True, choices=PAYMENT_MODE_CHOICES)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    ace = models.ForeignKey(Ace, on_delete=models.SET_NULL, blank=True, null=True)
    process = models.ForeignKey(Process, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        if not self.id: 
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "PR" + timestamp + random_number
        super().save(*args, **kwargs)
class PrItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    UNIT_CHOICES = [('Each','Each'),('KG', 'Kilogram'),('L', 'Liter'),('M', 'Meter'),('CM', 'Centimeter'),('MM', 'Millimeter'),('G', 'Gram'),]
    unit_of_measurement = models.CharField(max_length=100, choices=UNIT_CHOICES)
    quantity = models.DecimalField(max_digits=40, decimal_places=2)
    purchase_request = models.ForeignKey(PurchaseRequest, models.CASCADE, blank=True, null=True)
    ordered = models.DecimalField(max_digits=40, decimal_places=2,default=0)
    used= models.BooleanField(blank=True, null=True, default=False)
    def __str__(self):
        return f"{self.name}    {self.quantity} {self.unit_of_measurement}"





class Quotation(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE,blank=True, null=True)
    file = models.FileField(upload_to='uploads/purchase_request')
    supplier = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,blank=True, null=True)   
    vat = models.CharField(max_length=100, choices=[('inc','Inclusive'),('excl','Exclusive')],verbose_name='VAT',default='excl')
    def __str__(self):
        return f'{self.purchase_request} - {self.supplier}'
    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "QT" + timestamp + random_number
        super().save(*args, **kwargs)

class QuoteItem(models.Model):
    pr_item = models.ForeignKey(PrItem, models.CASCADE, blank=True, null=True)
    quantity = models.DecimalField(max_digits=40, decimal_places=2)
    unit_price = models.DecimalField(max_digits=40, decimal_places=2)
    quotation = models.ForeignKey(Quotation, models.CASCADE, blank=True, null=True)
    def __str__(self):
        return str(self.pk)


