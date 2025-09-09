from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Substation(models.Model):
    """Model for substation information and configuration"""
    
    SUBSTATION_TYPE_CHOICES = [
        ('primary', 'Primary Substation'),
        ('secondary', 'Secondary Substation'),
        ('distribution', 'Distribution Substation'),
        ('transmission', 'Transmission Substation'),
    ]
    
    VOLTAGE_LEVEL_CHOICES = [
        ('11kv', '11kV'),
        ('33kv', '33kV'),
        ('132kv', '132kV'),
        ('400kv', '400kV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substation_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    substation_type = models.CharField(max_length=20, choices=SUBSTATION_TYPE_CHOICES)
    voltage_level = models.CharField(max_length=10, choices=VOLTAGE_LEVEL_CHOICES)
    location = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    
    # Equipment inventory
    transformers_count = models.PositiveIntegerField(default=0)
    circuit_breakers_count = models.PositiveIntegerField(default=0)
    switchgear_count = models.PositiveIntegerField(default=0)
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    last_inspection_date = models.DateField(blank=True, null=True)
    next_scheduled_inspection = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['substation_code']
        verbose_name = 'Substation'
        verbose_name_plural = 'Substations'
    
    def __str__(self):
        return f"{self.substation_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.substation_code:
            self.substation_code = f"SUB-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class MonthlyInspectionSchedule(models.Model):
    """Model for scheduling monthly substation inspections"""
    
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substation = models.ForeignKey(Substation, on_delete=models.CASCADE, related_name='inspection_schedules')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    day_of_month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    assigned_inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Notification settings
    reminder_days_before = models.PositiveIntegerField(default=3)
    escalation_days_after_due = models.PositiveIntegerField(default=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['substation__substation_code', 'day_of_month']
        verbose_name = 'Monthly Inspection Schedule'
        verbose_name_plural = 'Monthly Inspection Schedules'
        unique_together = ['substation', 'frequency', 'day_of_month']
    
    def __str__(self):
        return f"{self.substation.substation_code} - {self.get_frequency_display()} (Day {self.day_of_month})"


class MonthlyInspectionReport(models.Model):
    """Model for monthly substation inspection reports"""
    
    INSPECTION_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    COMPLIANCE_STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('requires_attention', 'Requires Attention'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_number = models.CharField(max_length=50, unique=True)
    substation = models.ForeignKey(Substation, on_delete=models.CASCADE, related_name='monthly_reports')
    inspection_date = models.DateField()
    scheduled_date = models.DateField()
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Weather and environmental conditions
    weather_conditions = models.CharField(max_length=100, blank=True, null=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    humidity = models.PositiveIntegerField(null=True, blank=True)
    
    # Inspection status
    status = models.CharField(max_length=20, choices=INSPECTION_STATUS_CHOICES, default='scheduled')
    compliance_status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS_CHOICES, blank=True, null=True)
    
    # Overall assessment
    overall_condition = models.TextField(blank=True, null=True)
    critical_issues = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    
    # Approvals
    supervisor_approval = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_inspections')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-inspection_date', 'substation__substation_code']
        verbose_name = 'Monthly Inspection Report'
        verbose_name_plural = 'Monthly Inspection Reports'
    
    def __str__(self):
        return f"{self.report_number} - {self.substation.substation_code} - {self.inspection_date}"
    
    def save(self, *args, **kwargs):
        if not self.report_number:
            self.report_number = f"RPT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class InspectionChecklistItem(models.Model):
    """Model for individual inspection checklist items"""
    
    CATEGORY_CHOICES = [
        ('safety', 'Safety'),
        ('electrical', 'Electrical Equipment'),
        ('mechanical', 'Mechanical Equipment'),
        ('environmental', 'Environmental'),
        ('security', 'Security'),
        ('documentation', 'Documentation'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Reference information
    reference_standard = models.CharField(max_length=100, blank=True, null=True)
    frequency = models.CharField(max_length=20, default='monthly')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'item_code']
        verbose_name = 'Inspection Checklist Item'
        verbose_name_plural = 'Inspection Checklist Items'
    
    def __str__(self):
        return f"{self.item_code} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.item_code:
            self.item_code = f"CHK-{self.category.upper()[:3]}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class InspectionItemResponse(models.Model):
    """Model for individual inspection item responses"""
    
    RESPONSE_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable'),
        ('pending', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.ForeignKey(MonthlyInspectionReport, on_delete=models.CASCADE, related_name='item_responses')
    checklist_item = models.ForeignKey(InspectionChecklistItem, on_delete=models.CASCADE)
    
    # Response data
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES)
    observations = models.TextField(blank=True, null=True)
    photos = models.JSONField(default=list, blank=True)  # List of photo URLs/paths
    measurements = models.JSONField(default=dict, blank=True)  # Key-value pairs for measurements
    
    # Defect tracking
    defect_identified = models.BooleanField(default=False)
    defect_description = models.TextField(blank=True, null=True)
    defect_severity = models.CharField(max_length=10, choices=InspectionChecklistItem.SEVERITY_CHOICES, blank=True, null=True)
    corrective_action_required = models.BooleanField(default=False)
    corrective_action_description = models.TextField(blank=True, null=True)
    target_completion_date = models.DateField(blank=True, null=True)
    
    # Timestamps
    checked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['checklist_item__category', 'checklist_item__item_code']
        verbose_name = 'Inspection Item Response'
        verbose_name_plural = 'Inspection Item Responses'
        unique_together = ['inspection_report', 'checklist_item']
    
    def __str__(self):
        return f"{self.inspection_report.report_number} - {self.checklist_item.item_code}"