from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from approve.models import Process
from finance.Ace.models import Budget
from it.users.models import Regions, UserProfile, Sections, Designations

# Create your models here.
from django.db import models


class RemoteBudget(models.Model):
    # Define your fields here. For example:
    budget_id = models.AutoField(primary_key=True)
    section_code = models.CharField(max_length=36, blank=True, null=True)
    section = models.CharField(max_length=36, blank=True, null=True)
    budget = models.CharField(max_length=200, blank=True, null=True)
    allocated = models.FloatField(blank=True, null=True)
    awaiting_sanctioning = models.FloatField(blank=True, null=True, default=0)
    withdrawn = models.FloatField(blank=True, null=True, default=0)
    balance = models.FloatField(blank=True, null=True, default=0)
    withdrawal_date = models.DateField(blank=True, null=True)
    awaiting_sanctioning = models.FloatField(blank=True, null=True, default=0)
    period = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(9999)])

    # region = models.CharField(max_length=36, blank=True, null=True)

    # Add other fields based on the columns in the remote table

    class Meta:
        db_table = 'budget'  # Use the exact name of the table in your remote database
        managed = False  # Django won't create a table in your local database
        app_label = 'ACE2'  # Set the app label to the name of the app where this model is defined


# class RemoteDataModelRouter:
#     """
#     A router to control all database operations on models in the
#     RemoteDataModel application.
#     """
#
#     def db_for_read(self, model, **hints):
#         """
#         Attempts to read RemoteDataModel models go to 'other'.
#         """
#         if model._meta.app_label == 'RemoteDataModel':
#             return 'other'
#         return None
#
#     def db_for_write(self, model, **hints):
#         """
#         Attempts to write RemoteDataModel models go to 'other'.
#         """
#         if model._meta.app_label == 'RemoteDataModel':
#             return 'other'
#         return None
#
#     def allow_relation(self, obj1, obj2, **hints):
#         """
#         Allow relations if a model in the RemoteDataModel app is involved.
#         """
#         if obj1._meta.app_label == 'RemoteDataModel' or \
#                 obj2._meta.app_label == 'RemoteDataModel':
#             return True
#         return None
#
#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         """
#         Make sure the RemoteDataModel app only appears in the 'other'
#         database.
#         """
#         if app_label == 'RemoteDataModel':
#             return db == 'other'
#         return None
#
#
# class Old_budget(models.Model):
#     # Define fields that map to columns in your remote table
#     field1 = models.CharField(max_length=100)
#     field2 = models.IntegerField()
#
#     class Meta:
#         managed = False  # Set to avoid creating a local table
#         db_table = 'budget'


class AssetBudget(models.Model):
    budget_id = models.AutoField(primary_key=True, db_index=True)
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
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True)
    created_date = models.DateField(blank=True, null=True)
    budget_note = models.FileField(upload_to='uploads/budget')

    def __str__(self):
        return str(self.budget_name)

    #order list by id and period starting with the largest
    class Meta:
        ordering = ['budget_id', '-period']


class Ace2(models.Model):
    CLASSIFICATION_CHOICES = [
        ('Internal', 'Internal'),
        ('Project', 'Project'),
    ]

    CURRENCY_CHOICES = [
        ('ZIG', 'ZIG'),
        # ('USD', 'USD'),  # Add USD currency
    ]
    
    # Add ACE type choices for different workflows
    ACE_TYPE_CHOICES = [
        ('standard', 'Standard ACE'),
        ('high_value', 'High Value ACE (100k+ USD)'),
    ]

    # ace_type = models.CharField(max_length=15, blank=True, null=True)
    
    # Add new fields
    ace_type = models.CharField(max_length=20, choices=ACE_TYPE_CHOICES, default='standard')
    currency = models.CharField(max_length=15, blank=True, null=True, choices=CURRENCY_CHOICES, default='ZIG')
    usd_equivalent = models.FloatField(blank=True, null=True, help_text="Amount in USD for comparison")

    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    allocation_code_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    details_of_expenditure = models.CharField(max_length=100, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    # payment_mode = models.CharField(max_length=100, blank=True, null=True)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    Ace_id2 = models.CharField(max_length=60, db_index=True)
    Ace_id = models.AutoField(primary_key=True)

    asset_number = models.TextField(max_length=1000, blank=True, null=True)
    capital_estimated = models.FloatField(blank=True, null=True)
    capital_sanctioned = models.FloatField(blank=True, null=True)
    budget_id = models.ForeignKey(AssetBudget, on_delete=models.DO_NOTHING, default=1)
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
    # approval_code = models.IntegerField(null=True, max_length=5)

    quantity = models.IntegerField(null=True)

    process = models.ForeignKey(Process, on_delete=models.SET_NULL, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)

    # dummy = models.CharField(null=True, max_length=120, blank=True)

    def __str__(self):
        return self.Ace_id2


class Asset_budget_Virament(models.Model):
    virament_id = models.AutoField(primary_key=True)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True, null=True)
    from_budget = models.ForeignKey(AssetBudget, on_delete=models.DO_NOTHING, related_name='from_budget')
    to_budget = models.ForeignKey(AssetBudget, on_delete=models.DO_NOTHING, related_name='to_budget')
    amount = models.FloatField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    process = models.ForeignKey(Process, on_delete=models.DO_NOTHING, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    currency = models.CharField(max_length=15, blank=True, null=True, choices=Ace2.CURRENCY_CHOICES)

    def __str__(self):
        return str(self.virament_id)


class Transactions(models.Model):
    Ace_id2 = models.ForeignKey(Ace2, on_delete=models.CASCADE, blank=True, null=True)
    virament = models.ForeignKey(Asset_budget_Virament, on_delete=models.DO_NOTHING, blank=True, null=True)
    details_of_expenditure = models.CharField(blank=True, null=True, max_length=120)
    approval_status = models.CharField(blank=True, null=True, max_length=120)
    transaction_id = models.AutoField(primary_key=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING)
    amount = models.FloatField(blank=True, null=True, max_length=120)
    budget = models.ForeignKey(AssetBudget, on_delete=models.CASCADE)

    # quotation = models.ForeignKey(Ace, on_delete=models.CASCADE)

    def __str__(self):
        return self.transaction_id


class Quotation(models.Model):
    ace2 = models.ForeignKey(Ace2, on_delete=models.CASCADE, blank=True, null=True)
    virament = models.ForeignKey(Asset_budget_Virament, on_delete=models.DO_NOTHING, blank=True, null=True)
    quotation_file = models.FileField(upload_to='uploads/ace2')

    def __str__(self):
        return str(self.pk)


class AceReport(models.Model):
    report_id2 = models.AutoField(primary_key=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    region = models.ForeignKey(Regions, blank=True, null=True, on_delete=models.DO_NOTHING)
    budget = models.ForeignKey(AssetBudget, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return str(self.report_id2)
