"""
URL patterns for sync operations
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SyncOperationViewSet,
    UploadQueueViewSet,
    ConflictResolutionViewSet,
    sync_inspection_data,
    sync_workflow_data,
    bulk_sync_data,
    sync_inspection_batch,
    download_inspection_batch,
    incremental_sync_inspections,
    get_inspection_conflicts,
    resolve_inspection_conflict,
    sync_status_summary,
    sync_dashboard_data,
    sync_assignment_data,
    sync_assignment_batch,
    get_assignment_conflicts,
    resolve_assignment_conflict,
    sync_approval_data,
    sync_approval_transition,
    get_approval_conflicts,
    resolve_approval_conflict,
    bulk_merge_operations,
    intelligent_merge_suggestion
)

router = DefaultRouter()
router.register(r'operations', SyncOperationViewSet, basename='sync-operations')
router.register(r'queue', UploadQueueViewSet, basename='upload-queue')
router.register(r'conflicts', ConflictResolutionViewSet, basename='conflicts')

urlpatterns = [
    path('', include(router.urls)),
    path('sync-inspection/', sync_inspection_data, name='sync-inspection'),
    path('sync-workflow/', sync_workflow_data, name='sync-workflow'),
    path('bulk-sync/', bulk_sync_data, name='bulk-sync'),
    path('sync-inspection-batch/', sync_inspection_batch, name='sync-inspection-batch'),
    path('download-inspection-batch/', download_inspection_batch, name='download-inspection-batch'),
    path('incremental-sync/', incremental_sync_inspections, name='incremental-sync-inspections'),
    path('inspection-conflicts/', get_inspection_conflicts, name='get-inspection-conflicts'),
    path('resolve-conflict/<uuid:conflict_id>/', resolve_inspection_conflict, name='resolve-inspection-conflict'),
    path('status-summary/', sync_status_summary, name='sync-status-summary'),
    path('dashboard/', sync_dashboard_data, name='sync-dashboard'),

    # Assignment sync endpoints
    path('assignments/sync/', sync_assignment_data, name='sync-assignment'),
    path('assignments/batch/', sync_assignment_batch, name='sync-assignment-batch'),
    path('assignments/conflicts/', get_assignment_conflicts, name='get-assignment-conflicts'),
    path('assignments/resolve-conflict/<uuid:conflict_id>/', resolve_assignment_conflict, name='resolve-assignment-conflict'),

    # Approval sync endpoints
    path('approvals/sync/', sync_approval_data, name='sync-approval'),
    path('approvals/transition/', sync_approval_transition, name='sync-approval-transition'),
    path('approvals/conflicts/', get_approval_conflicts, name='get-approval-conflicts'),
    path('approvals/resolve-conflict/<uuid:conflict_id>/', resolve_approval_conflict, name='resolve-approval-conflict'),

    # Merge operation endpoints
    path('merge/bulk/', bulk_merge_operations, name='bulk-merge-operations'),
    path('merge/suggest/', intelligent_merge_suggestion, name='intelligent-merge-suggestion'),
]
