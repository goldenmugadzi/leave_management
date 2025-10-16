"""
Serializers for sync operations and data exchange
"""

from rest_framework import serializers
from django.utils import timezone
from .models import SyncOperation, UploadQueue, ConflictResolution
from ..models import ApplicationAssignment


class SyncOperationSerializer(serializers.ModelSerializer):
    """
    Serializer for sync operations
    """
    user = serializers.StringRelatedField(read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = SyncOperation
        fields = [
            'id', 'operation_type', 'status', 'user', 'records_affected',
            'error_message', 'started_at', 'completed_at', 'duration',
            'metadata', 'last_sync_timestamp', 'sync_direction'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'duration']

    def get_duration(self, obj):
        """Calculate duration of sync operation"""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class UploadQueueSerializer(serializers.ModelSerializer):
    """
    Serializer for upload queue operations
    """
    created_by = serializers.StringRelatedField(read_only=True)
    retry_delay = serializers.SerializerMethodField()
    can_retry = serializers.SerializerMethodField()

    class Meta:
        model = UploadQueue
        fields = [
            'id', 'operation_type', 'priority', 'status', 'attempts',
            'max_attempts', 'next_retry_at', 'created_at', 'processed_at',
            'error_message', 'entity_type', 'entity_id', 'created_by',
            'retry_delay', 'can_retry'
        ]
        read_only_fields = ['id', 'created_at', 'retry_delay', 'can_retry']

    def get_retry_delay(self, obj):
        """Get retry delay in minutes"""
        return obj.get_retry_delay()

    def get_can_retry(self, obj):
        """Check if operation can be retried"""
        return obj.can_retry()


class ConflictResolutionSerializer(serializers.ModelSerializer):
    """
    Serializer for conflict resolution records
    """
    resolved_by = serializers.StringRelatedField(read_only=True)
    sync_operation = SyncOperationSerializer(read_only=True)

    class Meta:
        model = ConflictResolution
        fields = [
            'id', 'conflict_type', 'entity_type', 'entity_id',
            'local_data', 'server_data', 'resolution', 'resolved_data',
            'resolved_by', 'resolved_at', 'notes', 'sync_operation'
        ]
        read_only_fields = ['id', 'resolved_at', 'sync_operation']


class InspectionSyncDataSerializer(serializers.Serializer):
    """
    Serializer for inspection data during sync operations
    """
    id = serializers.UUIDField(required=False)
    inspection_date = serializers.DateField()
    service_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    consumer_name = serializers.CharField(max_length=255)
    property_supplied = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    contractor = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # Safety checks
    all_equipment_bonded_earthed = serializers.ChoiceField(
        choices=[('pass', 'Pass'), ('fail', 'Fail'), ('na', 'Not Applicable')],
        required=False, allow_blank=True
    )
    socket_outlets_earthed = serializers.ChoiceField(
        choices=[('pass', 'Pass'), ('fail', 'Fail'), ('na', 'Not Applicable')],
        required=False, allow_blank=True
    )
    circuit_conductors_correct_size = serializers.ChoiceField(
        choices=[('pass', 'Pass'), ('fail', 'Fail'), ('na', 'Not Applicable')],
        required=False, allow_blank=True
    )

    # Status
    status = serializers.ChoiceField(
        choices=[('pass', 'Pass'), ('fail', 'Fail'), ('pending', 'Pending')],
        default='pending'
    )

    # Metadata
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def validate(self, data):
        """
        Validate inspection data
        """
        errors = []

        # Required field validation
        required_fields = ['consumer_name', 'inspection_date']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field} is required")

        # Status-specific validation
        status = data.get('status')
        if status in ['pass', 'fail']:
            # Require safety checks for pass/fail status
            safety_fields = [
                'all_equipment_bonded_earthed',
                'socket_outlets_earthed',
                'circuit_conductors_correct_size'
            ]
            for field in safety_fields:
                if not data.get(field):
                    errors.append(f"{field} is required when status is {status}")

        if errors:
            raise serializers.ValidationError(errors)

        return data


class WorkflowSyncDataSerializer(serializers.Serializer):
    """
    Serializer for workflow data during sync operations
    """
    id = serializers.UUIDField(required=False)
    workflow_number = serializers.CharField(max_length=50, read_only=True)
    status = serializers.ChoiceField(
        choices=[
            ('application_submitted', 'Application Submitted'),
            ('assigned', 'Assigned to Inspector'),
            ('inspection_scheduled', 'Inspection Scheduled'),
            ('inspection_completed', 'Inspection Completed'),
            ('e6_generated', 'E6 Certificate Generated'),
            ('e1_generated', 'E1 Defect Report Generated'),
            ('workflow_completed', 'Workflow Completed'),
        ]
    )
    current_step = serializers.IntegerField(min_value=1)
    reinspection_count = serializers.IntegerField(min_value=0, default=0)

    # Metadata
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class BulkSyncDataSerializer(serializers.Serializer):
    """
    Serializer for bulk sync operations
    """
    operation_type = serializers.ChoiceField(
        choices=[
            ('inspections_bulk_create', 'Bulk Create Inspections'),
            ('inspections_bulk_update', 'Bulk Update Inspections'),
            ('photos_bulk_upload', 'Bulk Upload Photos'),
        ]
    )
    data = serializers.ListField(child=serializers.DictField())
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],
        default='normal'
    )

    def validate_data(self, value):
        """
        Validate bulk data
        """
        if not value:
            raise serializers.ValidationError("Data list cannot be empty")

        if len(value) > 1000:
            raise serializers.ValidationError("Cannot process more than 1000 items at once")

        # Validate each item based on operation type
        operation_type = self.initial_data.get('operation_type')

        for item in value:
            if operation_type == 'inspections_bulk_create':
                serializer = InspectionSyncDataSerializer(data=item)
                if not serializer.is_valid():
                    raise serializers.ValidationError(f"Invalid inspection data: {serializer.errors}")
            elif operation_type == 'inspections_bulk_update':
                if not item.get('id'):
                    raise serializers.ValidationError("ID is required for update operations")
                serializer = InspectionSyncDataSerializer(data=item)
                if not serializer.is_valid():
                    raise serializers.ValidationError(f"Invalid inspection data: {serializer.errors}")

        return value


class SyncStatusSummarySerializer(serializers.Serializer):
    """
    Serializer for sync status summary
    """
    recent_syncs_count = serializers.IntegerField()
    successful_syncs_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    pending_uploads = serializers.IntegerField()
    unresolved_conflicts = serializers.IntegerField()
    last_sync = serializers.DateTimeField(allow_null=True)
    sync_health = serializers.ChoiceField(
        choices=[('good', 'Good'), ('warning', 'Warning'), ('critical', 'Critical')]
    )


class AssignmentSyncDataSerializer(serializers.Serializer):
    """
    Serializer for assignment data during sync operations
    """
    id = serializers.UUIDField(required=False)
    application = serializers.UUIDField()
    assigned_to = serializers.UUIDField()
    assigned_by = serializers.UUIDField()
    assignment_date = serializers.DateTimeField()
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    assignment_notes = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=[
            ('assigned', 'Assigned'),
            ('accepted', 'Accepted'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ]
    )
    accepted_date = serializers.DateTimeField(required=False, allow_null=True)
    completed_date = serializers.DateTimeField(required=False, allow_null=True)
    completion_notes = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ApprovalSyncDataSerializer(serializers.Serializer):
    """
    Serializer for approval data during sync operations
    """
    id = serializers.UUIDField(required=False)
    step = serializers.IntegerField()
    user = serializers.UUIDField()
    process = serializers.UUIDField()
    comment = serializers.CharField(max_length=200, required=False, allow_blank=True)
    approved = serializers.ChoiceField(
        choices=[
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected'),
        ],
        required=False, allow_null=True
    )
    approved_at = serializers.DateTimeField(required=False, allow_null=True)


class AssignmentBatchSerializer(serializers.Serializer):
    """
    Serializer for batch assignment operations
    """
    assignments = serializers.ListField(child=AssignmentSyncDataSerializer())
    operation_type = serializers.ChoiceField(
        choices=[
            ('bulk_create', 'Bulk Create'),
            ('bulk_update', 'Bulk Update'),
            ('bulk_status_change', 'Bulk Status Change'),
        ]
    )


class ApprovalTransitionSerializer(serializers.Serializer):
    """
    Serializer for approval workflow transitions
    """
    process_id = serializers.UUIDField()
    step_id = serializers.IntegerField()
    action = serializers.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('request_changes', 'Request Changes'),
        ]
    )
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)


class MergeOperationSerializer(serializers.Serializer):
    """
    Serializer for merge operation requests
    """
    entity_type = serializers.CharField(max_length=50)
    entity_id = serializers.UUIDField()
    merge_strategy = serializers.ChoiceField(
        choices=[
            ('server_wins', 'Server Data Takes Precedence'),
            ('local_wins', 'Local Data Takes Precedence'),
            ('intelligent_merge', 'Intelligent Merge'),
            ('manual_merge', 'Manual Merge Required'),
        ]
    )
    conflict_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    resolved_data = serializers.DictField(required=False)


class IntelligentMergeSuggestionSerializer(serializers.Serializer):
    """
    Serializer for intelligent merge suggestions
    """
    entity_type = serializers.CharField(max_length=50)
    entity_id = serializers.UUIDField()
    local_data = serializers.DictField()
    server_data = serializers.DictField()
    suggested_resolution = serializers.ChoiceField(
        choices=[
            ('server_wins', 'Use Server Data'),
            ('local_wins', 'Use Local Data'),
            ('merged', 'Merge Data'),
        ]
    )
    suggested_merged_data = serializers.DictField(required=False)
    confidence_score = serializers.FloatField(min_value=0, max_value=1)
    reasoning = serializers.CharField()
