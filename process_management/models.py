from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from it.users.models import Regions, UserProfile, Sections



class ProcessDepartment(models.Model):
    """
    Model representing organizational departments for process categorization.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="Display order for departments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Process Department'
        verbose_name_plural = 'Process Departments'

    def __str__(self):
        return self.name

    def clean(self):
        """Validate model fields"""
        if not self.name.strip():
            raise ValidationError({'name': 'Department name cannot be empty'})
        if self.order < 0:
            raise ValidationError({'order': 'Order must be a non-negative integer'})


class Process(models.Model):
    """
    Model representing a business process with departmental and regional relationships.
    Enhanced with IMS-specific fields for ISO compliance.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    department = models.ForeignKey(ProcessDepartment, on_delete=models.CASCADE, related_name='processes')
    region = models.ForeignKey(Regions, on_delete=models.SET_NULL, null=True, blank=True)
    section = models.ForeignKey(Sections, on_delete=models.SET_NULL, null=True, blank=True)
    process_code = models.CharField(max_length=50, blank=True, help_text="Optional process identifier")
    ims_reference = models.CharField(max_length=100, blank=True, help_text="IMS reference code (e.g., ZETDC-HRE MANAGEMENT 01-001)")
    iso_clause = models.CharField(max_length=50, blank=True, help_text="Relevant ISO clause reference")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['department__order', 'department__name', 'name']
        verbose_name = 'Process'
        verbose_name_plural = 'Processes'

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    def clean(self):
        """Validate model fields"""
        if not self.name.strip():
            raise ValidationError({'name': 'Process name cannot be empty'})
        
        # Process code validation removed - no longer requires uniqueness

    def save(self, *args, **kwargs):
        """Override save to run clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_documents_by_type(self):
        """Return documents grouped by type"""
        documents = {}
        for doc in self.documents.filter(is_current=True):
            documents[doc.document_type] = doc
        return documents

    def has_process_map(self):
        """Check if process has a current process map"""
        return self.documents.filter(document_type='process_map', is_current=True).exists()

    def has_procedure(self):
        """Check if process has a current procedure"""
        return self.documents.filter(document_type='procedure', is_current=True).exists()

    def has_risk_register(self):
        """Check if process has a current risk register"""
        return self.documents.filter(document_type='risk_register', is_current=True).exists()

    def has_objectives_targets(self):
        """Check if process has objectives and targets document"""
        return self.documents.filter(document_type='objectives_targets', is_current=True).exists()

    def has_internal_external_issues(self):
        """Check if process has internal and external issues document"""
        return self.documents.filter(document_type='internal_external_issues', is_current=True).exists()

    def has_stakeholder_needs(self):
        """Check if process has stakeholders and their needs document"""
        return self.documents.filter(document_type='stakeholder_needs', is_current=True).exists()

    def has_legal_register(self):
        """Check if process has legal register document"""
        return self.documents.filter(document_type='legal_register', is_current=True).exists()


class ProcessDocument(models.Model):
    """
    Model representing documents associated with processes.
    Enhanced with IMS-specific document types and compliance tracking.
    """
    DOCUMENT_TYPES = [
        ('process_map', 'Process Map'),
        ('procedure', 'Associated Procedure'),
        ('risk_register', 'Risk and Opportunity Register'),
        ('objectives_targets', 'Objectives and Targets'),
        ('internal_external_issues', 'Internal and External Issues'),
        ('stakeholder_needs', 'Stakeholders and Their Needs'),
        ('legal_register', 'Legal Register'),
    ]
    
    DOCUMENT_STATUS_CHOICES = [
        ('accessible', 'Accessible'),
        ('sanitized', 'Sanitized Path'),
        ('missing_file', 'Missing File'),
        ('permission_denied', 'Permission Denied'),
        ('corrupted', 'Corrupted File'),
        ('invalid_path', 'Invalid Path'),
        ('inaccessible', 'Inaccessible'),
        ('error', 'Error'),
    ]

    COMPLIANCE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('obsolete', 'Obsolete'),
        ('pending_approval', 'Pending Approval'),
    ]

    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='uploads/processes/', blank=True, null=True)
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, blank=True, help_text="Original filename before sanitization")
    file_path = models.CharField(max_length=500, blank=True, help_text="Current file path (may be sanitized)")
    original_file_path = models.CharField(max_length=500, blank=True, help_text="Original file path before sanitization")
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True, help_text="MIME type of the file")
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='accessible', help_text="File system status")
    version = models.CharField(max_length=20, default='1.0')
    is_current = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, help_text="Whether the document is active and accessible")
    
    # IMS-specific fields
    document_code = models.CharField(max_length=100, blank=True, help_text="IMS document code")
    ims_file_reference = models.CharField(max_length=200, blank=True, help_text="IMS file reference")
    compliance_status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS_CHOICES, default='draft', help_text="Document compliance status")
    review_due_date = models.DateField(null=True, blank=True, help_text="Date when document review is due")
    approval_authority = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_process_documents', help_text="User authorized to approve this document")
    
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata including file system check results")
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Process Document'
        verbose_name_plural = 'Process Documents'
        # Ensure only one current document per type per process
        unique_together = [['process', 'document_type', 'is_current']]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.process.name} (v{self.version})"

    def clean(self):
        """Validate model fields with enhanced file system error handling"""
        if not self.filename.strip():
            raise ValidationError({'filename': 'Filename cannot be empty'})
        
        if not self.version.strip():
            raise ValidationError({'version': 'Version cannot be empty'})
        
        # Set original_filename if not provided
        if not self.original_filename:
            self.original_filename = self.filename
        
        # Set original_file_path if not provided
        if not self.original_file_path and self.file_path:
            self.original_file_path = self.file_path
        
        # Validate file_size is non-negative
        if self.file_size < 0:
            raise ValidationError({'file_size': 'File size cannot be negative'})
        
        # Validate that only one current document exists per type per process
        if self.is_current:
            existing = ProcessDocument.objects.filter(
                process=self.process,
                document_type=self.document_type,
                is_current=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'is_current': f'Only one current {self.get_document_type_display()} can exist per process'
                })

    def save(self, *args, **kwargs):
        """Override save to handle current document logic and validation with file system error handling"""
        # If this is being set as current, mark others as not current
        if self.is_current:
            ProcessDocument.objects.filter(
                process=self.process,
                document_type=self.document_type,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        
        # Set filename from file if not provided
        if self.file and not self.filename:
            self.filename = self.file.name
        
        # Set file_path from file if not provided
        if self.file and not self.file_path:
            self.file_path = str(self.file)
        
        # Update file_size from file if available
        if self.file and self.file_size == 0:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError):
                pass
        
        # Set is_active based on status
        if self.status in ['missing_file', 'permission_denied', 'corrupted', 'invalid_path', 'inaccessible', 'error']:
            self.is_active = False
        
        self.full_clean()
        super().save(*args, **kwargs)

    def get_file_extension(self):
        """Get the file extension"""
        if self.filename:
            return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
        return ''

    def get_file_size(self):
        """Get the file size in bytes"""
        if self.file:
            try:
                return self.file.size
            except (OSError, ValueError):
                return 0
        return 0

    def get_file_size_display(self):
        """Get human-readable file size"""
        size = self.file_size or self.get_file_size()
        if size == 0:
            return "0 bytes"
        
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def has_file_system_error(self):
        """Check if document has file system errors"""
        return self.status not in ['accessible', 'sanitized']
    
    def get_file_system_error_message(self):
        """Get file system error message from metadata"""
        if self.metadata and 'file_system_error' in self.metadata:
            return self.metadata['file_system_error'].get('error_message', 'Unknown error')
        elif self.metadata and 'file_system_check' in self.metadata:
            return self.metadata['file_system_check'].get('error_message', 'Unknown error')
        return None
    
    def get_recovery_strategy(self):
        """Get recovery strategy applied for file system errors"""
        if self.metadata and 'file_system_error' in self.metadata:
            return self.metadata['file_system_error'].get('recovery_strategy', 'none')
        return 'none'
    
    def is_path_sanitized(self):
        """Check if the file path was sanitized"""
        return self.status == 'sanitized' or (self.original_file_path and self.file_path != self.original_file_path)
    
    def get_sanitization_changes(self):
        """Get list of sanitization changes made to the path"""
        if self.metadata and 'file_system_check' in self.metadata:
            return self.metadata['file_system_check'].get('sanitization_changes', [])
        return []

    def is_review_overdue(self):
        """Check if document review is overdue"""
        if self.review_due_date:
            return self.review_due_date < timezone.now().date()
        return False

    def get_compliance_status_display(self):
        """Get compliance status with overdue indicator"""
        status = self.get_compliance_status_display()
        if self.is_review_overdue():
            return f"{status} (Overdue)"
        return status


class MigrationCheckpoint(models.Model):
    """
    Model for tracking migration progress and enabling resume functionality.
    """
    MIGRATION_STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]
    
    migration_id = models.CharField(max_length=100, unique=True, help_text="Unique identifier for this migration run")
    status = models.CharField(max_length=20, choices=MIGRATION_STATUS_CHOICES, default='started')
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    successful_items = models.IntegerField(default=0)
    failed_items = models.IntegerField(default=0)
    skipped_items = models.IntegerField(default=0)
    
    # Migration metadata
    batch_size = models.IntegerField(default=50)
    max_retries = models.IntegerField(default=3)
    error_threshold = models.FloatField(default=0.1)
    
    # Timing information
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Progress tracking
    current_batch = models.IntegerField(default=0)
    last_processed_item_id = models.CharField(max_length=255, blank=True)
    
    # Error information
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Configuration snapshot
    migration_config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Migration Checkpoint'
        verbose_name_plural = 'Migration Checkpoints'
    
    def __str__(self):
        return f"Migration {self.migration_id} - {self.get_status_display()}"
    
    def update_progress(self, processed: int = 0, successful: int = 0, failed: int = 0, skipped: int = 0):
        """Update progress counters."""
        self.processed_items += processed
        self.successful_items += successful
        self.failed_items += failed
        self.skipped_items += skipped
        self.last_updated = timezone.now()
        self.save(update_fields=['processed_items', 'successful_items', 'failed_items', 'skipped_items', 'last_updated'])
    
    def mark_completed(self):
        """Mark migration as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error_message: str, error_details: dict = None):
        """Mark migration as failed."""
        self.status = 'failed'
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'error_details', 'completed_at'])
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100
    
    def can_resume(self) -> bool:
        """Check if this migration can be resumed."""
        return self.status in ['started', 'in_progress', 'failed'] and self.processed_items < self.total_items


class MigrationItem(models.Model):
    """
    Model for tracking individual items processed during migration.
    """
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    checkpoint = models.ForeignKey(MigrationCheckpoint, on_delete=models.CASCADE, related_name='items')
    item_id = models.CharField(max_length=100, help_text="Unique identifier for this item")
    item_type = models.CharField(max_length=50, help_text="Type of item (e.g., 'process_candidate', 'document')")
    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='pending')
    
    # Source information for idempotency checks
    source_filename = models.CharField(max_length=255, blank=True)
    source_folder_path = models.CharField(max_length=500, blank=True)
    source_identifier = models.CharField(max_length=255, blank=True, help_text="Original source ID (folder_id, legacy_id, etc.)")
    
    # Processing information
    retry_count = models.IntegerField(default=0)
    processing_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    error_type = models.CharField(max_length=50, blank=True)
    
    # Result information
    created_process_id = models.IntegerField(null=True, blank=True, help_text="ID of created Process")
    created_document_ids = models.JSONField(default=list, blank=True, help_text="IDs of created ProcessDocuments")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Item data snapshot
    item_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Migration Item'
        verbose_name_plural = 'Migration Items'
        constraints = [
            models.UniqueConstraint(fields=['checkpoint', 'item_id'], name='unique_checkpoint_item')
        ]
        indexes = [
            models.Index(fields=['source_filename']),
            models.Index(fields=['source_folder_path']),
            models.Index(fields=['source_identifier']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.item_id} - {self.get_status_display()}"
    
    def mark_completed(self, process_id: int = None, document_ids: list = None):
        """Mark item as completed with result information."""
        self.status = 'completed'
        self.processed_at = timezone.now()
        if process_id:
            self.created_process_id = process_id
        if document_ids:
            self.created_document_ids = document_ids
        self.save(update_fields=['status', 'processed_at', 'created_process_id', 'created_document_ids'])
    
    def mark_failed(self, error_message: str, error_type: str = ''):
        """Mark item as failed with error information."""
        self.status = 'failed'
        self.error_message = error_message
        self.error_type = error_type
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'error_type', 'processed_at'])
    
    def mark_skipped(self, reason: str = ''):
        """Mark item as skipped."""
        self.status = 'skipped'
        self.error_message = reason
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.save(update_fields=['retry_count'])
    
    def is_already_migrated(self) -> bool:
        """Check if this item has already been successfully migrated."""
        if self.created_process_id:
            # Check if the process still exists
            from process_management.models import Process
            return Process.objects.filter(id=self.created_process_id).exists()
        return False
