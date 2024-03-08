from django.db import models
from finance.Ace.models import Ace
from it.users.models import *
from django.utils import timezone
from approve.models import Process,Application

class RFQ(models.Model):
    # rfq_id = models.CharField(primary_key=True, max_length=20, editable=False)
    description = models.TextField( blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    scope_of_work = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.FloatField(blank=True, null=True)
    proc_ref = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    ace = models.ForeignKey(Ace, on_delete=models.SET_NULL, blank=True, null=True)
    process = models.OneToOneField(Process, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.description



class Quotation(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/rfq')

    # class Meta:
    #     db_table = 'quotation'

    def __str__(self):
        return str(self.pk)

