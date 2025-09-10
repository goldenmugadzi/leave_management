# Create your models here.
# maintenance_app/models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid

class CircuitBreaker(models.Model):
    """Separate model for circuit breaker assets"""
    breaker_number = models.CharField(max_length=50, unique=True, verbose_name="Circuit Breaker No.")
    make_type = models.CharField(max_length=100, verbose_name="Make/Type")
    voltage_capacity = models.CharField(max_length=20, verbose_name="Voltage Capacity")
    serial_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Serial Number")
    installation_date = models.DateField(null=True, blank=True, verbose_name="Installation Date")
    sub_station = models.CharField(max_length=100, verbose_name="Sub-Station")  # Reduced from 255
    region = models.ForeignKey('users.Regions', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Region")
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