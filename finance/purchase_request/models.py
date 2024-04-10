import random
import time
from django.db import models
from approve.models import Process
from finance.Ace.models import Ace
from it.users.models import UserProfile, Sections, Roles, Supplier
class PurchaseRequest(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    description = models.TextField(blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    scope_of_work = models.CharField(max_length=100, blank=True, null=True)
    proc_ref = models.CharField(max_length=100, blank=True, null=True)
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
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "PR" + timestamp + random_number
        super().save(*args, **kwargs)
class Quotation(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE,blank=True, null=True)
    file = models.FileField(upload_to='uploads/purchase_request')
    supplier = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE,blank=True, null=True)   
    def __str__(self):
        return f'{self.purchase_request} - {self.supplier}'
class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, blank=True, null=True)
    unit_measure = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.IntegerField()
    quotation = models.ForeignKey(Quotation, models.DO_NOTHING, blank=True, null=True)
    def __str__(self):
        return str(self.pk)
class Bid(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    response_received = models.BooleanField(default=False)
    second_non_response = models.BooleanField(default=False)
    Supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.pk)
class Order(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    signed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    def __str__(self):
        return str(self.pk)
    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "odr" + timestamp + random_number
        super().save(*args, **kwargs)
class SiteVisit(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    scheduled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    def __str__(self):
        return str(self.pk)
class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    able_to_deliver = models.BooleanField(default=False)
    def __str__(self):
        return str(self.pk)