from django.db import models
from finance.Ace.models import Ace
# Create your models here.
class RFQ(models.Model):
    rfq_id = models.CharField(primary_key=True, max_length=60)
    rfq_type = models.CharField(max_length=15, blank=True, null=True)
    Department = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    scope_of_work = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.FloatField(blank=True, null=True)
    proc_ref = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    quotation1 = models.FileField(upload_to='uploads/rfq')
    quotation2 = models.FileField(upload_to='uploads/rfq')
    quotation3 = models.FileField(upload_to='uploads/rfq')
    payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    rfq_id2 = models.CharField(max_length=60)
    approval_status = models.CharField(max_length=120, blank=True, null=True)
    approved_by = models.CharField(max_length=56, blank=True, null=True)
    rejected_by = models.CharField(max_length=56, blank=True, null=True)
    date_approved = models.DateField(null=True, blank=True)
    ace = models.ForeignKey(Ace, models.DO_NOTHING, db_column='ace_id2', blank=True, null=True)

    section_head = models.CharField(max_length=100, blank=True, null=True)
    finance_manager = models.CharField(max_length=100, blank=True, null=True)
    general_manager = models.CharField(max_length=100, blank=True, null=True)

    general_manager_approval_status = models.CharField(max_length=100, blank=True, null=True)
    general_manager_approval_date = models.DateField(null=True, blank=True)
    general_manager_rejection_reason = models.TextField(max_length=500, blank=True, null=True)
    finance_manager_approval_status = models.CharField(max_length=100, blank=True, null=True)
    finance_manager_approval_date = models.DateField(null=True, blank=True)
    finance_manager_rejection_reason = models.TextField(max_length=500, blank=True, null=True)
    section_head_approval_status = models.CharField(max_length=100, blank=True, null=True)
    section_head_approval_date = models.DateField(null=True, blank=True)
    section_head_rejection_reason = models.TextField(max_length=500, blank=True, null=True)






    class Meta:
        db_table = 'rfq'
    def __str__(self):
        return str(self.rfq_id)
