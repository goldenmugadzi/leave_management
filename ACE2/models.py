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
    
    @property
    def available_balance(self):
        """
        Calculate available balance considering to_be_withdrawn amounts.
        This is the actual amount available for new commitments.
        """
        if self.balance is None:
            return 0
        
        # Subtract to_be_withdrawn from balance to get truly available funds
        available = self.balance - (self.to_be_withdrawn or 0)
        return max(0, available)  # Ensure never negative
    
    @property
    def remaining_balance(self):
        """Alias for available_balance for backward compatibility"""
        return self.available_balance
    
    def can_accommodate_amount(self, amount):
        """Check if budget can accommodate a new amount considering to_be_withdrawn"""
        if amount is None or amount <= 0:
            return False
        return self.available_balance >= amount
    
    def reserve_amount(self, amount):
        """Reserve an amount in to_be_withdrawn field"""
        if self.can_accommodate_amount(amount):
            if self.to_be_withdrawn is None:
                self.to_be_withdrawn = 0
            self.to_be_withdrawn += amount
            return True
        return False
    
    def release_amount(self, amount):
        """Release a reserved amount from to_be_withdrawn field"""
        if self.to_be_withdrawn is None:
            self.to_be_withdrawn = 0
        
        if amount > 0:
            self.to_be_withdrawn = max(0, self.to_be_withdrawn - amount)

    #order list by id and period starting with the largest
    class Meta:
        ordering = ['budget_id', '-period']


class Ace2(models.Model):
    CLASSIFICATION_CHOICES = [
        ('Internal', 'Internal'),
        ('Project', 'Project'),
    ]

    CURRENCY_CHOICES = [
        ('ZWG', 'ZWG'),
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
        if self.Ace_id2:
            return self.Ace_id2
        elif self.details_of_expenditure:
            return f"ACE-{self.Ace_id or 'DRAFT'} - {self.details_of_expenditure[:50]}"
        else:
            return f"ACE-{self.Ace_id or 'DRAFT'} - No Description"
    
    def clean(self):
        """Validate ACE data before saving"""
        from django.core.exceptions import ValidationError
        
        # Skip Ace_id2 validation during creation since it's generated programmatically
        # Only validate if this is an update (pk exists) and Ace_id2 is still empty
        if self.pk and not self.Ace_id2:
            raise ValidationError("ACE ID (Ace_id2) is required")
        
        if not self.details_of_expenditure:
            raise ValidationError("Details of expenditure is required")
        
        if not self.amount or self.amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        
        if not self.budget_id:
            raise ValidationError("Budget is required")
        
        if not self.section:
            raise ValidationError("Section is required")
        
        # Only validate requested_by if we have a pk (i.e., during updates)
        # During creation, this might be set after the form processing
        if self.pk and not self.requested_by:
            raise ValidationError("Requested by is required")
    
    def save(self, *args, **kwargs):
        """Override save to ensure clean validation"""
        self.clean()
        super().save(*args, **kwargs)

    def get_asset_numbers_list(self):
        """Get list of asset numbers from both old and new format"""
        asset_numbers = []
        
        # Get from new relational model
        new_assets = [an.asset_number for an in self.asset_numbers.all()]
        asset_numbers.extend(new_assets)
        
        # Get from old comma-separated field (for backward compatibility)
        if self.asset_number and not new_assets:
            old_assets = [an.strip() for an in self.asset_number.split(',') if an.strip()]
            asset_numbers.extend(old_assets)
            
        return list(set(asset_numbers))  # Remove duplicates
    
    def migrate_legacy_asset_numbers(self, user):
        """Migrate comma-separated asset numbers to relational model"""
        if self.asset_number and not self.asset_numbers.exists():
            asset_list = [an.strip() for an in self.asset_number.split(',') if an.strip()]
            for asset_num in asset_list:
                ace_asset = AceAssetNumber.objects.create(
                    ace=self,
                    asset_number=asset_num,
                    added_by=user,
                    notes="Migrated from legacy format"
                )
                ace_asset.verify_against_register()
            return len(asset_list)
        return 0
    
    def add_asset_number(self, asset_number, user, notes=""):
        """Add a single asset number with validation"""
        asset_number = asset_number.strip()
        if not asset_number:
            raise ValueError("Asset number cannot be empty")
            
        # Check if already exists
        if self.asset_numbers.filter(asset_number=asset_number).exists():
            raise ValueError(f"Asset number {asset_number} already exists for this ACE")
            
        ace_asset = AceAssetNumber.objects.create(
            ace=self,
            asset_number=asset_number,
            added_by=user,
            notes=notes
        )
        ace_asset.verify_against_register()
        return ace_asset

    def get_all_asset_numbers(self):
        """Get asset numbers from both old and new system"""
        asset_numbers = []
        
        # Get from enhanced system
        enhanced_assets = [an.asset_number for an in self.enhanced_asset_numbers.all()]
        asset_numbers.extend(enhanced_assets)
        
        # Get from legacy field (your existing asset_number field)
        if self.asset_number and not enhanced_assets:
            legacy_assets = [an.strip() for an in self.asset_number.split(',') if an.strip()]
            asset_numbers.extend(legacy_assets)
            
        return asset_numbers

    def migrate_to_enhanced_assets(self, user):
        """Migrate your existing comma-separated asset numbers to enhanced format"""
        if self.asset_number and not self.enhanced_asset_numbers.exists():
            asset_list = [an.strip() for an in self.asset_number.split(',') if an.strip()]
            migrated_count = 0
            for asset_num in asset_list:
                try:
                    ace_asset = AceAssetNumber.objects.create(
                        ace=self,
                        asset_number=asset_num,
                        added_by=user,
                        notes="Migrated from existing data"
                    )
                    ace_asset.verify_against_register()
                    migrated_count += 1
                except Exception as e:
                    print(f"Error migrating {asset_num}: {e}")
            return migrated_count
        return 0


class AceAssetNumber(models.Model):
    """
    Enhanced asset number tracking - works alongside existing asset_number field
    """
    ace = models.ForeignKey('Ace2', on_delete=models.CASCADE, related_name='enhanced_asset_numbers')
    asset_number = models.CharField(max_length=100, db_index=True)
    asset_register_item = models.ForeignKey(
        'Asset_Register.ZetdcAssets', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Link to asset register if exists"
    )
    # FIXED: Change from 'it.users.UserProfile' to 'users.UserProfile'
    added_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['ace', 'asset_number']
        ordering = ['added_date']
        verbose_name = "Enhanced Asset Number"
        verbose_name_plural = "Enhanced Asset Numbers"
        
    def __str__(self):
        return f"{self.ace.Ace_id2} - {self.asset_number}"
    
    def verify_against_register(self):
        """Check if asset number exists in Asset Register"""
        try:
            from Asset_Register.models import ZetdcAssets
            asset = ZetdcAssets.objects.get(asset_number=self.asset_number)
            self.asset_register_item = asset
            self.is_verified = True
            self.save()
            return asset
        except ZetdcAssets.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error verifying asset {self.asset_number}: {e}")
            return None


class Asset_budget_Virament(models.Model):
    virament_id = models.AutoField(primary_key=True)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, blank=True, null=True)
    from_budget = models.ForeignKey(AssetBudget, on_delete=models.DO_NOTHING, related_name='from_budget')
    to_budget = models.ForeignKey(AssetBudget, on_delete=models.DO_NOTHING, related_name='to_budget')
    amount = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0.01)])
    reason = models.TextField(blank=True, null=True)
    process = models.ForeignKey(Process, on_delete=models.DO_NOTHING, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, blank=True, null=True)
    currency = models.CharField(max_length=15, blank=True, null=True, choices=Ace2.CURRENCY_CHOICES)

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate amount is positive
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be positive.'})
        
        # Validate from_budget != to_budget
        if self.from_budget and self.to_budget and self.from_budget == self.to_budget:
            raise ValidationError({
                'to_budget': 'Source and destination budgets cannot be the same.'
            })
        
        # Validate sufficient available balance considering to_be_withdrawn
        if self.from_budget and self.amount is not None:
            # For existing virements, check if amount changed
            if self.pk:
                try:
                    original = Asset_budget_Virament.objects.get(pk=self.pk)
                    if original.amount != self.amount or original.from_budget != self.from_budget:
                        # Amount or budget changed, validate available balance
                        if self.amount > self.from_budget.available_balance:
                            raise ValidationError({
                                'amount': f'Insufficient available balance in source budget. '
                                         f'Available: {self.from_budget.available_balance:,.2f} '
                                         f'(Balance: {self.from_budget.balance:,.2f}, '
                                         f'To be withdrawn: {self.from_budget.to_be_withdrawn or 0:,.2f})'
                            })
                except Asset_budget_Virament.DoesNotExist:
                    pass
            else:
                # New virement, validate available balance
                if self.amount > self.from_budget.available_balance:
                    raise ValidationError({
                        'amount': f'Insufficient available balance in source budget. '
                                 f'Available: {self.from_budget.available_balance:,.2f} '
                                 f'(Balance: {self.from_budget.balance:,.2f}, '
                                 f'To be withdrawn: {self.from_budget.to_be_withdrawn or 0:,.2f})'
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def release_reserved_amount(self):
        """Release the reserved amount from source budget's to_be_withdrawn field"""
        try:
            if self.from_budget and self.amount:
                budget = AssetBudget.objects.select_for_update().get(
                    budget_id=self.from_budget.budget_id
                )
                if budget.to_be_withdrawn is not None and budget.to_be_withdrawn >= self.amount:
                    budget.to_be_withdrawn -= self.amount
                    budget.save()
                    return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error releasing reserved amount for virement {self.virament_id}: {e}")
        return False

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

    def __str__(self):
        return str(self.transaction_id)


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
