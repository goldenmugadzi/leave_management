from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.utils import timezone
import uuid


class Customer(models.Model):
    """
    Model for customer information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=50, unique=True, blank=True)
    
    # Personal Information
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Address Information
    stand_plot_number = models.CharField(max_length=100, blank=True, null=True)
    farm_street_name = models.CharField(max_length=255, blank=True, null=True)
    suburb_township = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.customer_id} - {self.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = f"CUST-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class Contractor(models.Model):
    """
    Model for contractor information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor_id = models.CharField(max_length=50, unique=True, blank=True)
    
    # Business Information
    business_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Address Information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    
    # License and Registration
    license_number = models.CharField(max_length=100, blank=True, null=True)
    business_registration = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contractor'
        verbose_name_plural = 'Contractors'
    
    def __str__(self):
        return f"{self.contractor_id} - {self.business_name}"
    
    def save(self, *args, **kwargs):
        if not self.contractor_id:
            self.contractor_id = f"CONT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class ApplicationAttachment(models.Model):
    """
    Model for application attachments
    """
    ATTACHMENT_TYPE_CHOICES = [
        ('E21', 'E21'),
        ('E22', 'E22'),
        ('E25', 'E25'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey('ClientApplication', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='uploads/applications/')
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Application Attachment'
        verbose_name_plural = 'Application Attachments'
    
    def __str__(self):
        return f"{self.application.application_number} - {self.get_file_type_display()}"


class ClientApplication(models.Model):
    """
    Enhanced model for client applications submitted for electrical inspections
    Based on the application form requirements
    """
    
    APPLICATION_TYPE_CHOICES = [
        ('new_installation', 'New Installation'),
        ('statutory_inspection', 'Statutory Inspection'),
        ('change_of_tenancy', 'Change of Tenancy'),
        ('reconnection', 'Reconnection'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    PURPOSE_CHOICES = [
        ('domestic', 'Domestic'),
        ('commercial', 'Commercial'),
        ('agricultural', 'Agricultural'),
        ('public_lighting', 'Public Lighting'),
        ('industrial', 'Industrial'),
    ]
    
    SUPPLY_TYPE_CHOICES = [
        ('permanent', 'Permanent'),
        ('temporary', 'Temporary'),
    ]
    
    ROOF_COVERING_CHOICES = [
        ('metal_sheeting', 'Metal Sheeting'),
        ('tile_asbestos', 'Tile/Asbestos'),
        ('thatch', 'Thatch'),
    ]
    
    SERVICE_FEED_CHOICES = [
        ('overhead', 'Overhead'),
        ('underground', 'Underground'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Application Information
    application_number = models.CharField(max_length=50, unique=True)
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Customer Information (Enhanced)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='applications')
    
    # Property Owner Information (if different from applicant)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    owner_address = models.TextField(blank=True, null=True)
    
    # Contractor Information (Enhanced)
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, related_name='applications')
    
    # Electrical Supply Details
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    supply_type = models.CharField(max_length=15, choices=SUPPLY_TYPE_CHOICES)
    roof_covering = models.CharField(max_length=20, choices=ROOF_COVERING_CHOICES, blank=True, null=True)
    
    # Supply Particulars
    single_phase_required = models.BooleanField(default=False)
    single_phase_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    three_phase_required = models.BooleanField(default=False)
    three_phase_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    service_feed_type = models.CharField(max_length=15, choices=SERVICE_FEED_CHOICES, blank=True, null=True)
    
    # Main Switch Details
    main_switch_size_amperes = models.PositiveIntegerField(blank=True, null=True)
    main_switch_size_kva = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Application Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='submitted')
    
    # Client Liaison Information
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='submitted_applications'
    )
    submission_date = models.DateTimeField(default=timezone.now)
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client Application'
        verbose_name_plural = 'Client Applications'
    
    def __str__(self):
        return f"{self.application_number} - {self.customer.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # Auto-generate application number if not provided
            self.application_number = f"APP-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class InspectionReport(models.Model):
    """
    Enhanced model for electrical inspection reports (E117)
    Includes all 33 inspection items from the E117 form
    """
    
    INSTALLATION_TYPE_CHOICES = [
        ('domestic', 'Domestic'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
    ]
    
    CONSUMER_UNIT_TYPE_CHOICES = [
        ('metal', 'Metal'),
        ('plastic', 'Plastic'),
        ('other', 'Other'),
    ]
    
    DB_ENCLOSURE_TYPE_CHOICES = [
        ('ip20', 'IP20'),
        ('ip30', 'IP30'),
        ('ip40', 'IP40'),
        ('ip50', 'IP50'),
        ('ip54', 'IP54'),
        ('ip65', 'IP65'),
    ]
    
    CONDUIT_MATERIAL_CHOICES = [
        ('pvc', 'PVC'),
        ('steel', 'Steel'),
        ('aluminum', 'Aluminum'),
        ('flexible', 'Flexible'),
    ]
    
    COMPLIANCE_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable'),
    ]
    
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('pending', 'Pending'),
    ]
    
    REASON_CHOICES = [
        ('new_installation', 'New Installation'),
        ('routine', 'Routine'),
        ('change_of_tenancy', 'Change of Tenancy'),
    ]
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information (E117 Header)
    inspection_date = models.DateField(blank=True, null=True)
    service_no = models.CharField(max_length=50, blank=True, null=True)
    reason_for_inspection = models.CharField(max_length=20, choices=REASON_CHOICES, blank=True, null=True)
    
    # Item 1-3: General Information
    consumer_name = models.CharField(max_length=255, blank=True, null=True)  # Item 1
    property_supplied = models.TextField(blank=True, null=True)  # Item 2a
    property_owner_name = models.CharField(max_length=255, blank=True, null=True)  # Item 2b
    property_owner_address = models.TextField(blank=True, null=True)  # Item 2c
    contractor = models.CharField(max_length=255, blank=True, null=True)  # Item 3a
    contractor_address = models.TextField(blank=True, null=True)  # Item 3b
    
    # Item 4-16: Main Installation Details
    size_of_mains = models.CharField(max_length=50, blank=True, null=True)  # Item 4a
    size_of_mains_conduit = models.CharField(max_length=50, blank=True, null=True)  # Item 4b
    
    # Item 5: Consumer's main switch
    consumer_main_switch_type = models.CharField(max_length=100, blank=True, null=True)  # Item 5a
    consumer_main_switch_capacity = models.CharField(max_length=50, blank=True, null=True)  # Item 5b
    consumer_main_switch_setting = models.CharField(max_length=50, blank=True, null=True)  # Item 5c
    
    # Item 6: Neutral and earthing
    neutrals_fused = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 6a
    neutral_block_fitted = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 6b
    
    # Item 7: Earth electrode
    earth_electrode_installed = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 7a
    earth_electrode_type = models.CharField(max_length=100, blank=True, null=True)  # Item 7b
    
    # Item 8: Bonding and earthing
    all_equipment_bonded_earthed = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 8
    
    # Item 9: Insulation resistance tests
    insulation_resistance_between = models.CharField(max_length=100, blank=True, null=True)  # Item 9a
    insulation_resistance_to_earth = models.CharField(max_length=100, blank=True, null=True)  # Item 9b
    
    # Item 10: Earth continuity resistance
    earth_continuity_resistance = models.CharField(max_length=100, blank=True, null=True)  # Item 10
    
    # Item 11-13: Polarity and socket outlets
    polarity_switches_plugs = models.TextField(blank=True, null=True)  # Item 11
    socket_outlets_earthed = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 12
    socket_outlet_type = models.CharField(max_length=100, blank=True, null=True)  # Item 13
    
    # Item 14-16: Wiring details
    wiring_type = models.CharField(max_length=100, blank=True, null=True)  # Item 14
    circuit_conductors_correct_size = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 15
    wiring_condition = models.TextField(blank=True, null=True)  # Item 16
    
    # Item 17-19: Specific installation aspects
    flexible_cord_prohibited_positions = models.TextField(blank=True, null=True)  # Item 17
    bathroom_switch_accessible = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 18a
    unearthed_metal_switches = models.TextField(blank=True, null=True)  # Item 18b
    
    # Item 19: Conduits
    conduits_bushed = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 19a
    conduits_bonded_earth = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 19b
    conduits_correct_size = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 19c
    conduits_adequately_supported = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 19d
    conduits_suitable_type = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 19e
    
    # Item 20-24: Circuit and point counts
    max_lighting_points_per_circuit = models.PositiveIntegerField(blank=True, null=True)  # Item 20a
    max_plug_points_per_circuit = models.PositiveIntegerField(blank=True, null=True)  # Item 20b
    total_lighting_points = models.PositiveIntegerField(blank=True, null=True)  # Item 21
    total_plug_points = models.PositiveIntegerField(blank=True, null=True)  # Item 22
    appliances_wattages = models.TextField(blank=True, null=True)  # Item 23
    motors_plant_details = models.TextField(blank=True, null=True)  # Item 24
    
    # Item 25-30: Overhead lines and protection
    overhead_lines_height = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 25a
    overhead_lines_conductor_size = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 25b
    overhead_lines_support = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 25c
    overhead_lines_general = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 25d
    overhead_earthwires_fitted = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 26
    overhead_lines_protected = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 27
    outbuildings_protected = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 28
    motor_installations_protected = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 29
    commission_switch_details = models.TextField(blank=True, null=True)  # Item 30
    
    # Item 31-33: Final status and defects
    supply_connected_disconnected = models.CharField(max_length=20, blank=True, null=True)  # Item 31
    contractor_notified_defects = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)  # Item 32
    other_features_attention = models.TextField(blank=True, null=True)  # Item 33
    
    # Derived status (calculated from safety checks)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Relationships
    client_application = models.ForeignKey(
        'ClientApplication', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='inspection_reports'
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='inspection_reports'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inspection Report'
        verbose_name_plural = 'Inspection Reports'
    
    def __str__(self):
        return f"E117 - {self.service_no or 'TBD'} - {self.consumer_name or 'Unknown'}"
    
    def calculate_status(self):
        """
        Calculate overall status based on safety checks
        """
        safety_checks = [
            self.all_equipment_bonded_earthed,
            self.socket_outlets_earthed,
            self.circuit_conductors_correct_size,
            self.conduits_bonded_earth,
            self.overhead_lines_general,
            self.overhead_lines_protected,
            self.outbuildings_protected,
            self.motor_installations_protected,
        ]
        
        if any(check == 'fail' for check in safety_checks if check):
            return 'fail'
        elif all(check == 'pass' for check in safety_checks if check):
            return 'pass'
        else:
            return 'pending'
    
    def save(self, *args, **kwargs):
        # Auto-calculate status based on safety checks
        self.status = self.calculate_status()
        super().save(*args, **kwargs)


class E6Certificate(models.Model):
    """
    Model for E6 Inspection Clearance Certificate
    Generated when inspection passes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Certificate Information
    certificate_number = models.CharField(max_length=50, unique=True, blank=True)
    service_no = models.CharField(max_length=50, blank=True, null=True)
    
    # Installation Details
    installation_description = models.TextField(blank=True, null=True)
    property_address = models.TextField(blank=True, null=True)
    property_owner_occupant = models.CharField(max_length=255, blank=True, null=True)
    
    # Clearance Information
    minor_defects = models.TextField(blank=True, null=True)
    defects_rectification_period = models.PositiveIntegerField(default=14)  # 14 days default
    
    # Electronic Delivery
    sent_to_client = models.BooleanField(default=False)
    sent_date = models.DateTimeField(blank=True, null=True)
    delivery_method = models.CharField(max_length=50, blank=True, null=True)  # email, etc.
    
    # Relationships
    inspection_report = models.OneToOneField(
        InspectionReport, 
        on_delete=models.CASCADE,
        related_name='e6_certificate'
    )
    client_application = models.ForeignKey(
        ClientApplication,
        on_delete=models.CASCADE,
        related_name='e6_certificates'
    )
    
    # Inspector Information
    installation_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='e6_certificates'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'E6 Certificate'
        verbose_name_plural = 'E6 Certificates'
    
    def __str__(self):
        return f"E6 - {self.certificate_number or 'TBD'} - {self.service_no or 'Unknown'}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = f"E6-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class E1DefectReport(models.Model):
    """
    Model for E1 Inspection of Installation with List of Defects
    Generated when inspection fails
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Report Information
    report_number = models.CharField(max_length=50, unique=True, blank=True)
    service_no = models.CharField(max_length=50, blank=True, null=True)
    
    # Property Information
    property_address = models.TextField(blank=True, null=True)
    sub_division_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Defects Information
    defects_list = models.TextField(blank=True, null=True)
    defects_requiring_attention = models.TextField(blank=True, null=True)
    
    # Distribution Information
    sent_to_consumer = models.BooleanField(default=False)
    sent_to_contractor = models.BooleanField(default=False)
    sent_to_district_manager = models.BooleanField(default=False)
    sent_to_depot_official = models.BooleanField(default=False)
    
    # Electronic Delivery
    sent_date = models.DateTimeField(blank=True, null=True)
    delivery_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Reinspection Information
    is_reinspection = models.BooleanField(default=False)
    original_report = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reinspections'
    )
    
    # Relationships
    inspection_report = models.OneToOneField(
        InspectionReport,
        on_delete=models.CASCADE,
        related_name='e1_defect_report'
    )
    client_application = models.ForeignKey(
        ClientApplication,
        on_delete=models.CASCADE,
        related_name='e1_defect_reports'
    )
    
    # Inspector Information
    installation_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='e1_defect_reports'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'E1 Defect Report'
        verbose_name_plural = 'E1 Defect Reports'
    
    def __str__(self):
        return f"E1 - {self.report_number or 'TBD'} - {self.service_no or 'Unknown'}"
    
    def save(self, *args, **kwargs):
        if not self.report_number:
            self.report_number = f"E1-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class InspectionWorkflow(models.Model):
    """
    Model for tracking the complete inspection workflow
    """
    WORKFLOW_STATUS_CHOICES = [
        ('application_submitted', 'Application Submitted'),
        ('assigned', 'Assigned to Inspector'),
        ('inspection_scheduled', 'Inspection Scheduled'),
        ('inspection_completed', 'Inspection Completed'),
        ('e6_generated', 'E6 Certificate Generated'),
        ('e1_generated', 'E1 Defect Report Generated'),
        ('reinspection_requested', 'Reinspection Requested'),
        ('workflow_completed', 'Workflow Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Workflow Information
    workflow_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=25, choices=WORKFLOW_STATUS_CHOICES, default='application_submitted')
    
    # Relationships
    client_application = models.OneToOneField(
        ClientApplication,
        on_delete=models.CASCADE,
        related_name='workflow'
    )
    inspection_report = models.OneToOneField(
        InspectionReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow'
    )
    e6_certificate = models.OneToOneField(
        E6Certificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow'
    )
    e1_defect_report = models.OneToOneField(
        E1DefectReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow'
    )
    
    # Workflow Tracking
    current_step = models.PositiveIntegerField(default=1)
    total_steps = models.PositiveIntegerField(default=6)
    
    # Reinspection Tracking
    reinspection_count = models.PositiveIntegerField(default=0)
    max_reinspections = models.PositiveIntegerField(default=3)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inspection Workflow'
        verbose_name_plural = 'Inspection Workflows'
    
    def __str__(self):
        return f"Workflow {self.workflow_number} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.workflow_number:
            self.workflow_number = f"WF-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    def can_proceed_to_reinspection(self):
        """Check if reinspection is allowed"""
        return self.reinspection_count < self.max_reinspections
    
    def increment_reinspection_count(self):
        """Increment reinspection count"""
        self.reinspection_count += 1
        self.save()


class ApplicationAssignment(models.Model):
    """
    Model for tracking assignment of applications to field officers/inspectors
    Maps to applicationAssignments table in schema.ts
    """
    
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Assignment Information
    application = models.ForeignKey(
        'ClientApplication', 
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='assigned_inspections'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='assignments_made'
    )
    
    # Assignment Details
    assignment_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(blank=True, null=True)
    assignment_notes = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='assigned')
    
    # Acceptance/Completion
    accepted_date = models.DateTimeField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    completion_notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Application Assignment'
        verbose_name_plural = 'Application Assignments'
        unique_together = ['application', 'assigned_to']  # Prevent duplicate assignments
    
    def __str__(self):
        return f"{self.application.application_number} assigned to {self.assigned_to}"
    
    def accept_assignment(self):
        """
        Mark assignment as accepted
        """
        self.status = 'accepted'
        self.accepted_date = timezone.now()
        self.save()
    
    def complete_assignment(self, notes=None):
        """
        Mark assignment as completed
        """
        self.status = 'completed'
        self.completed_date = timezone.now()
        if notes:
            self.completion_notes = notes
        self.save()
        
        # Update the related application status
        self.application.status = 'completed'
        self.application.save() 