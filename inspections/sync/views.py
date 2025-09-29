"""
API views for sync operations
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging

from ..models import InspectionReport, ClientApplication, InspectionWorkflow, ApplicationAssignment
from approve.models import Approval, Process, Step, Workflow
from .models import SyncOperation, UploadQueue, ConflictResolution
from .serializers import (
    SyncOperationSerializer,
    UploadQueueSerializer,
    ConflictResolutionSerializer,
    InspectionSyncDataSerializer,
    WorkflowSyncDataSerializer,
    BulkSyncDataSerializer,
    SyncStatusSummarySerializer,
    AssignmentSyncDataSerializer,
    AssignmentBatchSerializer,
    ApprovalSyncDataSerializer,
    ApprovalTransitionSerializer,
    MergeOperationSerializer,
    IntelligentMergeSuggestionSerializer
)
from .service import InspectionSyncService
from .utils import get_sync_status_summary, create_sync_metadata

logger = logging.getLogger(__name__)


class SyncOperationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sync operations
    """
    serializer_class = SyncOperationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to user's sync operations"""
        return SyncOperation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user when creating sync operation"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def start_sync(self, request):
        """
        Start a sync operation
        """
        sync_type = request.data.get('sync_type', 'incremental')
        sync_direction = request.data.get('sync_direction', 'both')

        service = InspectionSyncService()
        sync_op = service.start_sync_operation(sync_type, request.user, sync_direction)

        serializer = self.get_serializer(sync_op)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def full_sync(self, request):
        """
        Perform a full sync
        """
        service = InspectionSyncService()
        results = service.perform_full_sync(request.user)

        return Response({
            'success': results['success'],
            'records_processed': results['records_processed'],
            'conflicts_resolved': results['conflicts_resolved'],
            'errors': results['errors']
        })

    @action(detail=False, methods=['post'])
    def incremental_sync(self, request):
        """
        Perform an incremental sync
        """
        since_timestamp = request.data.get('since_timestamp')
        if since_timestamp:
            try:
                since_timestamp = timezone.datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("Invalid timestamp format")

        service = InspectionSyncService()
        results = service.perform_incremental_sync(request.user, since_timestamp)

        return Response({
            'success': results['success'],
            'records_processed': results['records_processed'],
            'conflicts_resolved': results['conflicts_resolved'],
            'errors': results['errors']
        })


class UploadQueueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for upload queue management
    """
    serializer_class = UploadQueueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to user's upload queue items"""
        return UploadQueue.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """Set the user when creating queue item"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def add_inspection(self, request):
        """
        Add inspection data to upload queue
        """
        data = request.data.copy()
        data['operation_type'] = 'inspection_create'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        queue_item = serializer.save(created_by=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def process_queue(self, request):
        """
        Manually trigger queue processing
        """
        from .service import UploadQueueManager

        manager = UploadQueueManager()
        batch_size = request.data.get('batch_size', 10)

        manager.process_queue_batch(batch_size)

        return Response({'message': f'Processed up to {batch_size} queue items'})


class ConflictResolutionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for conflict resolution
    """
    serializer_class = ConflictResolutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to user's conflicts"""
        return ConflictResolution.objects.filter(
            sync_operation__user=self.request.user
        )

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Manually resolve a conflict
        """
        conflict = self.get_object()
        resolution = request.data.get('resolution')
        resolved_data = request.data.get('resolved_data')
        notes = request.data.get('notes')

        if resolution not in ['server_wins', 'local_wins', 'merged']:
            raise ValidationError("Invalid resolution type")

        if resolution == 'merged' and not resolved_data:
            raise ValidationError("Resolved data is required for merged resolution")

        # Apply resolution
        if resolution == 'server_wins':
            conflict.resolve_with_server_data(notes)
        elif resolution == 'local_wins':
            conflict.resolve_with_local_data(notes)
        elif resolution == 'merged':
            conflict.resolve_with_merged_data(resolved_data, notes)

        conflict.resolved_by = request.user
        conflict.save()

        serializer = self.get_serializer(conflict)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_inspection_data(request):
    """
    Sync inspection data (create or update)
    """
    serializer = InspectionSyncDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    inspection_id = data.get('id')

    # Check for existing inspection
    if inspection_id:
        inspection = get_object_or_404(InspectionReport, id=inspection_id)
        # Update existing
        for key, value in data.items():
            if key not in ['id', 'created_at']:
                setattr(inspection, key, value)
        inspection.save()
        action = 'updated'
    else:
        # Create new
        inspection = InspectionReport.objects.create(**data)
        action = 'created'

    # Create sync operation record
    sync_op = SyncOperation.objects.create(
        operation_type='upload',
        user=request.user,
        status='completed',
        records_affected=1,
        metadata=create_sync_metadata('inspection_sync', 1, {'action': action})
    )

    response_serializer = InspectionSyncDataSerializer(inspection)
    return Response({
        'success': True,
        'action': action,
        'inspection': response_serializer.data,
        'sync_operation': sync_op.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_workflow_data(request):
    """
    Sync workflow data
    """
    serializer = WorkflowSyncDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    workflow_id = data.get('id')

    if workflow_id:
        workflow = get_object_or_404(InspectionWorkflow, id=workflow_id)
        for key, value in data.items():
            if key not in ['id', 'created_at', 'workflow_number']:
                setattr(workflow, key, value)
        workflow.save()
        action = 'updated'
    else:
        workflow = InspectionWorkflow.objects.create(**data)
        action = 'created'

    sync_op = SyncOperation.objects.create(
        operation_type='upload',
        user=request.user,
        status='completed',
        records_affected=1,
        metadata=create_sync_metadata('workflow_sync', 1, {'action': action})
    )

    response_serializer = WorkflowSyncDataSerializer(workflow)
    return Response({
        'success': True,
        'action': action,
        'workflow': response_serializer.data,
        'sync_operation': sync_op.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_data(request):
    """
    Perform bulk sync operations
    """
    serializer = BulkSyncDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    operation_type = serializer.validated_data['operation_type']
    data_list = serializer.validated_data['data']
    priority = serializer.validated_data['priority']

    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    # Process each item in the bulk operation
    for i, item_data in enumerate(data_list):
        try:
            if operation_type == 'inspections_bulk_create':
                # Create queue items for each inspection
                for inspection_data in data_list:
                    queue_item = UploadQueue.objects.create(
                        operation_type='inspection_create',
                        data=inspection_data,
                        priority=priority,
                        entity_type='inspection',
                        created_by=request.user
                    )
                    results['processed'] += 1
                    results['successful'] += 1

            elif operation_type == 'inspections_bulk_update':
                # Create queue items for each update
                for inspection_data in data_list:
                    if inspection_data.get('id'):
                        queue_item = UploadQueue.objects.create(
                            operation_type='inspection_update',
                            data=inspection_data,
                            priority=priority,
                            entity_type='inspection',
                            entity_id=inspection_data['id'],
                            created_by=request.user
                        )
                        results['processed'] += 1
                        results['successful'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Item {i}: {str(e)}")

    # Create sync operation record
    sync_op = SyncOperation.objects.create(
        operation_type='upload',
        user=request.user,
        status='completed' if results['failed'] == 0 else 'failed',
        records_affected=results['successful'],
        metadata=create_sync_metadata('bulk_sync', results['processed'], {
            'operation_type': operation_type,
            'failed_count': results['failed']
        })
    )

    return Response({
        'success': results['failed'] == 0,
        'results': results,
        'sync_operation': sync_op.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_inspection_batch(request):
    """
    Sync multiple inspection records in batch
    """
    inspections_data = request.data.get('inspections', [])
    if not inspections_data:
        return Response({
            'success': False,
            'error': 'No inspection data provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    service = InspectionSyncService()
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    for i, inspection_data in enumerate(inspections_data):
        try:
            result = service.sync_inspection_data(inspection_data, request.user)
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'index': i,
                    'errors': result.get('errors', ['Unknown error'])
                })
            results['processed'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'index': i,
                'errors': [str(e)]
            })

    return Response({
        'success': results['failed'] == 0,
        'results': results
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_inspection_batch(request):
    """
    Download inspection data for multiple IDs
    """
    inspection_ids = request.GET.getlist('ids')
    if not inspection_ids:
        return Response({
            'success': False,
            'error': 'No inspection IDs provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    service = InspectionSyncService()
    result = service.download_inspection_data(inspection_ids, request.user)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def incremental_sync_inspections(request):
    """
    Perform incremental sync for inspections since timestamp
    """
    since_timestamp = request.data.get('since_timestamp')
    if since_timestamp:
        try:
            since_timestamp = timezone.datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid timestamp format'
            }, status=status.HTTP_400_BAD_REQUEST)

    service = InspectionSyncService()
    results = service.perform_incremental_sync(request.user, since_timestamp)

    return Response({
        'success': results['success'],
        'records_processed': results['records_processed'],
        'conflicts_resolved': results['conflicts_resolved'],
        'errors': results['errors']
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_inspection_conflicts(request):
    """
    Get unresolved inspection conflicts for the current user
    """
    conflicts = ConflictResolution.objects.filter(
        sync_operation__user=request.user,
        resolution='manual',
        conflict_type='inspection_data'
    ).order_by('-resolved_at')

    serializer = ConflictResolutionSerializer(conflicts, many=True)
    return Response({
        'success': True,
        'conflicts': serializer.data,
        'count': conflicts.count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_inspection_conflict(request, conflict_id):
    """
    Manually resolve an inspection conflict
    """
    try:
        conflict = ConflictResolution.objects.get(
            id=conflict_id,
            sync_operation__user=request.user,
            resolution='manual'
        )
    except ConflictResolution.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conflict not found or already resolved'
        }, status=status.HTTP_404_NOT_FOUND)

    resolution = request.data.get('resolution')
    resolved_data = request.data.get('resolved_data')
    notes = request.data.get('notes')

    if resolution not in ['server_wins', 'local_wins', 'merged']:
        return Response({
            'success': False,
            'error': 'Invalid resolution type'
        }, status=status.HTTP_400_BAD_REQUEST)

    if resolution == 'merged' and not resolved_data:
        return Response({
            'success': False,
            'error': 'Resolved data is required for merged resolution'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Apply resolution
    if resolution == 'server_wins':
        conflict.resolve_with_server_data(notes)
    elif resolution == 'local_wins':
        conflict.resolve_with_local_data(notes)
    elif resolution == 'merged':
        conflict.resolve_with_merged_data(resolved_data, notes)

    conflict.resolved_by = request.user
    conflict.save()

    serializer = ConflictResolutionSerializer(conflict)
    return Response({
        'success': True,
        'conflict': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_status_summary(request):
    """
    Get sync status summary for the current user
    """
    summary = get_sync_status_summary(request.user)
    serializer = SyncStatusSummarySerializer(summary)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_dashboard_data(request):
    """
    Get comprehensive sync dashboard data
    """
    # Get recent sync operations
    recent_syncs = SyncOperation.objects.filter(
        user=request.user,
        started_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).order_by('-started_at')[:10]

    # Get pending uploads
    pending_uploads = UploadQueue.objects.filter(
        created_by=request.user,
        status='pending'
    ).count()

    # Get unresolved conflicts
    unresolved_conflicts = ConflictResolution.objects.filter(
        sync_operation__user=request.user,
        resolution='manual'
    ).count()

    # Get sync statistics
    total_syncs = recent_syncs.count()
    successful_syncs = recent_syncs.filter(status='completed').count()
    failed_syncs = recent_syncs.filter(status='failed').count()

    return Response({
        'recent_syncs': SyncOperationSerializer(recent_syncs, many=True).data,
        'pending_uploads': pending_uploads,
        'unresolved_conflicts': unresolved_conflicts,
        'statistics': {
            'total_syncs': total_syncs,
            'successful_syncs': successful_syncs,
            'failed_syncs': failed_syncs,
            'success_rate': (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_assignment_data(request):
    """
    Sync assignment data (create or update)
    """
    serializer = AssignmentSyncDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    assignment_id = data.get('id')

    try:
        # Check for existing assignment
        if assignment_id:
            assignment = get_object_or_404(ApplicationAssignment, id=assignment_id)
            # Update existing
            for key, value in data.items():
                if key not in ['id', 'created_at']:
                    setattr(assignment, key, value)
            assignment.save()
            action = 'updated'
        else:
            # Create new
            assignment = ApplicationAssignment.objects.create(**data)
            action = 'created'

        # Create sync operation record
        sync_op = SyncOperation.objects.create(
            operation_type='upload',
            user=request.user,
            status='completed',
            records_affected=1,
            metadata=create_sync_metadata('assignment_sync', 1, {'action': action})
        )

        response_serializer = AssignmentSyncDataSerializer(assignment)
        return Response({
            'success': True,
            'action': action,
            'assignment': response_serializer.data,
            'sync_operation': sync_op.id
        })

    except Exception as e:
        logger.error(f"Error syncing assignment: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_assignment_batch(request):
    """
    Sync multiple assignment records in batch
    """
    serializer = AssignmentBatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    assignments_data = serializer.validated_data['assignments']
    operation_type = serializer.validated_data['operation_type']

    if not assignments_data:
        return Response({
            'success': False,
            'error': 'No assignment data provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    service = InspectionSyncService()
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    for i, assignment_data in enumerate(assignments_data):
        try:
            if operation_type == 'bulk_create':
                # Create assignment
                assignment = ApplicationAssignment.objects.create(**assignment_data)
                results['successful'] += 1
            elif operation_type == 'bulk_update':
                # Update assignment
                assignment_id = assignment_data.get('id')
                if not assignment_id:
                    results['failed'] += 1
                    results['errors'].append({
                        'index': i,
                        'errors': ['ID required for update operations']
                    })
                    continue

                assignment = get_object_or_404(ApplicationAssignment, id=assignment_id)
                for key, value in assignment_data.items():
                    if key not in ['id', 'created_at']:
                        setattr(assignment, key, value)
                assignment.save()
                results['successful'] += 1
            elif operation_type == 'bulk_status_change':
                # Change assignment status
                assignment_id = assignment_data.get('id')
                new_status = assignment_data.get('status')

                if not assignment_id or not new_status:
                    results['failed'] += 1
                    results['errors'].append({
                        'index': i,
                        'errors': ['ID and status required for status change']
                    })
                    continue

                assignment = get_object_or_404(ApplicationAssignment, id=assignment_id)
                old_status = assignment.status
                assignment.status = new_status

                # Update timestamps based on status
                if new_status == 'accepted' and old_status == 'assigned':
                    assignment.accepted_date = timezone.now()
                elif new_status == 'completed':
                    assignment.completed_date = timezone.now()

                assignment.save()
                results['successful'] += 1

            results['processed'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'index': i,
                'errors': [str(e)]
            })

    return Response({
        'success': results['failed'] == 0,
        'results': results
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_conflicts(request):
    """
    Get unresolved assignment conflicts for the current user
    """
    conflicts = ConflictResolution.objects.filter(
        sync_operation__user=request.user,
        resolution='manual',
        conflict_type__in=['assignment', 'assignment_status']
    ).order_by('-resolved_at')

    serializer = ConflictResolutionSerializer(conflicts, many=True)
    return Response({
        'success': True,
        'conflicts': serializer.data,
        'count': conflicts.count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_assignment_conflict(request, conflict_id):
    """
    Manually resolve an assignment conflict
    """
    try:
        conflict = ConflictResolution.objects.get(
            id=conflict_id,
            sync_operation__user=request.user,
            resolution='manual',
            conflict_type__in=['assignment', 'assignment_status']
        )
    except ConflictResolution.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conflict not found or already resolved'
        }, status=status.HTTP_404_NOT_FOUND)

    resolution = request.data.get('resolution')
    resolved_data = request.data.get('resolved_data')
    notes = request.data.get('notes')

    if resolution not in ['server_wins', 'local_wins', 'merged']:
        return Response({
            'success': False,
            'error': 'Invalid resolution type'
        }, status=status.HTTP_400_BAD_REQUEST)

    if resolution == 'merged' and not resolved_data:
        return Response({
            'success': False,
            'error': 'Resolved data is required for merged resolution'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Apply resolution
    if resolution == 'server_wins':
        conflict.resolve_with_server_data(notes)
    elif resolution == 'local_wins':
        conflict.resolve_with_local_data(notes)
    elif resolution == 'merged':
        conflict.resolve_with_merged_data(resolved_data, notes)

    conflict.resolved_by = request.user
    conflict.save()

    serializer = ConflictResolutionSerializer(conflict)
    return Response({
        'success': True,
        'conflict': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_approval_data(request):
    """
    Sync approval data (create or update)
    """
    serializer = ApprovalSyncDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    approval_id = data.get('id')

    try:
        # Check for existing approval
        if approval_id:
            approval = get_object_or_404(Approval, id=approval_id)
            # Update existing
            for key, value in data.items():
                if key not in ['id']:
                    setattr(approval, key, value)
            approval.save()
            action = 'updated'
        else:
            # Create new
            approval = Approval.objects.create(**data)
            action = 'created'

        # Create sync operation record
        sync_op = SyncOperation.objects.create(
            operation_type='upload',
            user=request.user,
            status='completed',
            records_affected=1,
            metadata=create_sync_metadata('approval_sync', 1, {'action': action})
        )

        response_serializer = ApprovalSyncDataSerializer(approval)
        return Response({
            'success': True,
            'action': action,
            'approval': response_serializer.data,
            'sync_operation': sync_op.id
        })

    except Exception as e:
        logger.error(f"Error syncing approval: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_approval_transition(request):
    """
    Handle approval workflow transitions
    """
    serializer = ApprovalTransitionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    process_id = data['process_id']
    step_id = data['step_id']
    action = data['action']
    comment = data.get('comment', '')

    try:
        # Get the process and step
        process = get_object_or_404(Process, id=process_id)
        step = get_object_or_404(Step, id=step_id)

        # Create or update approval record
        approval, created = Approval.objects.get_or_create(
            step=step,
            user=request.user,
            process=process,
            defaults={
                'comment': comment,
                'approved': 'Approved' if action == 'approve' else 'Rejected'
            }
        )

        if not created:
            # Update existing approval
            approval.comment = comment
            approval.approved = 'Approved' if action == 'approve' else 'Rejected'
            approval.approved_at = timezone.now()
            approval.save()

        # Create sync operation record
        sync_op = SyncOperation.objects.create(
            operation_type='upload',
            user=request.user,
            status='completed',
            records_affected=1,
            metadata=create_sync_metadata('approval_transition', 1, {
                'action': action,
                'process_id': str(process_id),
                'step_id': step_id
            })
        )

        return Response({
            'success': True,
            'action': action,
            'approval': ApprovalSyncDataSerializer(approval).data,
            'sync_operation': sync_op.id
        })

    except Exception as e:
        logger.error(f"Error in approval transition: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_approval_conflicts(request):
    """
    Get unresolved approval conflicts for the current user
    """
    conflicts = ConflictResolution.objects.filter(
        sync_operation__user=request.user,
        resolution='manual',
        conflict_type__in=['approval', 'approval_state']
    ).order_by('-resolved_at')

    serializer = ConflictResolutionSerializer(conflicts, many=True)
    return Response({
        'success': True,
        'conflicts': serializer.data,
        'count': conflicts.count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_approval_conflict(request, conflict_id):
    """
    Manually resolve an approval conflict
    """
    try:
        conflict = ConflictResolution.objects.get(
            id=conflict_id,
            sync_operation__user=request.user,
            resolution='manual',
            conflict_type__in=['approval', 'approval_state']
        )
    except ConflictResolution.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conflict not found or already resolved'
        }, status=status.HTTP_404_NOT_FOUND)

    resolution = request.data.get('resolution')
    resolved_data = request.data.get('resolved_data')
    notes = request.data.get('notes')

    if resolution not in ['server_wins', 'local_wins', 'merged']:
        return Response({
            'success': False,
            'error': 'Invalid resolution type'
        }, status=status.HTTP_400_BAD_REQUEST)

    if resolution == 'merged' and not resolved_data:
        return Response({
            'success': False,
            'error': 'Resolved data is required for merged resolution'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Apply resolution
    if resolution == 'server_wins':
        conflict.resolve_with_server_data(notes)
    elif resolution == 'local_wins':
        conflict.resolve_with_local_data(notes)
    elif resolution == 'merged':
        conflict.resolve_with_merged_data(resolved_data, notes)

    conflict.resolved_by = request.user
    conflict.save()

    serializer = ConflictResolutionSerializer(conflict)
    return Response({
        'success': True,
        'conflict': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_merge_operations(request):
    """
    Perform bulk merge operations on conflicting data
    """
    serializer = MergeOperationSerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)

    merge_operations = serializer.validated_data
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    for i, merge_op_data in enumerate(merge_operations):
        try:
            entity_type = merge_op_data['entity_type']
            entity_id = merge_op_data['entity_id']
            merge_strategy = merge_op_data['merge_strategy']
            conflict_fields = merge_op_data.get('conflict_fields', [])
            resolved_data = merge_op_data.get('resolved_data')

            # Find existing conflict
            try:
                conflict = ConflictResolution.objects.get(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    resolution='manual'
                )

                # Apply merge strategy
                if merge_strategy == 'server_wins':
                    conflict.resolve_with_server_data()
                    results['successful'] += 1
                elif merge_strategy == 'local_wins':
                    conflict.resolve_with_local_data()
                    results['successful'] += 1
                elif merge_strategy == 'intelligent_merge':
                    # Apply intelligent merge logic
                    merged_data = _perform_intelligent_merge(
                        conflict.local_data,
                        conflict.server_data,
                        conflict_fields
                    )
                    conflict.resolve_with_merged_data(merged_data)
                    results['successful'] += 1
                elif merge_strategy == 'manual_merge':
                    if not resolved_data:
                        results['failed'] += 1
                        results['errors'].append({
                            'index': i,
                            'errors': ['Resolved data required for manual merge']
                        })
                        continue
                    conflict.resolve_with_merged_data(resolved_data)
                    results['successful'] += 1

                conflict.resolved_by = request.user
                conflict.save()

            except ConflictResolution.DoesNotExist:
                results['failed'] += 1
                results['errors'].append({
                    'index': i,
                    'errors': ['No conflict found for entity']
                })
                continue

            results['processed'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'index': i,
                'errors': [str(e)]
            })

    # Create sync operation record
    sync_op = SyncOperation.objects.create(
        operation_type='upload',
        user=request.user,
        status='completed' if results['failed'] == 0 else 'failed',
        records_affected=results['successful'],
        metadata=create_sync_metadata('bulk_merge', results['processed'], {
            'merge_operations': len(merge_operations),
            'failed_count': results['failed']
        })
    )

    return Response({
        'success': results['failed'] == 0,
        'results': results,
        'sync_operation': sync_op.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intelligent_merge_suggestion(request):
    """
    Get intelligent merge suggestions for conflicting data
    """
    serializer = IntelligentMergeSuggestionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    entity_type = data['entity_type']
    entity_id = data['entity_id']
    local_data = data['local_data']
    server_data = data['server_data']

    try:
        # Find existing conflict
        conflict = ConflictResolution.objects.get(
            entity_type=entity_type,
            entity_id=entity_id,
            resolution='manual'
        )

        # Generate intelligent merge suggestion
        suggestion = _generate_merge_suggestion(
            local_data,
            server_data,
            conflict.conflict_type
        )

        return Response({
            'success': True,
            'suggestion': suggestion
        })

    except ConflictResolution.DoesNotExist:
        return Response({
            'success': False,
            'error': 'No conflict found for entity'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error generating merge suggestion: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _perform_intelligent_merge(local_data, server_data, conflict_fields):
    """
    Perform intelligent merge of conflicting data
    """
    merged_data = {}

    # For fields with conflicts, prefer more recent data or non-empty values
    for field in conflict_fields:
        local_value = local_data.get(field)
        server_value = server_data.get(field)

        if local_value != server_value:
            # Prefer non-empty values
            if local_value and not server_value:
                merged_data[field] = local_value
            elif server_value and not local_value:
                merged_data[field] = server_value
            elif local_value and server_value:
                # For timestamps, prefer more recent
                if field.endswith('_at') or field.endswith('_date'):
                    try:
                        local_time = timezone.datetime.fromisoformat(local_value.replace('Z', '+00:00'))
                        server_time = timezone.datetime.fromisoformat(server_value.replace('Z', '+00:00'))
                        merged_data[field] = local_value if local_time > server_time else server_value
                    except:
                        # Fallback to local data
                        merged_data[field] = local_value
                else:
                    # For other fields, prefer local data (user's data)
                    merged_data[field] = local_value
        else:
            merged_data[field] = local_value

    # Add non-conflicting fields
    for field, value in local_data.items():
        if field not in conflict_fields:
            merged_data[field] = value

    return merged_data


def _generate_merge_suggestion(local_data, server_data, conflict_type):
    """
    Generate intelligent merge suggestions
    """
    suggestion = {
        'suggested_resolution': 'merged',
        'confidence_score': 0.8,
        'reasoning': 'Intelligent merge based on data analysis',
        'suggested_merged_data': {}
    }

    # Analyze differences and generate suggestions
    differences = {}
    for field in local_data:
        if field in server_data and local_data[field] != server_data[field]:
            differences[field] = {
                'local': local_data[field],
                'server': server_data[field]
            }

    # Simple heuristic-based suggestions
    for field, values in differences.items():
        local_val = values['local']
        server_val = values['server']

        # For timestamps, suggest more recent
        if field.endswith('_at') or field.endswith('_date'):
            try:
                local_time = timezone.datetime.fromisoformat(local_val.replace('Z', '+00:00'))
                server_time = timezone.datetime.fromisoformat(server_val.replace('Z', '+00:00'))
                if local_time > server_time:
                    suggestion['suggested_merged_data'][field] = local_val
                else:
                    suggestion['suggested_merged_data'][field] = server_val
            except:
                suggestion['suggested_merged_data'][field] = local_val
        # For status fields, prefer more complete status
        elif field == 'status':
            status_priority = {
                'completed': 4,
                'in_progress': 3,
                'accepted': 2,
                'assigned': 1,
                'pending': 0
            }
            local_priority = status_priority.get(local_val, 0)
            server_priority = status_priority.get(server_val, 0)
            suggestion['suggested_merged_data'][field] = local_val if local_priority >= server_priority else server_val
        else:
            # Default to local data for other fields
            suggestion['suggested_merged_data'][field] = local_val

    return suggestion
