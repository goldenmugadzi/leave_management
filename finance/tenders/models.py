from django.db import models
from finance.Direct_purchases.models import Supplier

from finance.rfq.models import RFQ
from it.users.models import *

# Create your models here.
class Tender(models.Model):
    tender_id = models.CharField(max_length=100)
    rfq_id = models.ForeignKey(RFQ, on_delete=models.CASCADE)
    rfq_date = models.DateField()
    scope_of_work = models.CharField(max_length=400)
    closing_date = models.DateField()
    closing_time = models.CharField(max_length=10)
    advert = models.CharField(max_length=400)
    pr_number = models.CharField(max_length=100)
    pr_date = models.DateField()
    tender_opened = models.DateField()
    tac_date = models.DateField()
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)

class TenderItems(models.Model):
    document_id = models.CharField(max_length=100)
    item_name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)
    unit_price = models.CharField(max_length=50)
    total_price = models.CharField(max_length=50)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    delivery_date = models.DateField()
    remarks = models.CharField(max_length=400)

class Bids(models.Model):
    tender_id = models.ForeignKey(Tender, on_delete=models.CASCADE)
    item_id = models.ForeignKey(TenderItems, on_delete=models.CASCADE)
    sup_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    unit_price = models.CharField(max_length=50)
    vat = models.CharField(max_length=10)
    quoted_qty = models.CharField(max_length=50)
    bid_no = models.CharField(max_length=10)
    quote_date = models.DateField()
    total = models.CharField(max_length=50)
    bid_document = models.CharField(max_length=400)
    
class TenderCompliance(models.Model):
    tender_id = models.ForeignKey(Tender, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    payment_terms = models.CharField(max_length=100)
    bid_validity = models.CharField(max_length=100)
    delivery_period = models.CharField(max_length=100)
    technical_specifications = models.CharField(max_length=100)
    valid_tax_clearance = models.CharField(max_length=100)
    registered_with_praz = models.CharField(max_length=100)
    site_visit_done = models.CharField(max_length=100)
    samples_delivered = models.CharField(max_length=100)
    decision = models.CharField(max_length=255)
    remarks = models.CharField(max_length=255)
    
class Ranking(models.Model):
    tender_id = models.ForeignKey(Tender, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    rank = models.CharField(max_length=100)
    remarks = models.CharField(max_length=255)
    decision = models.CharField(max_length=255)
    
class Order(models.Model):
    tender_id = models.ForeignKey(Tender, on_delete=models.CASCADE)
    order_no = models.CharField(max_length=100)
    order_status = models.CharField(max_length=100)
    order_date = models.DateField()
    delivery_date = models.DateField()
    payment_status = models.CharField(max_length=100)
    site_visit_done = models.CharField(max_length=100)
    samples_delivered = models.CharField(max_length=100)

