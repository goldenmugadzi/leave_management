from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from approve.models import Process
from finance.Ace.models import Budget
from it.users.models import Regions, UserProfile, Sections, Designations


# Create your models here.

class AssetBudget(models.Model):
    budget_id = models.AutoField(primary_key=True)
    section_code = models.CharField(max_length=36, blank=True, null=True)
    section = models.CharField(max_length=36, blank=True, null=True)
    budget_name = models.CharField(max_length=200, blank=True, null=True)
    allocated = models.FloatField(blank=True, null=True)
    awaiting_sanctioning = models.FloatField(blank=True, null=True, default=0)
    withdrawn = models.FloatField(blank=True, null=True, default=0)
    to_be_withdrawn = models.FloatField(blank=True, null=True, default=0)
    balance = models.FloatField(blank=True, null=True, default=0)
    withdrawal_date = models.DateField(blank=True, null=True)
    period = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(9999)])
    region = models.CharField(max_length=36, blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    budget_note = models.FileField(upload_to='uploads/budget')

    def __str__(self):
        return str(self.budget_name)


class Ace2(models.Model):
    CLASSIFICATION_CHOICES = [
        ('Internal', 'Internal'),
        ('Project', 'Project'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('ZIG', 'ZIG'),
    ]

    # ace_type = models.CharField(max_length=15, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True),
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    # payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    Ace_id2 = models.CharField(max_length=60)
    Ace_id = models.AutoField(primary_key=True)

    asset_number = models.TextField(max_length=1000, blank=True, null=True)
    capital_estimated = models.FloatField(blank=True, null=True)
    capital_sanctioned = models.FloatField(blank=True, null=True)
    budget_id = models.ForeignKey(Budget, on_delete=models.DO_NOTHING, default=1)
    # budget_name = models.ForeignKey(assetBudget, on_delete=models.CASCADE)

    # project items
    classification = models.CharField(max_length=200, blank=True, null=True, choices=CLASSIFICATION_CHOICES)
    present_tariff = models.FloatField(blank=True, null=True)
    present_fmc = models.CharField(max_length=200, blank=True, null=True)
    capital_contribution = models.FloatField(blank=True, null=True)
    materials = models.FloatField(blank=True, null=True)
    connection_fee = models.FloatField(blank=True, null=True)
    labour = models.FloatField(blank=True, null=True)
    transport = models.FloatField(blank=True, null=True)
    total_connection_fee = models.FloatField(blank=True, null=True)

    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    currency = models.CharField(null=True, max_length=15, blank=True, choices=CURRENCY_CHOICES)
    # approval_code = models.IntegerField(null=True, max_length=5)

    quantity = models.IntegerField(null=True, max_length=20)

    process = models.OneToOneField(Process, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.Ace_id2


class Transactions(models.Model):
    Ace_id2 = models.ForeignKey(Ace2, on_delete=models.CASCADE)
    details_of_expenditure = models.CharField(blank=True, null=True, max_length=120)
    approval_status = models.CharField(blank=True, null=True, max_length=120)
    transaction_id = models.AutoField(primary_key=True)
    region = models.CharField(blank=True, null=True, max_length=120)
    amount = models.FloatField(blank=True, null=True, max_length=120)
    ace2 = models.CharField(blank=True, null=True, max_length=120)
    budget = models.ForeignKey(AssetBudget, on_delete=models.CASCADE)

    # quotation = models.ForeignKey(Ace, on_delete=models.CASCADE)

    def __str__(self):
        return self.transaction_id


class Quotation(models.Model):
    ace2 = models.ForeignKey(Ace2, on_delete=models.CASCADE)
    quotation_file = models.FileField(upload_to='uploads/ace2')

    def __str__(self):
        return str(self.pk)
