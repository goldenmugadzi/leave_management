from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.utils import timezone
import uuid


class ClientApplication(models.Model):
    """
    Model for client applications submitted for electrical inspections
    Maps to clientApplications table in schema.ts
    """
    
    APPLICATION_TYPE_CHOICES = [
        ('new_installation', 'New Installation'),
        ('routine_inspection', 'Routine Inspection'),
        ('change_of_tenancy', 'Change of Tenancy'),
        ('reconnection', 'Reconnection'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
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
    
    # Customer Information
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    
    # Property Information
    property_address = models.TextField()
    property_type = models.CharField(max_length=15, choices=PROPERTY_TYPE_CHOICES, blank=True, null=True)
    service_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Installation Details
    installation_description = models.TextField(blank=True, null=True)
    contractor_name = models.CharField(max_length=255, blank=True, null=True)
    contractor_license = models.CharField(max_length=100, blank=True, null=True)
    
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
    documents_attached = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client Application'
        verbose_name_plural = 'Client Applications'
    
    def __str__(self):
        return f"{self.application_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # Auto-generate application number if not provided
            self.application_number = f"APP-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class InspectionReport(models.Model):
    """
    Model for electrical inspection reports
    Maps to inspectionReports table in schema.ts
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
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    inspection_date = models.DateField(blank=True, null=True)
    service_no = models.CharField(max_length=50, blank=True, null=True)
    installation_type = models.CharField(max_length=15, choices=INSTALLATION_TYPE_CHOICES, blank=True, null=True)
    consumer_name = models.CharField(max_length=255, blank=True, null=True)
    property_supplied = models.TextField(blank=True, null=True)
    property_owner_name = models.CharField(max_length=255, blank=True, null=True)
    property_owner_address = models.TextField(blank=True, null=True)
    contractor = models.CharField(max_length=255, blank=True, null=True)
    contractor_address = models.TextField(blank=True, null=True)
    
    # Installation Details
    size_of_mains = models.CharField(max_length=50, blank=True, null=True)
    size_of_mains_conduit = models.CharField(max_length=50, blank=True, null=True)
    earthing = models.CharField(max_length=100, blank=True, null=True)
    consumer_unit_type = models.CharField(max_length=10, choices=CONSUMER_UNIT_TYPE_CHOICES, blank=True, null=True)
    db_enclosure_type = models.CharField(max_length=10, choices=DB_ENCLOSURE_TYPE_CHOICES, blank=True, null=True)
    
    # Testing
    insulation_resistance_between = models.CharField(max_length=100, blank=True, null=True)
    insulation_resistance_to_earth = models.CharField(max_length=100, blank=True, null=True)
    continuity_test = models.CharField(max_length=100, blank=True, null=True)
    
    # Safety Checks
    earth_fault_protection = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)
    overcurrent_protection = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)
    installation_safety = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)
    
    # Conduits
    conduit_material = models.CharField(max_length=15, choices=CONDUIT_MATERIAL_CHOICES, blank=True, null=True)
    conduit_installation = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)
    
    # Final Checks
    overall_compliance = models.CharField(max_length=10, choices=COMPLIANCE_CHOICES, blank=True, null=True)
    defects_found = models.TextField(blank=True, null=True)
    inspector_comments = models.TextField(blank=True, null=True)
    
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
        return f"Inspection {self.service_no or 'TBD'} - {self.consumer_name or 'Unknown'}"
    
    def calculate_status(self):
        """
        Calculate overall status based on safety checks
        """
        safety_checks = [
            self.earth_fault_protection,
            self.overcurrent_protection,
            self.installation_safety,
            self.overall_compliance
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