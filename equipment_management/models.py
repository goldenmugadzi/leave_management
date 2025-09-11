from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings


class Equipment(models.Model):
    """
    Model representing electrical equipment in the ZESA network
    Based on Form E114 specifications
    """
    EQUIPMENT_TYPES = [
        ('transformer', 'Transformer'),
        ('switchgear', 'Switchgear'),
        ('condenser', 'Condenser'),
        ('panel', 'Panel'),
        ('relay', 'Relay'),
        ('circuit_breaker', 'Circuit Breaker'),
        ('disconnect_switch', 'Disconnect Switch'),
        ('current_transformer', 'Current Transformer'),
        ('voltage_transformer', 'Voltage Transformer'),
        ('capacitor_bank', 'Capacitor Bank'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('removed', 'Removed'),
        ('faulty', 'Faulty'),
        ('maintenance', 'Under Maintenance'),
        ('decommissioned', 'Decommissioned'),
    ]

    equipment_type = models.CharField(
        max_length=100, 
        choices=EQUIPMENT_TYPES,
        help_text="Type of electrical equipment"
    )
    make = models.CharField(
        max_length=100,
        help_text="Manufacturer of the equipment"
    )
    serial_number = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Unique serial number of the equipment"
    )
    kva_rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="KVA rating of the equipment"
    )
    ampere_rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Ampere rating of the equipment"
    )
    voltage_rating = models.CharField(
        max_length=50,
        help_text="Voltage rating (e.g., 11kV, 33kV, 132kV)"
    )
    installation_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when equipment was installed"
    )
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the equipment"
    )
    location_description = models.TextField(
        help_text="Detailed location description"
    )
    substation_name = models.CharField(
        max_length=200,
        help_text="Name of the substation where equipment is located"
    )
    section = models.CharField(
        max_length=100,
        help_text="Section within the substation"
    )
    district = models.CharField(
        max_length=100,
        help_text="District where the equipment is located"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='equipment_created'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment"

    def __str__(self):
        return f"{self.equipment_type} - {self.serial_number} ({self.substation_name})"


class EquipmentOperation(models.Model):
    """
    Model representing equipment operations (Installation/Removal/Change)
    Digital equivalent of Form E114
    """
    OPERATION_TYPES = [
        ('installation', 'New Installation'),
        ('removal', 'Removal of Equipment'),
        ('change', 'Change of Equipment'),
        ('capacity_increase', 'Increase in Capacity'),
        ('capacity_decrease', 'Decrease in Capacity'),
        ('faulty_replacement', 'Faulty Equipment Replacement'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    form_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique form number (E114-YYYY-NNNN)"
    )
    operation_type = models.CharField(
        max_length=50, 
        choices=OPERATION_TYPES,
        help_text="Type of operation being performed"
    )
    consumer_name = models.CharField(
        max_length=200,
        help_text="Name of the consumer/customer"
    )
    consumer_account_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Consumer account number"
    )
    substation_name = models.CharField(
        max_length=200,
        help_text="Name of the substation"
    )
    section = models.CharField(
        max_length=100,
        help_text="Section within the substation"
    )
    district = models.CharField(
        max_length=100,
        help_text="District where operation is taking place"
    )
    equipment_installed = models.ForeignKey(
        Equipment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='installation_operations',
        help_text="Equipment being installed"
    )
    equipment_removed = models.ForeignKey(
        Equipment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='removal_operations',
        help_text="Equipment being removed"
    )
    reason = models.TextField(
        help_text="Detailed reason for the operation"
    )
    operator_name = models.CharField(
        max_length=200,
        help_text="Name of the operator performing the work"
    )
    operator_designation = models.CharField(
        max_length=100,
        help_text="Designation/position of the operator"
    )
    operator_signature = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Digital signature of the operator"
    )
    operation_date = models.DateField(
        default=timezone.now,
        help_text="Date when operation was performed"
    )
    scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled date for the operation"
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date"
    )
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status of the operation"
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium',
        help_text="Priority level of the operation"
    )
    estimated_duration_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated duration in hours"
    )
    actual_duration_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Actual duration in hours"
    )
    cost_estimate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost for the operation"
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual cost of the operation"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='operations_created',
        help_text="User who created this operation record"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='operations_approved',
        help_text="User who approved this operation"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations_reviewed',
        help_text="User who reviewed this operation"
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when operation was approved"
    )
    review_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notes from the review process"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Equipment Operation"
        verbose_name_plural = "Equipment Operations"

    def __str__(self):
        return f"{self.form_number} - {self.operation_type} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.form_number:
            # Auto-generate form number
            year = timezone.now().year
            count = EquipmentOperation.objects.filter(
                created_at__year=year
            ).count() + 1
            self.form_number = f"E114-{year}-{count:04d}"
        super().save(*args, **kwargs)


class OperationDocument(models.Model):
    """
    Model for storing supporting documents for equipment operations
    """
    DOCUMENT_TYPES = [
        ('technical_drawing', 'Technical Drawing'),
        ('specification', 'Equipment Specification'),
        ('compliance_cert', 'Compliance Certificate'),
        ('test_report', 'Test Report'),
        ('installation_photo', 'Installation Photo'),
        ('removal_photo', 'Removal Photo'),
        ('site_survey', 'Site Survey'),
        ('approval_letter', 'Approval Letter'),
        ('other', 'Other'),
    ]

    operation = models.ForeignKey(
        EquipmentOperation, 
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Related equipment operation"
    )
    document_type = models.CharField(
        max_length=100, 
        choices=DOCUMENT_TYPES,
        help_text="Type of document"
    )
    file = models.FileField(
        upload_to='equipment_operations/documents/%Y/%m/',
        help_text="Upload the document file"
    )
    file_name = models.CharField(
        max_length=200,
        help_text="Original file name"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Description of the document"
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="User who uploaded this document"
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Operation Document"
        verbose_name_plural = "Operation Documents"

    def __str__(self):
        return f"{self.operation.form_number} - {self.document_type}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class EquipmentHistory(models.Model):
    """
    Model to track equipment history and changes
    """
    ACTION_TYPES = [
        ('created', 'Equipment Created'),
        ('installed', 'Equipment Installed'),
        ('removed', 'Equipment Removed'),
        ('maintenance', 'Maintenance Performed'),
        ('status_change', 'Status Changed'),
        ('location_change', 'Location Changed'),
        ('specification_change', 'Specification Changed'),
    ]

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Equipment this history record relates to"
    )
    operation = models.ForeignKey(
        EquipmentOperation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related operation (if applicable)"
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )
    action_description = models.TextField(
        help_text="Detailed description of the action"
    )
    old_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Previous values (JSON format)"
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        help_text="New values (JSON format)"
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who performed the action"
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_at']
        verbose_name = "Equipment History"
        verbose_name_plural = "Equipment History"

    def __str__(self):
        return f"{self.equipment} - {self.action_type} ({self.performed_at.date()})"
