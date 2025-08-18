from django.db import models
from it.users.models import Supplier
from finance.comparative_schedules.models import Currency

from finance.purchase_request.models import PurchaseRequest
from it.users.models import *

class DPProcPlan(models.Model):
    proc_ref = models.CharField(max_length=100)
    period = models.CharField(max_length=4)
    description = models.CharField(max_length=100)
    annual_cost = models.DecimalField(max_digits=10, decimal_places=2)
    annual_qty = models.DecimalField(max_digits=10, decimal_places=2)
    uom = models.CharField(max_length=10)
    proc_method = models.CharField(max_length=20)
    sprc = models.CharField(max_length=3)
    region = models.CharField(max_length=100)

class DirectPurchase(models.Model):
    cs_id = models.CharField(max_length=100)
    pr_id = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, blank=True, null=True, default=None)
    pr_date = models.DateField(blank=True, null=True)
    proc_plan = models.ForeignKey(DPProcPlan, on_delete=models.CASCADE, blank=True, null=True, default=None)
    ref_date = models.DateField(blank=True, null=True, default=None)
    scope_of_work = models.CharField(max_length=400)
    closing_date = models.DateField(blank=True, null=True)
    closing_time = models.CharField(max_length=10)
    advert = models.CharField(max_length=400)
    show_site_visit = models.BooleanField(default=False, null=True, blank=True)
    show_sample_required = models.BooleanField(default=False, null=True, blank=True)
    pr_number = models.CharField(max_length=100)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, default=1)
    cs_opened = models.DateField(blank=True, null=True)
    tac_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled = models.BooleanField(default=False)
    additional_notes = models.CharField(max_length=400, blank=True, null=True)
    # Add missing field that exists in comparative schedules
    buyers_notes = models.CharField(max_length=400, blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_by_id', 'region', 'cancelled']),
            models.Index(fields=['cs_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Direct Purchase"
        verbose_name_plural = "Direct Purchases"
    
    def __str__(self):
        return f"DP-{self.cs_id} - {self.scope_of_work[:50]}"
    
    # add a function to get logged in user's cost center
    def get_logged_in_user_cost_center(self):
        return self.created_by.cost_center

class DPRequiredItems(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    item_name = models.CharField(max_length=300)
    quantity = models.CharField(max_length=50)
    unit_of_measurement = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Required Item"
        verbose_name_plural = "DP Required Items"
        indexes = [
            models.Index(fields=['cs_id', 'item_id']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit_of_measurement}"

class DPItems(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    item_name = models.CharField(max_length=300)
    quantity = models.CharField(max_length=50)
    unit_of_measurement = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Item"
        verbose_name_plural = "DP Items"
        indexes = [
            models.Index(fields=['cs_id', 'item_id']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit_of_measurement}"

class DPBids(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    item_id = models.ForeignKey(DPItems, on_delete=models.CASCADE)
    sup_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    unit_price = models.CharField(max_length=50)
    vat = models.CharField(max_length=10, blank=True, null=True)
    quoted_qty = models.CharField(max_length=50)
    bid_no = models.CharField(max_length=10)
    quote_date = models.DateField()
    total = models.CharField(max_length=50)
    bid_document = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Bid"
        verbose_name_plural = "DP Bids"
        indexes = [
            models.Index(fields=['cs_id', 'bid_no']),
            models.Index(fields=['sup_id']),
        ]
    
    def __str__(self):
        return f"Bid {self.bid_no} - {self.sup_id.name if self.sup_id else 'Unknown Supplier'}"
    
class DPCompliance(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
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
    
    class Meta:
        verbose_name = "DP Compliance"
        verbose_name_plural = "DP Compliances"
        indexes = [
            models.Index(fields=['cs_id', 'supplier_id']),
            models.Index(fields=['decision']),
        ]
    
    def __str__(self):
        return f"Compliance - {self.supplier_id.name if self.supplier_id else 'Unknown'} - {self.decision}"

class DPComplianceRemarks(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Compliance Remark"
        verbose_name_plural = "DP Compliance Remarks"
        indexes = [
            models.Index(fields=['cs_id', 'supplier_id']),
        ]
    
    def __str__(self):
        return f"Remarks - {self.supplier_id.name if self.supplier_id else 'Unknown'} - {self.remarks[:50]}"
    
class DPRanking(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    rank = models.CharField(max_length=100)
    remarks = models.CharField(max_length=255)
    decision = models.CharField(max_length=255)
    total = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Ranking"
        verbose_name_plural = "DP Rankings"
        indexes = [
            models.Index(fields=['cs_id', 'rank']),
            models.Index(fields=['supplier_id']),
        ]
    
    def __str__(self):
        return f"Rank {self.rank} - {self.supplier_id.name if self.supplier_id else 'Unknown'}"

class DPOrder(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    order_no = models.CharField(max_length=100)
    order_status = models.CharField(max_length=100)
    order_date = models.DateField()
    delivery_date = models.DateField()
    payment_status = models.CharField(max_length=100)
    site_visit_done = models.CharField(max_length=100)
    samples_delivered = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Order"
        verbose_name_plural = "DP Orders"
        indexes = [
            models.Index(fields=['cs_id', 'order_no']),
            models.Index(fields=['order_status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_no} - {self.order_status}"

class DPCommittee(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    committee_name = models.CharField(max_length=100, null=True, blank=True)
    committee_position = models.CharField(max_length=100, null=True, blank=True)
    committee_status = models.BooleanField(default=False, null=True, blank=True)
    committee_approval = models.CharField(max_length=100, null=True, blank=True) # Approved, Rejected
    justification = models.CharField(max_length=255, null=True, blank=True)
    committee_date = models.DateTimeField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Committee Member"
        verbose_name_plural = "DP Committee Members"
        indexes = [
            models.Index(fields=['cs_id', 'user_id']),
            models.Index(fields=['committee_approval']),
        ]
    
    def __str__(self):
        return f"Committee - {self.user.username if self.user else 'Unknown'} - {self.committee_position or 'Member'}"
    
class DPApproval(models.Model):
    cs_id = models.ForeignKey(DirectPurchase, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    approver_role = models.CharField(max_length=100, null=True, blank=True) # General Manager, Finance Manager
    approval = models.CharField(max_length=100, null=True, blank=True) # Approved, Rejected
    justification = models.CharField(max_length=255, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "DP Approval"
        verbose_name_plural = "DP Approvals"
        indexes = [
            models.Index(fields=['cs_id', 'approver_role']),
            models.Index(fields=['approval']),
        ]
    
    def __str__(self):
        return f"{self.approver_role} - {self.approval} by {self.user.username if self.user else 'Unknown'}"