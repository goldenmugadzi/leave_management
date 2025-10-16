from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class E60InspectionReport(models.Model):
    """Main model for E60 Consumer Substation Inspection and Overhaul reports"""
    
    INSPECTION_TYPE_CHOICES = [
        ('routine', 'Routine Inspection'),
        ('overhaul', 'Overhaul'),
        ('emergency', 'Emergency Inspection'),
        ('commissioning', 'Commissioning'),
    ]
    
    CONSTRUCTION_TYPE_CHOICES = [
        ('pmt', 'PMT'),
        ('concrete', 'Concrete'),
        ('steel', 'Steel'),
        ('brick', 'Brick'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_number = models.CharField(max_length=50, unique=True)
    
    # Header Information
    substation_name = models.CharField(max_length=255)
    service_number = models.CharField(max_length=50)
    section = models.CharField(max_length=100)
    construction_type = models.CharField(max_length=20, choices=CONSTRUCTION_TYPE_CHOICES)
    inspection_date = models.DateField()
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPE_CHOICES)
    
    # Inspector Information
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    inspector_signature = models.TextField(blank=True, null=True)  # Base64 encoded signature
    
    # Overall Assessment
    general_condition = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-inspection_date', 'substation_name']
        verbose_name = 'E60 Inspection Report'
        verbose_name_plural = 'E60 Inspection Reports'
    
    def __str__(self):
        return f"{self.report_number} - {self.substation_name} - {self.inspection_date}"
    
    def save(self, *args, **kwargs):
        if not self.report_number:
            self.report_number = f"E60-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class E60TransformerInspection(models.Model):
    """Model for Section A: TRANSFORMERS inspection data"""
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    BREATHER_TYPE_CHOICES = [
        ('silica_gel', 'Silica Gel'),
        ('oil', 'Oil'),
        ('sealed', 'Sealed'),
    ]
    
    OIL_LEAK_CHOICES = [
        ('none', 'None'),
        ('minor', 'Minor'),
        ('major', 'Major'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='transformer_inspection')
    
    # Transformer Specifications
    make = models.CharField(max_length=100, blank=True, null=True)
    kva_rating = models.PositiveIntegerField(blank=True, null=True)
    voltage_ratio = models.CharField(max_length=20, blank=True, null=True)  # e.g., "11/0.4"
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    security_mounting = models.CharField(max_length=50, blank=True, null=True)
    
    # Bonding and Earthing
    # tank_bonded_to_earth = models.BooleanField(blank=True, null=True)
    lt_neutral_bonded_to_earth = models.BooleanField(blank=True, null=True)
    
    # Condition Assessment
    bushings_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    paintwork_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    
    # Technical Specifications
    arcing_horn_gap_setting = models.CharField(max_length=20, blank=True, null=True)  # e.g., "95mm"
    breather_type = models.CharField(max_length=20, choices=BREATHER_TYPE_CHOICES, blank=True, null=True)
    breather_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    oil_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    oil_leaks = models.CharField(max_length=20, choices=OIL_LEAK_CHOICES, blank=True, null=True)
    
    # Test Results
    megger_hv_lv = models.CharField(max_length=20, blank=True, null=True)
    megger_hv_e = models.CharField(max_length=20, blank=True, null=True)
    megger_lv_e = models.CharField(max_length=20, blank=True, null=True)
    oil_test_results = models.CharField(max_length=100, blank=True, null=True)
    
    # Tap Settings
    tap_range = models.CharField(max_length=20, blank=True, null=True)  # e.g., "1-5"
    tap_position_found = models.CharField(max_length=20, blank=True, null=True)  # e.g., "tap 3"
    tap_position_left = models.CharField(max_length=20, blank=True, null=True)  # e.g., "tap 3"
    
    class Meta:
        verbose_name = 'E60 Transformer Inspection'
        verbose_name_plural = 'E60 Transformer Inspections'
    
    def __str__(self):
        return f"Transformer - {self.inspection_report.report_number}"


class E60CircuitBreakerInspection(models.Model):
    """Model for Section B: A.C.B or O.C.B inspection data"""
    
    BREAKER_TYPE_CHOICES = [
        ('acb', 'A.C.B'),
        ('ocb', 'O.C.B'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='circuit_breaker_inspection')
    
    # Basic Information
    make = models.CharField(max_length=100, blank=True, null=True)
    breaker_type = models.CharField(max_length=10, choices=BREAKER_TYPE_CHOICES, blank=True, null=True)
    zesa_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Ratings
    current_rating = models.CharField(max_length=20, blank=True, null=True)
    voltage_rating = models.CharField(max_length=20, blank=True, null=True)
    
    # Settings
    trip_setting = models.CharField(max_length=20, blank=True, null=True)
    consumer_trip_setting = models.CharField(max_length=20, blank=True, null=True)
    
    # Condition Assessment
    oil_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    contacts_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    nuts_connections_tight = models.BooleanField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 Circuit Breaker Inspection'
        verbose_name_plural = 'E60 Circuit Breaker Inspections'
    
    def __str__(self):
        return f"Circuit Breaker - {self.inspection_report.report_number}"


class E60MeteringInspection(models.Model):
    """Model for Section C: METERING inspection data"""
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    PHASE_ROTATION_CHOICES = [
        ('correct', 'Correct'),
        ('incorrect', 'Incorrect'),
        ('not_checked', 'Not Checked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='metering_inspection')
    
    # Basic Information
    make = models.CharField(max_length=100, blank=True, null=True)
    current_rating = models.CharField(max_length=20, blank=True, null=True)
    voltage_rating = models.CharField(max_length=20, blank=True, null=True)
    meter_type = models.CharField(max_length=50, blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    zesa_number = models.CharField(max_length=50, blank=True, null=True)
    vad_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Ratios
    ct_ratio = models.CharField(max_length=20, blank=True, null=True)
    vt_ratio = models.CharField(max_length=20, blank=True, null=True)
    
    # Protection and Safety
    meter_protection_type = models.CharField(max_length=50, blank=True, null=True)
    meter_case_earthed = models.BooleanField(blank=True, null=True)
    
    # Condition Assessment
    potential_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    phase_rotation = models.CharField(max_length=20, choices=PHASE_ROTATION_CHOICES, blank=True, null=True)
    connections_tight = models.BooleanField(blank=True, null=True)
    equipment_fully_sealed = models.BooleanField(blank=True, null=True)
    meter_reading_card_available = models.BooleanField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 Metering Inspection'
        verbose_name_plural = 'E60 Metering Inspections'
    
    def __str__(self):
        return f"Metering - {self.inspection_report.report_number}"


class E60HousingInspection(models.Model):
    """Model for Section D: METER/SWITCHGEAR HOUSING inspection data"""
    
    HOUSING_TYPE_CHOICES = [
        ('cubicle', 'Cubicle'),
        ('house', 'House'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='housing_inspection')
    
    # Housing Type and Condition
    housing_type = models.CharField(max_length=20, choices=HOUSING_TYPE_CHOICES, blank=True, null=True)
    weatherproof = models.BooleanField(blank=True, null=True)
    door_fitted = models.BooleanField(blank=True, null=True)
    paintwork_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    water_outlet_in_conduit = models.BooleanField(blank=True, null=True)
    door_fitted_with_lock = models.BooleanField(blank=True, null=True)
    lock_lubricated = models.BooleanField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 Housing Inspection'
        verbose_name_plural = 'E60 Housing Inspections'
    
    def __str__(self):
        return f"Housing - {self.inspection_report.report_number}"


class E60FuseInspection(models.Model):
    """Model for Section E: 'D' FUSES inspection data"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='fuse_inspection')
    
    # Fuse Specifications
    rating_and_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., "31.5A"
    gauze_washers_fitted = models.BooleanField(blank=True, null=True)
    
    # Holder Condition
    holders_drop_freely = models.BooleanField(blank=True, null=True)
    holders_make_good_contact = models.BooleanField(blank=True, null=True)
    contacts_treated_with_anti_scuffing_paste = models.BooleanField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 Fuse Inspection'
        verbose_name_plural = 'E60 Fuse Inspections'
    
    def __str__(self):
        return f"Fuses - {self.inspection_report.report_number}"


class E60SurgeArrestorInspection(models.Model):
    """Model for Sections F & G: HV and LV SURGE ARRESTORS inspection data"""
    
    ARRESTOR_TYPE_CHOICES = [
        ('hv', 'HV Surge Arrestor'),
        ('lv', 'LV Surge Arrestor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.ForeignKey(E60InspectionReport, on_delete=models.CASCADE, related_name='surge_arrestor_inspections')
    arrestor_type = models.CharField(max_length=10, choices=ARRESTOR_TYPE_CHOICES)
    
    # Basic Information
    make_and_type = models.CharField(max_length=100, blank=True, null=True)
    voltage_rating = models.CharField(max_length=20, blank=True, null=True)
    current_rating = models.CharField(max_length=20, blank=True, null=True)  # For LV only
    capacity_satisfactory = models.BooleanField(blank=True, null=True)  # For LV only
    
    class Meta:
        verbose_name = 'E60 Surge Arrestor Inspection'
        verbose_name_plural = 'E60 Surge Arrestor Inspections'
    
    def __str__(self):
        return f"{self.get_arrestor_type_display()} - {self.inspection_report.report_number}"


class E60GeneralStateInspection(models.Model):
    """Model for Section J: SUBSTATION GENERAL STATE inspection data"""
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='general_state_inspection')
    
    # Earth Resistance and Bonding
    total_earth_resistance = models.CharField(max_length=20, blank=True, null=True)
    number_of_earth_electrodes = models.PositiveIntegerField(blank=True, null=True)
    structures_bonded_to_earth = models.BooleanField(blank=True, null=True)
    lv_cable_sheath_bonded_to_earth = models.BooleanField(blank=True, null=True)
    
    # LV Mains and Infrastructure
    lv_mains_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    lv_mains_type_and_length = models.CharField(max_length=100, blank=True, null=True)
    
    # Poles and Paintwork
    poles_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    paintwork_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    
    # Site Conditions
    site_clear_of_undergrowth = models.BooleanField(blank=True, null=True)
    site_accessible_by_vehicle = models.BooleanField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 General State Inspection'
        verbose_name_plural = 'E60 General State Inspections'
    
    def __str__(self):
        return f"General State - {self.inspection_report.report_number}"


class E60SafetyInspection(models.Model):
    """Model for Section K: SAFETY PRECAUTIONS inspection data"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='safety_inspection')
    
    # Safety Equipment
    danger_plates_fitted = models.BooleanField(blank=True, null=True)
    anti_climb_fitted = models.BooleanField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 Safety Inspection'
        verbose_name_plural = 'E60 Safety Inspections'
    
    def __str__(self):
        return f"Safety - {self.inspection_report.report_number}"


class E60ConsumerInstallationInspection(models.Model):
    """Model for Section L: CONSUMER'S INSTALLATION inspection data"""
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_report = models.OneToOneField(E60InspectionReport, on_delete=models.CASCADE, related_name='consumer_installation_inspection')
    
    # Consumer Installation Assessment
    general_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    
    class Meta:
        verbose_name = 'E60 Consumer Installation Inspection'
        verbose_name_plural = 'E60 Consumer Installation Inspections'
    
    def __str__(self):
        return f"Consumer Installation - {self.inspection_report.report_number}"