import random
import time

from approve.models import Process
from finance.Ace.models import Ace
from it.users.models import *


class Procurement(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    description = models.TextField(blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    scope_of_work = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    proc_ref = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    PAYMENT_MODE_CHOICES = [('USD Cash', 'USD Cash'),('USD Swipe', 'USD Swipe'),('ZWL Cash', 'ZWL Cash'),('ZWL Transfer', 'ZWL Transfer'),]
    payment_mode = models.CharField(max_length=100, blank=True, null=True, choices=PAYMENT_MODE_CHOICES)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    ace = models.ForeignKey(Ace, on_delete=models.SET_NULL, blank=True, null=True)
    process = models.OneToOneField(Process, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        if not self.id:  # Generate rfq_id only if it doesn't exist
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "Procurement" + timestamp + random_number
        super().save(*args, **kwargs)


class Quotation(models.Model):
    procurement = models.ForeignKey(Procurement, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/procurement')
    supplier = models.CharField(max_length=100)
    amount = models.IntegerField()    


    def __str__(self):
        return f"Quotation from {self.supplier} for Order {self.procurement}"

class Order(models.Model):
    procurement = models.ForeignKey('Procurement', on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20)
    signed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return self.order_number


class SiteVisit(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    scheduled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Site Visit for Order {self.order}"

class Bid(models.Model):
    procurement = models.ForeignKey('Procurement', on_delete=models.CASCADE)
    response_received = models.BooleanField(default=False)
    second_non_response = models.BooleanField(default=False)

    def __str__(self):
        return str(self.pk)

        return f"Bid for Procurement {self.procurement}"


class Delivery(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    able_to_deliver = models.BooleanField(default=False)

    def __str__(self):
        return f"Delivery for Order {self.order}"