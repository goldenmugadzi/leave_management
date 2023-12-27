from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Create your models here.

# budget models
class YearField(models.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(models.MinValueValidator(1))
        self.validators.append(models.MaxValueValidator(9999))

    def deconstruct(self):
        return (YearField,)

    def get_internal_value(self, value):
        return value.year

    def set_internal_value(self, value, data=None):
        return value

class Budget(models.Model):
    budget_id = models.AutoField(primary_key=True)
    section_code = models.CharField(max_length=36, blank=True, null=True)
    section = models.CharField(max_length=36, blank=True, null=True)
    budget_name = models.CharField(max_length=36, blank=True, null=True)
    allocated = models.FloatField( blank=True, null=True)
    withdrawn = models.FloatField(blank=True, null=True)
    balance = models.FloatField( blank=True, null=True)
    withdrawal_date = models.DateField(blank=True, null=True)
    period = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(9999)])
    region = models.CharField(max_length=36, blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    budget_note = models.FileField(upload_to='uploads/budget')

    def __str__(self):
        return self.budget_id

class Ace(models.Model):
    # ace_type = models.CharField(max_length=15, blank=True, null=True)
    Department = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    quotation1 = models.FileField(upload_to='uploads/ace')
    quotation2 = models.FileField(upload_to='uploads/ace')
    quotation3 = models.FileField(upload_to='uploads/ace')
    # payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    Ace_id2 = models.CharField(max_length=60)
    Ace_id = models.AutoField(primary_key=True)
    approval_status = models.CharField(max_length=16, blank=True, null=True)
    approved_by = models.CharField(max_length=26, blank=True, null=True)
    rejected_by = models.CharField(max_length=26, blank=True, null=True)
    date_approved = models.DateField(null=True, blank=True)
    date_rejected = models.DateField(null=True,blank=True)
    rejection_reason = models.CharField(max_length=200, blank=True, null=True)
    fm_approval_status = models.CharField(max_length=16, blank=True, null=True)
    fm_approved = models.CharField(max_length=26, blank=True, null=True)
    fm_rejected = models.CharField(max_length=26, blank=True, null=True)
    fm_rejection_reason = models.CharField(max_length=200, blank=True, null=True)
    fm_date_approved = models.DateField(null=True, blank=True)
    fm_date_rejected = models.DateField(null=True,blank=True)
    gm_approval_status = models.CharField(max_length=16, blank=True, null=True)
    gm_approved = models.CharField(max_length=26, blank=True, null=True)
    gm_rejection_reason = models.CharField(max_length=200, blank=True, null=True)
    gm_rejected = models.CharField(max_length=200, blank=True, null=True)
    gm_approved_date = models.DateField(null=True, blank=True)
    asset_number = models.CharField(max_length=26, blank=True, null=True)
    capital_estimated = models.FloatField( blank=True, null=True)
    capital_sanctioned = models.FloatField( blank=True, null=True)
    budget_id = models.ForeignKey(Budget, on_delete=models.CASCADE ,default=1)
    region = models.CharField(max_length=40, blank=True,null=True)
    # budget_name = models.ForeignKey(Budget, on_delete=models.CASCADE)
    # project items
    classification = models.CharField(max_length=200, blank=True, null=True)
    present_tariff = models.FloatField( blank=True, null=True)
    present_fmc = models.CharField(max_length=200, blank=True, null=True)
    capital_contribution = models.FloatField( blank=True, null=True)
    materials = models.FloatField( blank=True, null=True)
    connection_fee = models.FloatField( blank=True, null=True)
    labour = models.FloatField( blank=True, null=True)
    transport = models.FloatField( blank=True, null=True)
    total_connection_fee = models.FloatField( blank=True, null=True)
    designation = models.CharField(null = True, max_length=70)


    def __str__(self):
        return self.Ace_id2

