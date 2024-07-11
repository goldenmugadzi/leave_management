from django.db import models
from finance.Direct_purchases.models import Supplier
from finance.comparative_schedules.models import Currency

from finance.purchase_request.models import PurchaseRequest
from it.users.models import *

class RBProcPlan(models.Model):
    proc_ref = models.CharField(max_length=100)
    period = models.CharField(max_length=4)
    description = models.CharField(max_length=100)
    annual_cost = models.DecimalField(max_digits=10, decimal_places=2)
    annual_qty = models.DecimalField(max_digits=10, decimal_places=2)
    uom = models.CharField(max_length=10)
    proc_method = models.CharField(max_length=20)
    sprc = models.CharField(max_length=3)
    region = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class RistricedBiddings(models.Model):
    cs_id = models.CharField(max_length=100)
    pr_id = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    pr_date = models.DateField()
    proc_plan = models.ForeignKey(RBProcPlan, on_delete=models.CASCADE)
    ref_date = models.DateField(blank=True, null=True, default=None)
    scope_of_work = models.CharField(max_length=400)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, default=1)
    closing_date = models.DateField()
    closing_time = models.CharField(max_length=10)
    advert = models.CharField(max_length=400)
    show_site_visit = models.BooleanField(default=False, null=True, blank=True)
    show_sample_required = models.BooleanField(default=False, null=True, blank=True)
    pr_number = models.CharField(max_length=100)
    pr_date = models.DateField()
    cs_opened = models.DateField()
    tac_date = models.DateField()
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    cancelled = models.BooleanField(default=False)
    additional_notes = models.CharField(max_length=400, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RBRequiredItems(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    item_name = models.CharField(max_length=300)
    quantity = models.CharField(max_length=50)
    unit_of_measurement = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class RBItems(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    item_name = models.CharField(max_length=300)
    quantity = models.CharField(max_length=50)
    unit_of_measurement = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class RBBids(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    item_id = models.ForeignKey(RBItems, on_delete=models.CASCADE)
    sup_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    unit_price = models.CharField(max_length=50)
    vat = models.CharField(max_length=10)
    quoted_qty = models.CharField(max_length=50)
    bid_no = models.CharField(max_length=10)
    quote_date = models.DateField()
    total = models.CharField(max_length=50)
    bid_document = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)
    
class RBCompliance(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    payment_terms = models.BooleanField(default=False)
    bid_validity = models.BooleanField(default=False)
    delivery_period = models.BooleanField(default=False)
    technical_specifications = models.BooleanField(default=False)
    valid_tax_clearance = models.BooleanField(default=False)
    registered_with_praz = models.BooleanField(default=False)
    site_visit_done = models.BooleanField(default=False)
    samples_delivered = models.BooleanField(default=False)
    decision = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class RBComplianceRemarks(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=255)
    
class RBRanking(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    rank = models.CharField(max_length=100)
    remarks = models.CharField(max_length=255)
    decision = models.CharField(max_length=255)
    total = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class RBCommittee(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    committee_name = models.CharField(max_length=100, null=True, blank=True)
    committee_position = models.CharField(max_length=100, null=True, blank=True)
    committee_status = models.BooleanField(default=False, null=True, blank=True)
    committee_approval = models.CharField(max_length=100, null=True, blank=True) # Approved, Rejected
    justification = models.CharField(max_length=255, null=True, blank=True)
    committee_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
class RBApproval(models.Model):
    cs_id = models.ForeignKey(RistricedBiddings, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    approver_role = models.CharField(max_length=100, null=True, blank=True) # General Manager, Finance Manager
    approval = models.CharField(max_length=100, null=True, blank=True) # Approved, Rejected
    justification = models.CharField(max_length=255, null=True, blank=True)
    approval_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)