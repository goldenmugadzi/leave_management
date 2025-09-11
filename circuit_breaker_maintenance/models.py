# Create your models here.
# maintenance_app/models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from it.users.models import Regions
import uuid

class CircuitBreaker(models.Model):
    """Enhanced model for circuit breaker assets supporting different types"""
    
    # Circuit Breaker Types
    BREAKER_TYPES = [
        ('sf6', 'SF6 Circuit Breaker'),
        ('vacuum', 'Vacuum Circuit Breaker'),
        ('oil', 'Oil Circuit Breaker'),
        ('air_blast', 'Air Blast Circuit Breaker'),
        ('minimum_oil', 'Minimum Oil Circuit Breaker'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    breaker_number = models.CharField(max_length=50, unique=True, verbose_name="Circuit Breaker No.")
    breaker_type = models.CharField(max_length=20, choices=BREAKER_TYPES, default='sf6', verbose_name="Breaker Type")
    make_type = models.CharField(max_length=100, verbose_name="Make/Type")
    voltage_capacity = models.CharField(max_length=20, verbose_name="Voltage Capacity")
    current_rating = models.CharField(max_length=20, blank=True, null=True, verbose_name="Current Rating")
    breaking_capacity = models.CharField(max_length=20, blank=True, null=True, verbose_name="Breaking Capacity")
    
    # Technical Specifications
    serial_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Serial Number")
    installation_date = models.DateField(null=True, blank=True, verbose_name="Installation Date")
    sub_station = models.CharField(max_length=100, verbose_name="Sub-Station")
    bay_position = models.CharField(max_length=50, blank=True, null=True, verbose_name="Bay Position")
    
    # V/T and C/T Information (from forms)
    vt_make_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="V/T Make/Type")
    vt_volt_ratio_rating = models.CharField(max_length=50, blank=True, null=True, verbose_name="V/T Volt Ratio Rating")
    vt_serial_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="V/T Serial No.")
    
    ct_make_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="C/T Make/Type")
    ct_ratio = models.CharField(max_length=50, blank=True, null=True, verbose_name="C/T Ratio")
    ct_serial_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="C/T Serial No.")
    
    # Administrative
    region = models.ForeignKey(Regions, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Region")
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
            models.Index(fields=['serial_number']),
            models.Index(fields=['region']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['breaker_number', 'sub_station'],
                name='unique_breaker_per_substation'
            ),
            models.CheckConstraint(
                check=models.Q(voltage_capacity__isnull=False) & ~models.Q(voltage_capacity=''),
                name='voltage_capacity_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(breaker_type__in=['sf6', 'vacuum', 'oil', 'air_blast', 'minimum_oil', 'other']),
                name='valid_breaker_type'
            ),
        ]
    
    def __str__(self):
        return f"{self.breaker_number} - {self.sub_station}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Validate voltage capacity format
        if self.voltage_capacity:
            voltage_str = self.voltage_capacity.strip().upper()
            if not any(unit in voltage_str for unit in ['KV', 'V', 'MV']):
                errors['voltage_capacity'] = 'Voltage capacity must include units (KV, MV, or V)'
        
        # Validate installation date
        if self.installation_date and self.installation_date > timezone.now().date():
            errors['installation_date'] = 'Installation date cannot be in the future'
        
        if errors:
            raise ValidationError(errors)
    
    @property
    def age_years(self):
        """Calculate age of circuit breaker in years"""
        if self.installation_date:
            return (timezone.now().date() - self.installation_date).days // 365
        return None
    
    @property
    def last_maintenance_date(self):
        """Get date of last completed maintenance"""
        last_maintenance = self.maintenancerecord_set.filter(
            status='completed'
        ).order_by('-date').first()
        return last_maintenance.date if last_maintenance else None

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
    previous_report_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="Previous Report No.")
    previous_report_date = models.DateField(blank=True, null=True, verbose_name="Previous Report Date")    # Environmental conditions
    weather_conditions = models.CharField(max_length=100, blank=True, null=True, verbose_name="Weather Conditions")
    ambient_temperature = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="Ambient Temperature (°C)"
    )
    humidity = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Humidity (%)"
    )
    
    # Environmental considerations (keeping as text field for flexibility)
    environmental_considerations = models.TextField(blank=True, null=True, verbose_name="Environmental Considerations")
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
            models.Index(fields=['priority']),
            models.Index(fields=['next_maintenance_due']),
        ]
    
    def __str__(self):
        return f"Report {self.report_no} for CB {self.circuit_breaker.breaker_number} on {self.date}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Validate permit dates
        if self.permit_issued_date and self.permit_expires_date:
            if self.permit_issued_date >= self.permit_expires_date:
                errors['permit_expires_date'] = 'Permit expiry date must be after issued date'
        
        # Validate maintenance date
        if self.date > timezone.now().date():
            errors['date'] = 'Maintenance date cannot be in the future'
        
        # Validate follow-up date
        if self.follow_up_required and not self.follow_up_date:
            errors['follow_up_date'] = 'Follow-up date is required when follow-up is needed'
        
        if self.follow_up_date and self.follow_up_date <= self.date:
            errors['follow_up_date'] = 'Follow-up date must be after maintenance date'
        
        # Validate operations counters
        if (self.operations_counter_last_oh is not None and 
            self.operations_counter_to_date is not None and
            self.operations_counter_to_date < self.operations_counter_last_oh):
            errors['operations_counter_to_date'] = 'Current operations counter cannot be less than last overhaul counter'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Auto-generate report number if not provided
        if not self.report_no:
            self.report_no = self.generate_report_number()
        
        # Calculate next maintenance due date
        if self.date and not self.next_maintenance_due:
            import datetime
            # Calculate next maintenance date (approximate: 30 days per month)
            days_to_add = self.maintenance_interval_months * 30
            self.next_maintenance_due = self.date + datetime.timedelta(days=days_to_add)
        
        super().save(*args, **kwargs)
    
    def generate_report_number(self):
        """Generate unique report number with race condition protection"""
        from django.db import transaction
        
        year = timezone.now().year
        with transaction.atomic():
            # Get the highest existing report number for this year
            last_record = MaintenanceRecord.objects.filter(
                report_no__startswith=f"CBM-{year}-"
            ).order_by('-report_no').first()
            
            if last_record:
                # Extract the counter from the last report number
                try:
                    last_counter = int(last_record.report_no.split('-')[-1])
                    counter = last_counter + 1
                except (ValueError, IndexError):
                    # Fallback if report number format is unexpected
                    counter = MaintenanceRecord.objects.filter(date__year=year).count() + 1
            else:
                counter = 1
            
            return f"CBM-{year}-{counter:04d}"
    
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
    
    @property
    def can_be_edited(self):
        """Check if record can be edited based on status"""
        return self.status in ['draft', 'in_progress']
    
    @property
    def duration_days(self):
        """Calculate duration of maintenance in days"""
        if self.date and self.updated_at:
            return (self.updated_at.date() - self.date).days
        return 0

    @staticmethod
    def get_default_general_checks():
        """Get default check items for general maintenance"""
        return [
            "Visual inspection of SF6 breaker",
            "Check for oil leaks",
            "Check SF6 gas pressure",
            "Inspect main contacts",
            "Check auxiliary contacts", 
            "Inspect insulators",
            "Check control wiring",
        ]

    @staticmethod
    def get_default_mechanism_checks():
        """Get default check items for mechanism maintenance"""
        return [
            "Check operating mechanism",
            "Inspect spring charge motor",
            "Check mechanical interlocks",
            "Verify closing/opening times",
            "Check contact travel",
        ]

    @staticmethod
    def get_default_ct_checks():
        """Get default check items for C/T maintenance"""
        return [
            "Check current transformer connections",
            "Verify CT ratio",
            "Inspect CT secondary circuits",
            "Check CT insulation",
        ]

    @staticmethod
    def get_default_vt_checks():
        """Get default check items for V/T maintenance"""
        return [
            "Check voltage transformer connections",
            "Verify VT ratio",
            "Inspect VT secondary circuits",
            "Check VT insulation",
        ]

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

class EquipmentDetail(models.Model):
    """Equipment details for circuit breakers"""
    circuit_breaker = models.OneToOneField(CircuitBreaker, on_delete=models.CASCADE, related_name='equipment_detail')
    
    # SF6 Gas System
    sf6_gas_pressure_bar = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="SF6 Gas Pressure (bar)")
    sf6_gas_density = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True, verbose_name="SF6 Gas Density")
    gas_leakage_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True, verbose_name="Gas Leakage Rate (%/year)")
    
    # Contact System
    contact_material = models.CharField(max_length=50, blank=True, null=True, verbose_name="Contact Material")
    contact_erosion_mm = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name="Contact Erosion (mm)")
    arcing_contacts_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('replace', 'Needs Replacement')
    ], blank=True, null=True, verbose_name="Arcing Contacts Condition")
    
    # Mechanical System
    operating_mechanism_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Operating Mechanism Type")
    spring_charge_motor_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], blank=True, null=True, verbose_name="Spring Charge Motor Condition")
    
    # Insulation System
    insulator_material = models.CharField(max_length=50, blank=True, null=True, verbose_name="Insulator Material")
    insulator_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], blank=True, null=True, verbose_name="Insulator Condition")
    
    # Control System
    control_voltage = models.CharField(max_length=20, blank=True, null=True, verbose_name="Control Voltage")
    auxiliary_contacts_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Number of Auxiliary Contacts")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Equipment Detail"
        verbose_name_plural = "Equipment Details"
    
    def __str__(self):
        return f"Equipment details for {self.circuit_breaker.breaker_number}"

class MaintenanceCheckItem(models.Model):
    """Individual maintenance check items"""
    CHECK_CATEGORIES = [
        ('general', 'General Checks'),
        ('mechanism', 'Mechanism Checks'),
        ('ct', 'C/T Checks'),
        ('vt', 'V/T Checks'),
        ('safety', 'Safety Checks'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('na', 'Not Applicable'),
        ('failed', 'Failed'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='check_items')
    category = models.CharField(max_length=20, choices=CHECK_CATEGORIES, verbose_name="Check Category")
    item_name = models.CharField(max_length=200, verbose_name="Check Item")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name="Status")
    is_critical = models.BooleanField(default=False, verbose_name="Critical Item")
    
    # Results
    result_passed = models.BooleanField(null=True, blank=True, verbose_name="Passed")
    measured_value = models.CharField(max_length=100, blank=True, null=True, verbose_name="Measured Value")
    expected_value = models.CharField(max_length=100, blank=True, null=True, verbose_name="Expected Value")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    # Personnel
    checked_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Checked By")
    checked_date = models.DateTimeField(null=True, blank=True, verbose_name="Checked Date")
    
    # Order for display
    order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    
    class Meta:
        verbose_name = "Maintenance Check Item"
        verbose_name_plural = "Maintenance Check Items"
        ordering = ['category', 'order', 'item_name']
        indexes = [
            models.Index(fields=['maintenance_record', 'category']),
            models.Index(fields=['status']),
            models.Index(fields=['is_critical']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.maintenance_record.report_no}"

class TestResult(models.Model):
    """Individual test results"""
    TEST_TYPES = [
        ('insulation_resistance', 'Insulation Resistance'),
        ('contact_resistance', 'Contact Resistance'),
        ('timing_test', 'Timing Test'),
        ('travel_test', 'Contact Travel'),
        ('velocity_test', 'Contact Velocity'),
        ('sf6_gas_analysis', 'SF6 Gas Analysis'),
        ('partial_discharge', 'Partial Discharge'),
        ('power_factor', 'Power Factor'),
        ('other', 'Other'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='test_results_detail')
    test_type = models.CharField(max_length=30, choices=TEST_TYPES, verbose_name="Test Type")
    test_name = models.CharField(max_length=200, verbose_name="Test Name")
    
    # Test conditions
    test_voltage = models.CharField(max_length=50, blank=True, null=True, verbose_name="Test Voltage")
    test_frequency = models.CharField(max_length=50, blank=True, null=True, verbose_name="Test Frequency")
    ambient_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Ambient Temperature (°C)")
    
    # Results
    measured_value = models.CharField(max_length=100, verbose_name="Measured Value")
    unit = models.CharField(max_length=20, blank=True, null=True, verbose_name="Unit")
    acceptable_range = models.CharField(max_length=100, blank=True, null=True, verbose_name="Acceptable Range")
    result_status = models.CharField(max_length=20, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning'),
        ('info', 'Information Only')
    ], verbose_name="Result Status")
    
    # Documentation
    test_procedure = models.TextField(blank=True, null=True, verbose_name="Test Procedure")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    test_equipment_used = models.CharField(max_length=200, blank=True, null=True, verbose_name="Test Equipment Used")
    
    # Personnel
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    
    # Order for display
    order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    
    class Meta:
        verbose_name = "Test Result"
        verbose_name_plural = "Test Results"
        ordering = ['test_type', 'order', 'test_name']
        indexes = [
            models.Index(fields=['maintenance_record', 'test_type']),
            models.Index(fields=['result_status']),
            models.Index(fields=['test_date']),
        ]
    
    def __str__(self):
        return f"{self.test_name} - {self.maintenance_record.report_no}"

class MaintenanceTeamMember(models.Model):
    """Team members involved in maintenance"""
    ROLE_CHOICES = [
        ('lead_technician', 'Lead Technician'),
        ('technician', 'Technician'),
        ('engineer', 'Engineer'),
        ('supervisor', 'Supervisor'),
        ('safety_officer', 'Safety Officer'),
        ('apprentice', 'Apprentice'),
        ('contractor', 'Contractor'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=100, verbose_name="Name")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Role")
    employee_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Employee ID")
    certification_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Certification Number")
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Hours Worked")
    
    class Meta:
        verbose_name = "Maintenance Team Member"
        verbose_name_plural = "Maintenance Team Members"
        unique_together = ['maintenance_record', 'name', 'role']
        indexes = [
            models.Index(fields=['maintenance_record', 'role']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.role}) - {self.maintenance_record.report_no}"

class SafetyPrecaution(models.Model):
    """Safety precautions taken during maintenance"""
    PRECAUTION_TYPES = [
        ('isolation', 'Electrical Isolation'),
        ('lockout', 'Lockout/Tagout'),
        ('ppe', 'Personal Protective Equipment'),
        ('gas_monitoring', 'Gas Monitoring'),
        ('confined_space', 'Confined Space'),
        ('lifting', 'Lifting Operations'),
        ('environmental', 'Environmental Protection'),
        ('other', 'Other'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='safety_precautions_detail')
    precaution_type = models.CharField(max_length=20, choices=PRECAUTION_TYPES, verbose_name="Precaution Type")
    description = models.CharField(max_length=200, verbose_name="Description")
    is_mandatory = models.BooleanField(default=True, verbose_name="Mandatory")
    is_completed = models.BooleanField(default=False, verbose_name="Completed")
    completed_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Completed By")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Completed Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Safety Precaution"
        verbose_name_plural = "Safety Precautions"
        indexes = [
            models.Index(fields=['maintenance_record', 'precaution_type']),
            models.Index(fields=['is_mandatory', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.maintenance_record.report_no}"

class InsulationResistanceTest(models.Model):
    """Insulation Resistance Tests (Megger Tests) - From the forms"""
    PHASE_CHOICES = [
        ('red', 'Red Phase'),
        ('yellow', 'Yellow Phase'),
        ('blue', 'Blue Phase'),
    ]
    
    TEST_TYPES = [
        ('open_contact', 'Open Contact'),
        ('top_e', 'Top-E'),
        ('bottom_e', 'Bottom-E'),
        ('phase_next', 'Phase-Next'),
        ('before_maintenance', 'Before Maintenance'),
        ('after_maintenance', 'After Maintenance'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='insulation_tests')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, verbose_name="Phase")
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, verbose_name="Test Type")
    resistance_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Resistance (MΩ)")
    test_voltage = models.CharField(max_length=20, blank=True, null=True, verbose_name="Test Voltage")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Temperature (°C)")
    humidity = models.PositiveIntegerField(null=True, blank=True, verbose_name="Humidity (%)")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Insulation Resistance Test"
        verbose_name_plural = "Insulation Resistance Tests"
        unique_together = ['maintenance_record', 'phase', 'test_type']
        indexes = [
            models.Index(fields=['maintenance_record', 'phase']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.phase} {self.test_type} - {self.maintenance_record.report_no}"

class ContactResistanceTest(models.Model):
    """Contact Resistance Tests - From the forms"""
    PHASE_CHOICES = [
        ('red', 'Red Phase'),
        ('yellow', 'Yellow Phase'), 
        ('blue', 'Blue Phase'),
    ]
    
    TEST_CONDITIONS = [
        ('before_maintenance', 'Before Maintenance'),
        ('after_maintenance', 'After Maintenance'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='contact_resistance_tests')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, verbose_name="Phase")
    test_condition = models.CharField(max_length=20, choices=TEST_CONDITIONS, verbose_name="Test Condition")
    resistance_microohms = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Resistance (μΩ)")
    test_current = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Test Current (A)")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Temperature (°C)")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Contact Resistance Test"
        verbose_name_plural = "Contact Resistance Tests"
        unique_together = ['maintenance_record', 'phase', 'test_condition']
        indexes = [
            models.Index(fields=['maintenance_record', 'phase']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.phase} {self.test_condition} - {self.maintenance_record.report_no}"

class TimingTest(models.Model):
    """Timing Tests - From the forms"""
    PHASE_CHOICES = [
        ('red', 'Red Phase'),
        ('yellow', 'Yellow Phase'),
        ('blue', 'Blue Phase'),
    ]
    
    OPERATION_TYPES = [
        ('closing', 'Closing Operation'),
        ('opening', 'Opening Operation'),
        ('close_open', 'Close-Open Operation'),
        ('open_close_open', 'Open-Close-Open Operation'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='timing_tests')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, verbose_name="Phase")
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES, verbose_name="Operation Type")
    
    # Multiple operation phases for complex operations
    phu1_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Phu1 Time (ms)")
    phu2_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Phu2 Time (ms)")
    operation_1_close_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="1st Operation Close (ms)")
    operation_2_open_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="2nd Operation Open (ms)")
    operation_3_close_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="3rd Operation Close (ms)")
    repeat_1st_operation = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Repeat 1st Operation (ms)")
    repeat_2nd_operation = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Repeat 2nd Operation (ms)")
    
    # Overall results
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Timing Test"
        verbose_name_plural = "Timing Tests"
        unique_together = ['maintenance_record', 'phase', 'operation_type']
        indexes = [
            models.Index(fields=['maintenance_record', 'phase']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.phase} {self.operation_type} - {self.maintenance_record.report_no}"

class InterlockTest(models.Model):
    """Interlock Tests - From the forms"""
    INTERLOCK_TYPES = [
        ('hv_cb', 'HV CB'),
        ('lv_cb', 'LV CB'), 
        ('oltc', 'OLTC'),
        ('mechanical', 'Mechanical Interlock'),
        ('electrical', 'Electrical Interlock'),
        ('remote_local', 'Remote/Local Operation'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='interlock_tests')
    interlock_type = models.CharField(max_length=20, choices=INTERLOCK_TYPES, verbose_name="Interlock Type")
    description = models.CharField(max_length=200, verbose_name="Test Description")
    is_checked = models.BooleanField(default=False, verbose_name="Checked")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Interlock Test"
        verbose_name_plural = "Interlock Tests"
        indexes = [
            models.Index(fields=['maintenance_record', 'interlock_type']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.interlock_type} - {self.maintenance_record.report_no}"

class ContactTravelTest(models.Model):
    """Contact Travel and Velocity Tests - From the forms"""
    PHASE_CHOICES = [
        ('red', 'Red Phase'),
        ('yellow', 'Yellow Phase'),
        ('blue', 'Blue Phase'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='contact_travel_tests')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, verbose_name="Phase")
    contact_travel_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Contact Travel (mm)")
    velocity_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Velocity (m/s)")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Contact Travel Test"
        verbose_name_plural = "Contact Travel Tests"
        unique_together = ['maintenance_record', 'phase']
        indexes = [
            models.Index(fields=['maintenance_record', 'phase']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.phase} Contact Travel - {self.maintenance_record.report_no}"

class DuctorTest(models.Model):
    """Ductor Tests (Low Resistance Tests) - From the forms"""
    PHASE_CHOICES = [
        ('red', 'Red Phase'),
        ('yellow', 'Yellow Phase'),
        ('blue', 'Blue Phase'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='ductor_tests')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, verbose_name="Phase")
    current_amps = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Current (A)")
    volt_drop_mv = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Volt Drop (mV)")
    resistance_microohms = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Resistance (μΩ)")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Ductor Test"
        verbose_name_plural = "Ductor Tests"
        unique_together = ['maintenance_record', 'phase']
        indexes = [
            models.Index(fields=['maintenance_record', 'phase']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.phase} Ductor Test - {self.maintenance_record.report_no}"

class ProtectionTest(models.Model):
    """Protection System Tests - From the forms"""
    PROTECTION_TYPES = [
        ('overcurrent_r', 'O/C R'),
        ('overcurrent_y', 'O/C Y'),
        ('overcurrent_b', 'O/C B'),
        ('earth_fault', 'E'),
        ('instantaneous_r', 'INST R'),
        ('instantaneous_y', 'INST Y'),
        ('instantaneous_b', 'INST B'),
        ('distance_protection_r', 'Distance Protection R'),
        ('distance_protection_y', 'Distance Protection Y'),
        ('distance_protection_b', 'Distance Protection B'),
        ('vt_fail', 'V/T Fail'),
        ('dc_fail', 'DC Fail'),
        ('springs_discharged', 'Springs Discharged'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='protection_tests')
    protection_type = models.CharField(max_length=30, choices=PROTECTION_TYPES, verbose_name="Protection Type")
    action_taken = models.CharField(max_length=200, blank=True, null=True, verbose_name="Action Taken")
    alarm_status = models.BooleanField(null=True, blank=True, verbose_name="Alarm")
    trip_status = models.BooleanField(null=True, blank=True, verbose_name="Trip")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Protection Test"
        verbose_name_plural = "Protection Tests"
        unique_together = ['maintenance_record', 'protection_type']
        indexes = [
            models.Index(fields=['maintenance_record', 'protection_type']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.protection_type} - {self.maintenance_record.report_no}"

class RelayOperationTest(models.Model):
    """Relay Operation Tests - From the forms"""
    RELAY_TYPES = [
        ('distance_protection_annunciate', 'Distance Protection Annunciate'),
        ('j_relay_auto_trip_vt_dc', 'J Relay Auto Trip VT/DC'),
        ('distance_repeat', 'Distance Repeat'),
        ('trip_relay', 'Trip Relay'),
        ('master_trip_relay', 'Master Trip Relay'),
        ('time_delay_relay', 'Time Delay Relay'),
        ('transformer_alarm_relay', 'Transformer Alarm Relay'),
        ('alarm_repeat_relay', 'Alarm Repeat Relay'),
        ('all_relays_reset_correctly', 'All Relays Reset Correctly'),
        ('discrepancy_trip_correct', 'Discrepancy Trip Correct'),
    ]
    
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='relay_operation_tests')
    relay_type = models.CharField(max_length=40, choices=RELAY_TYPES, verbose_name="Relay Type")
    action_taken = models.CharField(max_length=200, blank=True, null=True, verbose_name="Action Taken")
    alarm_status = models.BooleanField(null=True, blank=True, verbose_name="Alarm")
    trip_status = models.BooleanField(null=True, blank=True, verbose_name="Trip")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Relay Operation Test"
        verbose_name_plural = "Relay Operation Tests"
        unique_together = ['maintenance_record', 'relay_type']
        indexes = [
            models.Index(fields=['maintenance_record', 'relay_type']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.relay_type} - {self.maintenance_record.report_no}"

class AutoRecloseTest(models.Model):
    """Auto Reclose Tests - From the forms"""
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='auto_reclose_tests')
    reclose_operation_correct = models.BooleanField(null=True, blank=True, verbose_name="Reclose Operation Correct")
    lockout_operation_correct = models.BooleanField(null=True, blank=True, verbose_name="Lockout Operation Correct")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable')
    ], default='pass', verbose_name="Result Status")
    tested_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tested By")
    test_date = models.DateTimeField(null=True, blank=True, verbose_name="Test Date")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    
    class Meta:
        verbose_name = "Auto Reclose Test"
        verbose_name_plural = "Auto Reclose Tests"
        indexes = [
            models.Index(fields=['maintenance_record']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"Auto Reclose Test - {self.maintenance_record.report_no}"

class VacuumBreakerChecks(models.Model):
    """Vacuum Circuit Breaker Specific Checks - From the Vacuum CB form"""
    maintenance_record = models.OneToOneField(MaintenanceRecord, on_delete=models.CASCADE, related_name='vacuum_checks')
    
    # Gearing checks
    gearing_checked = models.BooleanField(default=False, verbose_name="Gearing Checked")
    lubrication_checked = models.BooleanField(default=False, verbose_name="Lubrication Checked")
    auxiliary_contacts_checked = models.BooleanField(default=False, verbose_name="Auxiliary Contacts Checked")
    motor_checked = models.BooleanField(default=False, verbose_name="Motor Checked")
    springs_close_open_checked = models.BooleanField(default=False, verbose_name="Springs (Close/Open) Checked")
    cb_insulators_checked = models.BooleanField(default=False, verbose_name="C/B Insulators Checked")
    cts_checked = models.BooleanField(default=False, verbose_name="CTS Checked")
    porcelain_checked = models.BooleanField(default=False, verbose_name="Porcelain Checked")
    local_remote_operation_checked = models.BooleanField(default=False, verbose_name="Local/Remote Operation Checked")
    vacuum_check_performed = models.BooleanField(default=False, verbose_name="Vacuum Check Performed")
    
    # Ductor Tests - Three phases
    red_phase_ductor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Red Phase Ductor")
    yellow_phase_ductor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Yellow Phase Ductor")
    blue_phase_ductor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Blue Phase Ductor")
    
    # Additional vacuum-specific checks
    vacuum_level_satisfactory = models.BooleanField(default=False, verbose_name="Vacuum Level Satisfactory")
    contacts_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('replace', 'Needs Replacement')
    ], blank=True, null=True, verbose_name="Contacts Condition")
    
    # Timing tests specific data
    timing_tests_attached = models.BooleanField(default=False, verbose_name="Timing Tests - See Attached Results")
    
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments")
    
    class Meta:
        verbose_name = "Vacuum Breaker Checks"
        verbose_name_plural = "Vacuum Breaker Checks"
    
    def __str__(self):
        return f"Vacuum CB Checks - {self.maintenance_record.report_no}"

class OilBreakerChecks(models.Model):
    """Oil Circuit Breaker Specific Checks - From the Oil CB form"""
    maintenance_record = models.OneToOneField(MaintenanceRecord, on_delete=models.CASCADE, related_name='oil_checks')
    
    # Basic oil checks
    oil_level_checked = models.BooleanField(default=False, verbose_name="Oil Level Checked")
    oil_quality_checked = models.BooleanField(default=False, verbose_name="Oil Quality Checked")
    oil_leakage_checked = models.BooleanField(default=False, verbose_name="Oil Leakage Checked")
    
    # Oil condition assessment
    oil_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('replace', 'Needs Replacement')
    ], blank=True, null=True, verbose_name="Oil Condition")
    
    oil_dielectric_strength = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Oil Dielectric Strength (kV)")
    oil_moisture_content = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Oil Moisture Content (ppm)")
    oil_acidity = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, verbose_name="Oil Acidity (mg KOH/g)")
    
    # Mechanical checks
    contacts_inspection = models.BooleanField(default=False, verbose_name="Contacts Inspection")
    arcing_contacts_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('replace', 'Needs Replacement')
    ], blank=True, null=True, verbose_name="Arcing Contacts Condition")
    
    # Tank and sealing
    tank_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], blank=True, null=True, verbose_name="Tank Condition")
    
    gasket_seals_condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('replace', 'Needs Replacement')
    ], blank=True, null=True, verbose_name="Gasket/Seals Condition")
    
    # Oil analysis results
    oil_analysis_required = models.BooleanField(default=False, verbose_name="Oil Analysis Required")
    oil_analysis_date = models.DateField(null=True, blank=True, verbose_name="Oil Analysis Date")
    oil_analysis_results = models.TextField(blank=True, null=True, verbose_name="Oil Analysis Results")
    
    comments = models.TextField(blank=True, null=True, verbose_name="Additional Comments")
    
    class Meta:
        verbose_name = "Oil Breaker Checks"
        verbose_name_plural = "Oil Breaker Checks"
    
    def __str__(self):
        return f"Oil CB Checks - {self.maintenance_record.report_no}"

class TransformerMaintenanceRecord(models.Model):
    """Transformer Annual Maintenance Record - From the transformer forms"""
    
    # Status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_no = models.CharField(max_length=50, unique=True, verbose_name="Report No.")
    
    # Transformer details
    substation = models.CharField(max_length=100, verbose_name="Substation")
    transformer_number = models.CharField(max_length=50, verbose_name="Transformer Number")
    make_manufacturer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Make/Manufacturer")
    serial_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="Serial No.")
    rating_mva = models.CharField(max_length=20, blank=True, null=True, verbose_name="Rating (MVA)")
    voltage_ratio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Voltage Ratio")
    year_of_manufacture = models.PositiveIntegerField(null=True, blank=True, verbose_name="Year of Manufacture")
    
    # Administrative
    date = models.DateField(default=timezone.now, verbose_name="Date of Maintenance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Status")
    
    # Maintenance carried out by
    maintenance_carried_out_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Maintenance Carried Out By")
    protection_test_carried_out_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Protection Test Carried Out By")
    checked_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Checked By")
    engineer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Engineer")
    ops_and_maint_engineer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ops and Maint Engineer")
    
    # Dates
    maintenance_date = models.DateField(null=True, blank=True, verbose_name="Maintenance Date")
    protection_test_date = models.DateField(null=True, blank=True, verbose_name="Protection Test Date")
    checked_date = models.DateField(null=True, blank=True, verbose_name="Checked Date")
    engineer_date = models.DateField(null=True, blank=True, verbose_name="Engineer Date")
    ops_maint_date = models.DateField(null=True, blank=True, verbose_name="Ops and Maint Date")
    
    # Remarks
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transformer Maintenance Record"
        verbose_name_plural = "Transformer Maintenance Records"
        ordering = ['-date', 'transformer_number']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['substation', 'transformer_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Report {self.report_no} for Transformer {self.transformer_number} on {self.date}"

class TransformerCheckItem(models.Model):
    """Individual maintenance check items for transformers"""
    TRANSFORMER_CHECK_CATEGORIES = [
        ('visual_inspection', 'Visual Inspection'),
        ('cooling_system', 'Cooling System'),
        ('protection_system', 'Protection System'),
        ('electrical_tests', 'Electrical Tests'),
        ('oil_analysis', 'Oil Analysis'),
        ('buchholz_relay', 'Buchholz Relay'),
        ('tap_changer', 'Tap Changer'),
        ('bushings', 'Bushings'),
        ('general', 'General'),
    ]
    
    # Pre-defined check items based on the form
    PREDEFINED_CHECKS = [
        ('warn_control_of_earthing_operations', 'Warn control of earthing operations and'),
        ('isolation_assemble_earthing', 'Isolation, assemble earthing'),
        ('examine_all_external_accessories', 'Examine all external accessories,'),
        ('service_and_test_protection_ac', 'Service and test protection a.c. main billing'),
        ('check_winding_to_earth_lv_ct_and_lv_ct', 'Check winding to earth LV CT and LV CT'),
        ('examine_all_main_lv_omg_injection_covers', 'Examine all main LV omg, injection covers'),
        ('etc', 'etc.'),
        ('examine_at_main_lv_omg_injection_covers', 'Examine at main LV omg, injection covers'),
        ('examine_and_clean_it_bushings_check', 'Examine and clean it bushings, check'),
        ('examine_and_clean_lv_bushings_check', 'Examine and clean LV bushings, check'),
        ('examine_and_clean_hv_bushing_check', 'Examine and clean HV bushing, check'),
        ('hv_winding_to_earth', 'HV winding to earth'),
        ('lv_winding_to_earth', 'LV winding to earth'),
        ('hv_winding_to_lv_winding', 'HV winding to LV winding'),
        ('tap_changer_alarm', 'Tap changer alarm'),
        ('temp_winding_temp_alarm', 'Temp Winding Temp alarm'),
        ('uv_winding_temp_alarm', 'UV Winding Temp alarm'),
        ('temp_winding_trip', 'Temp Winding Trip'),
        ('uv_winding_trip', 'UV Winding Trip'),
        ('top_oil_temp_alarm', 'Top Oil Temp Alarm'),
        ('temp_winding_temp_alarm', 'Temp Winding Temp alarm'),
        ('uv_cooler_control', 'UV Cooler control'),
        ('hv_cooler_control', 'HV Cooler control'),
        ('top_oil_temp_alarm', 'Top Oil Temp Alarm'),
        ('main_buchholz_trip', 'Main Buchholz Trip'),
        ('cable_oil_pressure_abnormal', 'Cable Oil pressure abnormal'),
    ]
    
    transformer_record = models.ForeignKey(TransformerMaintenanceRecord, on_delete=models.CASCADE, related_name='check_items')
    category = models.CharField(max_length=30, choices=TRANSFORMER_CHECK_CATEGORIES, verbose_name="Check Category")
    item_name = models.CharField(max_length=200, verbose_name="Check Item")
    is_completed = models.BooleanField(default=False, verbose_name="Completed")
    result_status = models.CharField(max_length=10, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable')
    ], default='pass', verbose_name="Result Status")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")
    checked_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Checked By")
    checked_date = models.DateTimeField(null=True, blank=True, verbose_name="Checked Date")
    
    # Order for display
    order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    
    class Meta:
        verbose_name = "Transformer Check Item"
        verbose_name_plural = "Transformer Check Items"
        ordering = ['category', 'order', 'item_name']
        indexes = [
            models.Index(fields=['transformer_record', 'category']),
            models.Index(fields=['result_status']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.transformer_record.report_no}"