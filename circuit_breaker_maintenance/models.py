# Create your models here.
# maintenance_app/models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class CircuitBreaker(models.Model):
    """Separate model for circuit breaker assets"""
    breaker_number = models.CharField(max_length=50, unique=True, verbose_name="Circuit Breaker No.")  # Reduced from 100
    make_type = models.CharField(max_length=100, verbose_name="Make/Type")  # Reduced from 255
    voltage_capacity = models.CharField(max_length=20, verbose_name="Voltage Capacity")  # Reduced from 100
    serial_number = models.CharField(max_length=50, unique=True, verbose_name="Serial Number")  # Reduced from 100
    installation_date = models.DateField(null=True, blank=True, verbose_name="Installation Date")
    sub_station = models.CharField(max_length=100, verbose_name="Sub-Station")  # Reduced from 255
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Circuit Breaker"
        verbose_name_plural = "Circuit Breakers"
        ordering = ['sub_station', 'breaker_number']
        indexes = [
            models.Index(fields=['sub_station']),
            models.Index(fields=['make_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.breaker_number} - {self.sub_station}"

class MaintenanceRecord(models.Model):
    """Enhanced SF6 Circuit Breaker Annual Maintenance record"""
    
    # Status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_no = models.CharField(max_length=50, unique=True, verbose_name="Report No.")  # Reduced from 100
    circuit_breaker = models.ForeignKey(CircuitBreaker, on_delete=models.CASCADE, verbose_name="Circuit Breaker")
    
    # Administrative fields
    date = models.DateField(default=timezone.now, verbose_name="Date of Maintenance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")
    
    # Work permits and authorizations
    permit_to_work_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Permit to Work No.")  # Reduced from 100
    permit_issued_date = models.DateTimeField(null=True, blank=True, verbose_name="Permit Issued Date")
    permit_expires_date = models.DateTimeField(null=True, blank=True, verbose_name="Permit Expires Date")
    sanction_for_test_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sanction for Test No.")  # Reduced from 100
    limitation_of_access_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Limitation of Access No.")  # Reduced from 100
    
    # Operations tracking
    operations_since_last_oh = models.PositiveIntegerField(
        null=True, blank=True, 
        validators=[MinValueValidator(0)],
        verbose_name="Operations Since Last O/H"
    )
    operations_counter_last_oh = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Operations Counter Last O/H"
    )
    operations_counter_to_date = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Operations Counter To Date"
    )
    
    # Previous maintenance reference
    previous_report_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="Previous Report No.")  # Reduced from 100
    previous_report_date = models.DateField(blank=True, null=True, verbose_name="Previous Report Date")
    
    # Environmental conditions
    ambient_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ambient Temperature (°C)"
    )
    humidity = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Humidity (%)"
    )
    # Safety and compliance
    environmental_considerations = models.TextField(blank=True, null=True, verbose_name="Environmental Considerations")
    # Personnel and approvals
    maintenance_carried_out_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Maintenance Carried Out By")  # Reduced from 255
    protection_test_carried_out_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Protection Test Carried Out By")  # Reduced from 255
    # Approval workflow
    checked_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Checked By")  # Reduced from 255
    checked_by_role = models.CharField(max_length=100, blank=True, null=True, verbose_name="Checked By Role")  # Reduced from 255
    checked_date = models.DateTimeField(null=True, blank=True, verbose_name="Checked Date")
    approved_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Approved By")  # Reduced from 255
    approved_by_role = models.CharField(max_length=100, blank=True, null=True, verbose_name="Approved By Role")  # Reduced from 255
    approved_date = models.DateTimeField(null=True, blank=True, verbose_name="Approved Date")
    
    # Documentation
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    recommendations = models.TextField(blank=True, null=True, verbose_name="Recommendations")
    follow_up_required = models.BooleanField(default=False, verbose_name="Follow-up Required")
    follow_up_date = models.DateField(null=True, blank=True, verbose_name="Follow-up Date")
    
    # Next maintenance scheduling
    next_maintenance_due = models.DateField(null=True, blank=True, verbose_name="Next Maintenance Due")
    maintenance_interval_months = models.PositiveIntegerField(
        default=12, 
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Maintenance Interval (Months)"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Created By")  # Reduced from 255
    updated_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Updated By")  # Reduced from 255
    
    class Meta:
        verbose_name = "SF6 Circuit Breaker Maintenance Record"
        verbose_name_plural = "SF6 Circuit Breaker Maintenance Records"
        ordering = ['-date', 'circuit_breaker__breaker_number']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['circuit_breaker', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['priority'])
            # Note: removed report_no from index since it's already unique
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate report number if not provided
        if not self.report_no:
            self.report_no = self.generate_report_number()
        
        # Calculate next maintenance due date
        if self.date and not self.next_maintenance_due:
            try:
                from dateutil.relativedelta import relativedelta
                self.next_maintenance_due = self.date + relativedelta(months=self.maintenance_interval_months)
            except ImportError:
                # Fallback if dateutil is not available
                import datetime
                # Approximate calculation (30 days per month)
                days_to_add = self.maintenance_interval_months * 30
                self.next_maintenance_due = self.date + datetime.timedelta(days=days_to_add)
        
        super().save(*args, **kwargs)
    
    def generate_report_number(self):
        """Generate unique report number"""
        year = timezone.now().year
        count = MaintenanceRecord.objects.filter(date__year=year).count() + 1
        return f"CBM-{year}-{count:04d}"
    
    @property
    def is_overdue(self):
        """Check if maintenance is overdue"""
        if self.next_maintenance_due:
            return timezone.now().date() > self.next_maintenance_due
        return False
    
    @property
    def days_until_due(self):
        """Calculate days until next maintenance is due"""
        if self.next_maintenance_due:
            delta = self.next_maintenance_due - timezone.now().date()
            return delta.days
        return None

    @staticmethod
    def get_default_general_checks():
        return [
            {"item": "Visual inspection of SF6 breaker", "status": False, "comment": ""},
            {"item": "Check for oil leaks", "status": False, "comment": ""},
            {"item": "Check SF6 gas pressure", "status": False, "comment": ""},
            {"item": "Inspect main contacts", "status": False, "comment": ""},
            {"item": "Check auxiliary contacts", "status": False, "comment": ""},
            {"item": "Inspect insulators", "status": False, "comment": ""},
            {"item": "Check control wiring", "status": False, "comment": ""},
        ]

    @staticmethod
    def get_default_test_results():
        return {
            "megger_tests": [],
            "ductor_tests": [],
            "timing_tests": {},
            "contact_travel": [],
            "velocity_tests": [],
            "insulation_resistance": {},
        }

class MaintenanceAttachment(models.Model):
    """File attachments for maintenance records"""
    ATTACHMENT_TYPES = [
        ('photo', 'Photo'),
        ('test_report', 'Test Report'),
        ('certificate', 'Certificate'),
        ('drawing', 'Drawing'),
        ('other', 'Other'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='maintenance_attachments/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='other')
    description = models.CharField(max_length=200, blank=True, null=True)  # Reduced from 255
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=100, blank=True, null=True)  # Reduced from 255
    
    class Meta:
        verbose_name = "Maintenance Attachment"
        verbose_name_plural = "Maintenance Attachments"
        indexes = [
            models.Index(fields=['maintenance_record', 'file_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.get_file_type_display()} for {self.maintenance_record.report_no}"

class MaintenanceTemplate(models.Model):
    """Templates for different types of maintenance checks"""
    name = models.CharField(max_length=100, unique=True)  # Reduced from 255
    description = models.TextField(blank=True, null=True)
    check_items = models.JSONField(default=list, verbose_name="Check Items Template")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Maintenance Template"
        verbose_name_plural = "Maintenance Templates"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name