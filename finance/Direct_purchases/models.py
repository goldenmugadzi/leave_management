from django.db import models
from it.users.models import UserProfile,Regions,Sections
from finance.rfq.models import RFQ
from approve.models import Process
# Create your models here.
class Direct_purchase(models.Model):
    id = models.CharField(primary_key=True, max_length=60)
    section = models.ForeignKey(Sections, models.DO_NOTHING, blank=True, null=True)
    process = models.OneToOneField(Process, on_delete=models.SET_NULL, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    requested_by = models.ForeignKey(UserProfile , models.DO_NOTHING,blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    rfq = models.ForeignKey(RFQ, models.CASCADE, blank=True, null=True)
    service_type = models.CharField(max_length=100, blank=True, null=True)
    region = models.ForeignKey(Regions, models.DO_NOTHING, blank=True, null=True)
    grn_delivery_status = models.CharField(max_length=100, blank=True, null=True)
    grn_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return self.id

    def save(self, *args, **kwargs):
        if not self.id:
            if self.date_created is None:
                self.date_created = timezone.now()
            timestamp = self.date_created.strftime('%Y%m%d%H%M%S')
            self.id = f"DP{timestamp}"
        super().save(*args, **kwargs)


class Supplier(models.Model):
    name = models.CharField(max_length=100,unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.IntegerField(max_length=13, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
       ordering = ['name']
    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    total = models.FloatField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, models.DO_NOTHING)
    direct_purchase = models.ForeignKey(Direct_purchase, models.DO_NOTHING)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name



