from django.db import models
from ..purchase_request.models import *
from it.users.models import Supplier

# Create your models here.

class Compare(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.pk)
    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "CMP" + timestamp + random_number
        super().save(*args, **kwargs)

class Bid(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    time= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.pk)

    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "BID" + timestamp + random_number
        super().save(*args, **kwargs)


class BidItem(models.Model):
    pr_item = models.ForeignKey(PrItem, models.CASCADE, blank=True, null=True)
    quantity = models.DecimalField(max_digits=40, decimal_places=2)
    bid = models.ForeignKey(Bid, models.CASCADE, blank=True, null=True)
    price = models.DecimalField(max_digits=40, decimal_places=2)  # Add a price field for the bid

    def __str__(self):
        return str(self.pr_item)


class Order(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.pk)
    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "ODR" + timestamp + random_number
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    bid_item = models.ForeignKey(BidItem, models.CASCADE, blank=True, null=True)
    order = models.ForeignKey(Order, models.CASCADE, blank=True, null=True)
    quantity = models.DecimalField(max_digits=40, decimal_places=2)
    def __str__(self):
        return str(self.bid_item.pr_item.name) 
    


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