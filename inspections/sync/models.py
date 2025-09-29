from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class SyncOperation(models.Model):
    """
    Track all sync attempts and their status
    """
    SYNC_TYPE_CHOICES = [
        ('full', 'Full Synchronization'),
        ('incremental', 'Incremental Synchronization'),
        ('upload', 'Upload Only'),
        ('download', 'Download Only'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sync_operations'
    )
    records_affected = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Sync parameters
    last_sync_timestamp = models.DateTimeField(blank=True, null=True)
    sync_direction = models.CharField(max_length=10, default='both')  # 'upload', 'download', 'both'

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Sync Operation'
        verbose_name_plural = 'Sync Operations'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['operation_type', 'status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_operation_type_display()} - {self.get_status_display()}"

    def mark_completed(self, records_affected=0, error_message=None):
        """Mark sync operation as completed"""
        self.status = 'completed' if not error_message else 'failed'
        self.completed_at = timezone.now()
        self.records_affected = records_affected
        if error_message:
            self.error_message = error_message
        self.save()

    def mark_in_progress(self):
        """Mark sync operation as in progress"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()


class UploadQueue(models.Model):
    """
    Manage offline upload operations with priority
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    OPERATION_TYPE_CHOICES = [
        ('inspection_create', 'Create Inspection'),
        ('inspection_update', 'Update Inspection'),
        ('photo_upload', 'Upload Photo'),
        ('defect_create', 'Create Defect'),
        ('workflow_update', 'Update Workflow'),
        ('assignment_create', 'Create Assignment'),
        ('assignment_update', 'Update Assignment'),
        ('assignment_accept', 'Accept Assignment'),
        ('assignment_complete', 'Complete Assignment'),
        ('approval_create', 'Create Approval'),
        ('approval_update', 'Update Approval'),
        ('approval_transition', 'Approval Transition'),
        ('merge_operation', 'Merge Operation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPE_CHOICES)
    data = models.JSONField()  # The actual data to sync
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    # Entity reference
    entity_type = models.CharField(max_length=50, blank=True, null=True)  # 'inspection', 'photo', etc.
    entity_id = models.UUIDField(blank=True, null=True)

    # User who created the operation
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='upload_queue_items'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Upload Queue Item'
        verbose_name_plural = 'Upload Queue Items'
        indexes = [
            models.Index(fields=['priority', 'status', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['next_retry_at']),
        ]

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.get_priority_display()} - {self.get_status_display()}"

    def can_retry(self):
        """Check if operation can be retried"""
        return self.attempts < self.max_attempts and self.status in ['failed', 'pending']

    def should_retry_now(self):
        """Check if operation should be retried now"""
        return (
            self.can_retry() and
            self.next_retry_at and
            timezone.now() >= self.next_retry_at
        )

    def mark_processing(self):
        """Mark operation as being processed"""
        self.status = 'processing'
        self.attempts += 1
        self.save()

    def mark_completed(self, error_message=None):
        """Mark operation as completed or failed"""
        self.status = 'failed' if error_message else 'completed'
        self.processed_at = timezone.now()
        if error_message:
            self.error_message = error_message

        # Calculate next retry if failed and can retry
        if self.status == 'failed' and self.can_retry():
            delay_minutes = min(2 ** self.attempts, 60)  # Exponential backoff, max 60 minutes
            self.next_retry_at = timezone.now() + timezone.timedelta(minutes=delay_minutes)
        else:
            self.next_retry_at = None

        self.save()

    def get_retry_delay(self):
        """Get delay in minutes for next retry"""
        if not self.can_retry():
            return 0
        return min(2 ** self.attempts, 60)


class ConflictResolution(models.Model):
    """
    Store conflict resolution decisions and history
    """
    CONFLICT_TYPE_CHOICES = [
        ('inspection_data', 'Inspection Data Conflict'),
        ('workflow_state', 'Workflow State Conflict'),
        ('assignment', 'Assignment Conflict'),
        ('assignment_status', 'Assignment Status Conflict'),
        ('approval', 'Approval Conflict'),
        ('approval_state', 'Approval State Conflict'),
        ('photo_metadata', 'Photo Metadata Conflict'),
    ]

    RESOLUTION_CHOICES = [
        ('server_wins', 'Server Version Accepted'),
        ('local_wins', 'Local Version Accepted'),
        ('merged', 'Data Merged'),
        ('manual', 'Manual Resolution Required'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conflict_type = models.CharField(max_length=20, choices=CONFLICT_TYPE_CHOICES)
    entity_type = models.CharField(max_length=50)  # 'inspection', 'workflow', etc.
    entity_id = models.UUIDField()
    local_data = models.JSONField()
    server_data = models.JSONField()
    resolution = models.CharField(max_length=15, choices=RESOLUTION_CHOICES)
    resolved_data = models.JSONField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conflict_resolutions'
    )
    resolved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    # Sync operation that detected the conflict
    sync_operation = models.ForeignKey(
        SyncOperation,
        on_delete=models.CASCADE,
        related_name='conflicts_detected'
    )

    class Meta:
        ordering = ['-resolved_at']
        verbose_name = 'Conflict Resolution'
        verbose_name_plural = 'Conflict Resolutions'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['conflict_type', 'resolution']),
            models.Index(fields=['resolved_by']),
        ]

    def __str__(self):
        return f"{self.get_conflict_type_display()} - {self.get_resolution_display()} - {self.entity_type}:{self.entity_id}"

    def resolve_with_server_data(self, notes=None):
        """Resolve conflict by accepting server data"""
        self.resolution = 'server_wins'
        self.resolved_data = self.server_data
        self.resolved_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()

    def resolve_with_local_data(self, notes=None):
        """Resolve conflict by accepting local data"""
        self.resolution = 'local_wins'
        self.resolved_data = self.local_data
        self.resolved_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()

    def resolve_with_merged_data(self, merged_data, notes=None):
        """Resolve conflict with merged data"""
        self.resolution = 'merged'
        self.resolved_data = merged_data
        self.resolved_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()

    def mark_manual_resolution_required(self, notes=None):
        """Mark conflict as requiring manual resolution"""
        self.resolution = 'manual'
        self.resolved_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
