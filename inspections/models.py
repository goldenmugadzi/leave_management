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
    
    # INSTALLATION_TYPE_CHOICES, CONSUMER_UNIT_TYPE_CHOICES, DB_ENCLOSURE_TYPE_CHOICES removed
    # CONDUIT_MATERIAL_CHOICES removed (not used)
    
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
    
    # Defects tracking
    defects_count = models.PositiveIntegerField(default=0, blank=True, null=True, help_text="Number of defects found during inspection")
    
    # Mobile sync tracking
    offline_created = models.BooleanField(default=False, blank=True, null=True, help_text="Whether inspection was created offline")
    sync_status = models.CharField(max_length=20, default='pending', blank=True, null=True, help_text="Sync status: pending, synced, failed, conflict")
    sync_attempts = models.PositiveIntegerField(default=0, blank=True, null=True, help_text="Number of sync attempts")
    last_sync_attempt = models.DateTimeField(null=True, blank=True, help_text="Last sync attempt timestamp")
    sync_error_message = models.TextField(blank=True, null=True, help_text="Last sync error message")
    
    # Location and GPS tracking
    gps_coordinates = models.JSONField(null=True, blank=True, help_text="GPS coordinates as {'latitude': float, 'longitude': float}")
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    location_timestamp = models.DateTimeField(null=True, blank=True, help_text="When GPS location was captured")
    
    # Digital signatures
    inspector_signature = models.TextField(blank=True, null=True, help_text="Base64 encoded inspector signature")
    customer_signature = models.TextField(blank=True, null=True, help_text="Base64 encoded customer signature")
    signature_timestamp = models.DateTimeField(null=True, blank=True, help_text="When signatures were captured")
    
    # Installation metadata - REMOVED (not on original form)
    # installation_type, consumer_unit_type, db_enclosure_type removed
    
    # Inspection timing
    started_at = models.DateTimeField(null=True, blank=True, help_text="When inspection was started")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When inspection was completed")
    inspection_duration = models.DurationField(null=True, blank=True, help_text="Total inspection duration")
    
    # Photo tracking
    photos_count = models.PositiveIntegerField(default=0, blank=True, null=True, help_text="Number of photos taken")
    photos_taken_at = models.DateTimeField(null=True, blank=True, help_text="When photos were taken")
    # photo_quality and photo_resolution removed (not used)
    
    # Meter and equipment details - REMOVED (not on original form)
    # meter_type, meter_serial_number, meter_reading, main_switch_rating, main_switch_type removed
    
    # Environmental conditions - REMOVED (not on original form)
    # temperature, humidity, weather_conditions removed
    
    # Earthing system - REMOVED (not on original form)
    # earthing_system_type, earthing_resistance removed
    
    # Additional notes and recommendations
    notes = models.TextField(blank=True, null=True, help_text="Additional inspection notes")
    recommendations = models.TextField(blank=True, null=True, help_text="Recommendations from inspection")
    next_inspection_due = models.DateField(null=True, blank=True, help_text="Next inspection due date")
    
    # Mobile-specific fields (not stored, but may exist in DB)
    mobile_id = models.CharField(max_length=255, blank=True, null=True, help_text="Mobile app identifier (not used for lookups)")
    # Note: inspector_id is automatically created by Django for the 'inspector' ForeignKey field
    
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


class InspectionPhoto(models.Model):
    """
    Model for inspection photos uploaded during field inspections
    Stores photos with GPS coordinates and metadata
    """
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationship
    inspection_report = models.ForeignKey(
        InspectionReport,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    
    # File Information
    filename = models.CharField(max_length=255)
    file = models.ImageField(upload_to='uploads/inspections/photos/')
    caption = models.CharField(max_length=500, blank=True, null=True)
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    content_type = models.CharField(max_length=100, default='image/jpeg')
    file_size = models.PositiveIntegerField(default=0)  # Size in bytes
    
    # GPS Coordinates
    gps_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        blank=True, 
        null=True,
        help_text="Latitude coordinate where photo was taken"
    )
    gps_longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        blank=True, 
        null=True,
        help_text="Longitude coordinate where photo was taken"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Inspection Photo'
        verbose_name_plural = 'Inspection Photos'
    
    def __str__(self):
        return f"{self.filename} - {self.inspection_report.service_no or 'Unknown'}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate file size if not set
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
        
        # Update parent inspection's photos_count
        self._update_inspection_photo_count()
    
    def delete(self, *args, **kwargs):
        inspection = self.inspection_report
        result = super().delete(*args, **kwargs)
        # Update count after deletion
        if inspection:
            inspection.photos_count = inspection.photos.count()
            inspection.save(update_fields=['photos_count'])
        return result
    
    def _update_inspection_photo_count(self):
        """Update the photos_count field on the related inspection"""
        if self.inspection_report:
            actual_count = self.inspection_report.photos.count()
            if self.inspection_report.photos_count != actual_count:
                self.inspection_report.photos_count = actual_count
                self.inspection_report.save(update_fields=['photos_count'])


class DocumentDistribution(models.Model):
    """
    Audit trail for document distribution to stakeholders.
    Tracks when and how documents (E6/E1) are shared with various stakeholders.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('e6_certificate', 'E6 Certificate'),
        ('e1_defect_report', 'E1 Defect Report'),
        ('inspection_report', 'Inspection Report'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('print', 'Printed'),
        ('hand_delivery', 'Hand Delivery'),
        ('postal', 'Postal Mail'),
        ('native_share', 'Native Share'),
        ('file_export', 'File Export'),
    ]
    
    STAKEHOLDER_TYPE_CHOICES = [
        ('client', 'Client/Property Owner'),
        ('consumer', 'Consumer'),
        ('contractor', 'Contractor'),
        ('district_manager', 'District Manager'),
        ('depot_official', 'Depot Official'),
        ('regional_manager', 'Regional Manager'),
        ('inspector', 'Inspector'),
        ('other', 'Other'),
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('read', 'Read/Acknowledged'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Document Information
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    e6_certificate = models.ForeignKey(
        E6Certificate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='distributions'
    )
    e1_defect_report = models.ForeignKey(
        E1DefectReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='distributions'
    )
    inspection_report = models.ForeignKey(
        InspectionReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='distributions'
    )
    
    # Recipient Information
    stakeholder_type = models.CharField(max_length=30, choices=STAKEHOLDER_TYPE_CHOICES)
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    recipient_organization = models.CharField(max_length=255, blank=True, null=True)
    
    # Distribution Details
    delivery_method = models.CharField(max_length=30, choices=DELIVERY_METHOD_CHOICES)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking Details
    tracking_reference = models.CharField(max_length=255, blank=True, null=True, help_text="Email ID, SMS ID, etc.")
    error_message = models.TextField(blank=True, null=True)
    
    # User and Device Information
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_distributions'
    )
    device_info = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional distribution metadata")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Document Distribution'
        verbose_name_plural = 'Document Distributions'
        indexes = [
            models.Index(fields=['document_type', 'delivery_status']),
            models.Index(fields=['stakeholder_type', 'sent_at']),
            models.Index(fields=['recipient_email']),
        ]
    
    def __str__(self):
        doc_ref = self.get_document_reference()
        return f"{self.get_document_type_display()} to {self.recipient_name} ({self.get_delivery_status_display()}) - {doc_ref}"
    
    def get_document_reference(self):
        """Get the document reference number"""
        if self.e6_certificate:
            return self.e6_certificate.certificate_number
        elif self.e1_defect_report:
            return self.e1_defect_report.report_number
        elif self.inspection_report:
            return self.inspection_report.reference_number
        return "Unknown"
    
    def mark_delivered(self):
        """Mark the distribution as delivered"""
        self.delivery_status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['delivery_status', 'delivered_at', 'updated_at'])
    
    def mark_acknowledged(self):
        """Mark the distribution as acknowledged/read"""
        self.delivery_status = 'read'
        self.acknowledged_at = timezone.now()
        if not self.delivered_at:
            self.delivered_at = self.acknowledged_at
        self.save(update_fields=['delivery_status', 'acknowledged_at', 'delivered_at', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark the distribution as failed with error message"""
        self.delivery_status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['delivery_status', 'error_message', 'updated_at'])


class CertificateAuditLog(models.Model):
    """
    Comprehensive audit log for all certificate-related actions.
    Tracks creation, updates, sharing, revocation, and verification.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('shared', 'Shared'),
        ('revoked', 'Revoked'),
        ('acknowledged', 'Acknowledged'),
        ('verified', 'Verified'),
        ('printed', 'Printed'),
        ('downloaded', 'Downloaded'),
        ('viewed', 'Viewed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Certificate Reference
    e6_certificate = models.ForeignKey(
        E6Certificate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    e1_defect_report = models.ForeignKey(
        E1DefectReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # Action Details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # User Information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificate_audit_logs'
    )
    user_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Technical Details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional Context
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional action metadata (recipients, method, etc.)")
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Certificate Audit Log'
        verbose_name_plural = 'Certificate Audit Logs'
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        doc_ref = self.get_document_reference()
        user = self.user_name or (self.user.get_full_name() if self.user else 'System')
        return f"{self.get_action_display()} - {doc_ref} by {user} at {self.timestamp}"
    
    def get_document_reference(self):
        """Get the document reference number"""
        if self.e6_certificate:
            return f"E6-{self.e6_certificate.certificate_number}"
        elif self.e1_defect_report:
            return f"E1-{self.e1_defect_report.report_number}"
        return "Unknown" 