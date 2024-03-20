from django.db import models


# Create your models here.
class Pettycash(models.Model):
    Department = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    petty_id = models.CharField(max_length=60)
    pettycash_id = models.AutoField(primary_key=True)
    approval_status = models.CharField(max_length=16, blank=True, null=True)


    section_head= models.CharField(max_length=26, blank=True, null=True)
    petty_authoriser = models.CharField(max_length=26, blank=True, null=True)
    disburser = models.CharField(max_length=26, blank=True, null=True)

    section_head_approval = models.CharField(max_length=16, blank=True, null=True)
    petty_authoriser_approval = models.CharField(max_length=16, blank=True, null=True)
    disburser_approval = models.CharField(max_length=16, blank=True, null=True)

    section_head_comment = models.CharField(max_length=100, blank=True, null=True)
    petty_authoriser_comment = models.CharField(max_length=100, blank=True, null=True)
    disburser_comment = models.CharField(max_length=100, blank=True, null=True)

    section_head_approval_date = models.DateField(null=True, blank=True)
    petty_authoriser_approval_date = models.DateField(null=True, blank=True)
    disburser_approval_date = models.DateField(null=True, blank=True)


    def __str__(self):
        return self.petty_id

class Quotation(models.Model):
    rfq = models.ForeignKey(Pettycash, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/pettycash')


    def __str__(self):
        return str(self.pk)
