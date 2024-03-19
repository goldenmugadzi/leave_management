from django.db import models
from finance.Ace.models import Ace
# Create your models here.
class RFQ(models.Model):
    rfq_id = models.CharField(primary_key=True, max_length=60)
    rfq_type = models.CharField(max_length=15, blank=True, null=True)

    section = models.CharField(max_length=100, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    scope_of_work = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.FloatField(blank=True, null=True)
    proc_ref = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    quotation1 = models.FileField(upload_to='uploads/finance/rfq')
    quotation2 = models.FileField(upload_to='uploads/finance/rfq')
    quotation3 = models.FileField(upload_to='uploads/finance/rfq')
    payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)

    approval_status = models.CharField(max_length=120, blank=True, null=True)
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
<<<<<<< HEAD
        return str(self.rfq_id)
=======
        return self.rfq_id

    def save(self, *args, **kwargs):
        if not self.rfq_id:
            if self.date_created is None:
                self.date_created = timezone.now()
            timestamp = self.date_created.strftime('%Y%m%d%H%M%S')
            self.rfq_id = f"RFQ{timestamp}"
        super().save(*args, **kwargs)


class Quotation(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/rfq')

    class Meta:
        db_table = 'quotation'

    def __str__(self):
        return str(self.pk)

# class ApprovalStage(models.Model):
#     stage = models.CharField(max_length=100)

#     class Meta:
#         db_table = 'approval_stage'

#     def __str__(self):
#         return self.stage


# class ApprovalStatus(models.Model):
#     stage = models.ForeignKey(ApprovalStage, on_delete=models.CASCADE)
#     status = models.CharField(
#         max_length=100,
#         choices=[
#             ('Approved', 'Approved'),
#             ('Rejected', 'Rejected'),
#             ('Pending', 'Pending'),
#             ('Cancelled', 'Cancelled'),
#         ],
#         default='Pending'
#     )

#     class Meta:
#         db_table = 'approval_status'

#     def __str__(self):
#         return self.status


# class RFQApproval(models.Model):
#     rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE)
#     approval_status = models.ForeignKey(ApprovalStatus, on_delete=models.CASCADE)
#     approval_date = models.DateField(null=True, blank=True)
#     rejection_reason = models.TextField(max_length=500, blank=True, null=True)

#     class Meta:
#         db_table = 'rfq_approval'
>>>>>>> parent of decd928 (tables in sqlite)
