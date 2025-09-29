"""
Inspection Data Synchronization Service

This service handles the core synchronization logic for inspection data,
including upload queue management, conflict resolution, and sync status tracking.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from ..models import (
    InspectionReport,
    ClientApplication,
    InspectionWorkflow,
    ApplicationAssignment,
    E1DefectReport,
    E6Certificate
)
from .models import SyncOperation, UploadQueue, ConflictResolution

logger = logging.getLogger(__name__)


class InspectionSyncService:
    """
    Core service for managing inspection data synchronization
    """

    def __init__(self):
        self.sync_operation = None
        self.upload_queue_manager = UploadQueueManager()
        self.conflict_resolver = ConflictResolver()

    def start_sync_operation(self, operation_type: str, user, sync_direction: str = 'both') -> SyncOperation:
        """
        Start a new sync operation

        Args:
            operation_type: 'full', 'incremental', 'upload', or 'download'
            user: User performing the sync
            sync_direction: 'upload', 'download', or 'both'

        Returns:
            SyncOperation instance
        """
        self.sync_operation = SyncOperation.objects.create(
            operation_type=operation_type,
            user=user,
            sync_direction=sync_direction,
            status='in_progress'
        )

        logger.info(f"Started sync operation {self.sync_operation.id} for user {user.username}")
        return self.sync_operation

    def complete_sync_operation(self, records_affected: int = 0, error_message: str = None):
        """
        Complete the current sync operation

        Args:
            records_affected: Number of records processed
            error_message: Error message if operation failed
        """
        if self.sync_operation:
            self.sync_operation.mark_completed(records_affected, error_message)
            if error_message:
                logger.error(f"Sync operation {self.sync_operation.id} failed: {error_message}")
            else:
                logger.info(f"Sync operation {self.sync_operation.id} completed successfully")

    def perform_full_sync(self, user) -> Dict[str, Any]:
        """
        Perform a full synchronization for the user

        Args:
            user: User to sync for

        Returns:
            Dict with sync results
        """
        sync_op = self.start_sync_operation('full', user)
        results = {
            'success': True,
            'records_processed': 0,
            'conflicts_resolved': 0,
            'errors': []
        }

        try:
            # Download latest data from server
            download_results = self._download_latest_data(user)
            results['records_processed'] += download_results['records_processed']

            # Upload pending changes
            upload_results = self._upload_pending_changes(user)
            results['records_processed'] += upload_results['records_processed']

            # Resolve conflicts
            conflict_results = self._resolve_conflicts(user)
            results['conflicts_resolved'] = conflict_results['conflicts_resolved']

            # Update sync timestamp
            user.userprofile.last_sync_timestamp = timezone.now()
            user.userprofile.save()

        except Exception as e:
            logger.exception(f"Full sync failed for user {user.username}")
            results['success'] = False
            results['errors'].append(str(e))
            self.complete_sync_operation(error_message=str(e))
            return results

        self.complete_sync_operation(results['records_processed'])
        return results

    def perform_incremental_sync(self, user, since_timestamp: datetime = None) -> Dict[str, Any]:
        """
        Perform incremental synchronization since last sync

        Args:
            user: User to sync for
            since_timestamp: Only sync data changed since this timestamp

        Returns:
            Dict with sync results
        """
        sync_op = self.start_sync_operation('incremental', user)
        results = {
            'success': True,
            'records_processed': 0,
            'conflicts_resolved': 0,
            'errors': []
        }

        try:
            if since_timestamp is None:
                # Get user's last sync timestamp
                since_timestamp = getattr(user.userprofile, 'last_sync_timestamp', None)
                if since_timestamp is None:
                    # If no previous sync, do full sync
                    return self.perform_full_sync(user)

            # Download changes since timestamp
            download_results = self._download_changes_since(user, since_timestamp)
            results['records_processed'] += download_results['records_processed']

            # Upload pending changes
            upload_results = self._upload_pending_changes(user)
            results['records_processed'] += upload_results['records_processed']

            # Resolve conflicts
            conflict_results = self._resolve_conflicts(user)
            results['conflicts_resolved'] = conflict_results['conflicts_resolved']

        except Exception as e:
            logger.exception(f"Incremental sync failed for user {user.username}")
            results['success'] = False
            results['errors'].append(str(e))
            self.complete_sync_operation(error_message=str(e))
            return results

        self.complete_sync_operation(results['records_processed'])
        return results

    def _download_latest_data(self, user) -> Dict[str, Any]:
        """
        Download latest data from server for user
        """
        results = {'records_processed': 0}

        # Get user's assigned applications
        assignments = ApplicationAssignment.objects.filter(
            assigned_to=user,
            status__in=['assigned', 'accepted', 'in_progress']
        )

        for assignment in assignments:
            # Download inspection reports
            inspection_reports = InspectionReport.objects.filter(
                client_application=assignment.application
            )

            for report in inspection_reports:
                # Check for conflicts with local data
                local_report = self._get_local_inspection_report(report.id)
                if local_report:
                    conflicts = self._detect_inspection_conflicts(local_report, report)
                    if conflicts:
                        self.conflict_resolver.record_conflict(
                            'inspection_data',
                            'inspection',
                            report.id,
                            local_report.data,
                            self._serialize_inspection_for_sync(report),
                            self.sync_operation
                        )

                results['records_processed'] += 1

        return results

    def _download_changes_since(self, user, since_timestamp: datetime) -> Dict[str, Any]:
        """
        Download changes since specified timestamp
        """
        results = {'records_processed': 0}

        # Get user's assigned applications with recent changes
        assignments = ApplicationAssignment.objects.filter(
            assigned_to=user,
            updated_at__gt=since_timestamp
        )

        # Process changes...
        results['records_processed'] = assignments.count()

        return results

    def _upload_pending_changes(self, user) -> Dict[str, Any]:
        """
        Upload pending changes for user
        """
        results = {'records_processed': 0}

        # Process upload queue for this user
        pending_items = UploadQueue.objects.filter(
            created_by=user,
            status='pending'
        ).order_by('priority', 'created_at')

        for item in pending_items:
            try:
                self._process_upload_item(item)
                results['records_processed'] += 1
            except Exception as e:
                logger.error(f"Failed to process upload item {item.id}: {e}")
                item.mark_completed(str(e))

        return results

    def _process_upload_item(self, queue_item: UploadQueue):
        """
        Process a single upload queue item
        """
        queue_item.mark_processing()

        try:
            if queue_item.operation_type == 'inspection_create':
                self._create_inspection_from_queue(queue_item)
            elif queue_item.operation_type == 'inspection_update':
                self._update_inspection_from_queue(queue_item)
            elif queue_item.operation_type == 'photo_upload':
                self._upload_photo_from_queue(queue_item)
            elif queue_item.operation_type == 'assignment_create':
                self._create_assignment_from_queue(queue_item)
            elif queue_item.operation_type == 'assignment_update':
                self._update_assignment_from_queue(queue_item)
            elif queue_item.operation_type == 'assignment_accept':
                self._accept_assignment_from_queue(queue_item)
            elif queue_item.operation_type == 'assignment_complete':
                self._complete_assignment_from_queue(queue_item)
            elif queue_item.operation_type == 'approval_create':
                self._create_approval_from_queue(queue_item)
            elif queue_item.operation_type == 'approval_update':
                self._update_approval_from_queue(queue_item)
            elif queue_item.operation_type == 'approval_transition':
                self._transition_approval_from_queue(queue_item)
            elif queue_item.operation_type == 'merge_operation':
                self._process_merge_from_queue(queue_item)
            # Add other operation types as needed

            queue_item.mark_completed()

        except Exception as e:
            queue_item.mark_completed(str(e))
            raise

    def _resolve_conflicts(self, user) -> Dict[str, Any]:
        """
        Resolve conflicts for user
        """
        results = {'conflicts_resolved': 0}

        # Get unresolved conflicts for this user
        conflicts = ConflictResolution.objects.filter(
            sync_operation__user=user,
            resolution='manual'  # Only process manual resolution conflicts
        )

        for conflict in conflicts:
            # Apply automatic resolution rules
            if self._can_auto_resolve(conflict):
                self._auto_resolve_conflict(conflict)
                results['conflicts_resolved'] += 1

        return results

    def _detect_inspection_conflicts(self, local_data: Dict, server_data: Dict) -> List[str]:
        """
        Detect conflicts between local and server inspection data
        """
        conflicts = []

        # Check for timestamp conflicts
        local_updated = local_data.get('updated_at')
        server_updated = server_data.updated_at

        if local_updated and server_updated:
            if local_updated > server_updated:
                conflicts.append('local_data_newer')
            elif server_updated > local_updated:
                conflicts.append('server_data_newer')

        # Check for status conflicts
        if local_data.get('status') != server_data.status:
            conflicts.append('status_conflict')

        return conflicts

    def _can_auto_resolve(self, conflict: ConflictResolution) -> bool:
        """
        Check if conflict can be automatically resolved using business rules
        """
        if conflict.conflict_type == 'inspection_data':
            return self._can_auto_resolve_inspection_conflict(conflict)
        elif conflict.conflict_type == 'workflow_state':
            return self._can_auto_resolve_workflow_conflict(conflict)

        return False

    def _can_auto_resolve_inspection_conflict(self, conflict: ConflictResolution) -> bool:
        """
        Check if inspection conflict can be auto-resolved
        """
        local_data = conflict.local_data
        server_data = conflict.server_data

        # Business Rule 1: Server data wins for critical safety fields
        critical_safety_fields = [
            'all_equipment_bonded_earthed',
            'socket_outlets_earthed',
            'circuit_conductors_correct_size',
            'overhead_lines_protected',
            'motor_installations_protected'
        ]

        for field in critical_safety_fields:
            local_value = local_data.get(field)
            server_value = server_data.get(field)
            if local_value != server_value:
                # If server has 'pass' and local has 'fail', server wins
                if server_value == 'pass' and local_value == 'fail':
                    return True
                # If local has 'pass' and server has 'fail', local wins
                elif local_value == 'pass' and server_value == 'fail':
                    return True

        # Business Rule 2: Last write wins for non-critical fields
        local_updated = local_data.get('updated_at')
        server_updated = server_data.get('updated_at')

        if local_updated and server_updated:
            try:
                if isinstance(local_updated, str):
                    local_updated = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
                if isinstance(server_updated, str):
                    server_updated = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))

                # If difference is more than 5 minutes, use last write wins
                if abs((local_updated - server_updated).total_seconds()) > 300:
                    return True
            except ValueError:
                pass

        return False

    def _can_auto_resolve_workflow_conflict(self, conflict: ConflictResolution) -> bool:
        """
        Check if workflow conflict can be auto-resolved
        """
        local_data = conflict.local_data
        server_data = conflict.server_data

        # Business Rule: Cannot downgrade workflow status
        local_status = local_data.get('status')
        server_status = server_data.get('status')

        workflow_status_hierarchy = {
            'application_submitted': 1,
            'assigned': 2,
            'inspection_scheduled': 3,
            'inspection_completed': 4,
            'e6_generated': 5,
            'e1_generated': 6,
            'workflow_completed': 7
        }

        if local_status and server_status:
            local_level = workflow_status_hierarchy.get(local_status, 0)
            server_level = workflow_status_hierarchy.get(server_status, 0)

            # If server has higher status level, server wins
            if server_level > local_level:
                return True
            # If local has higher status level, local wins
            elif local_level > server_level:
                return True

        return False

    def _auto_resolve_conflict(self, conflict: ConflictResolution):
        """
        Automatically resolve a conflict using business rules
        """
        if conflict.conflict_type == 'inspection_data':
            self._auto_resolve_inspection_conflict(conflict)
        elif conflict.conflict_type == 'workflow_state':
            self._auto_resolve_workflow_conflict(conflict)

    def _auto_resolve_inspection_conflict(self, conflict: ConflictResolution):
        """
        Auto-resolve inspection conflict using business rules
        """
        local_data = conflict.local_data
        server_data = conflict.server_data

        # Apply business rules for inspection conflicts
        resolution_data = self._apply_inspection_business_rules(local_data, server_data)

        conflict.resolve_with_merged_data(
            resolution_data,
            "Auto-resolved using business rules"
        )

    def _auto_resolve_workflow_conflict(self, conflict: ConflictResolution):
        """
        Auto-resolve workflow conflict using business rules
        """
        local_data = conflict.local_data
        server_data = conflict.server_data

        # Apply business rules for workflow conflicts
        resolution_data = self._apply_workflow_business_rules(local_data, server_data)

        conflict.resolve_with_merged_data(
            resolution_data,
            "Auto-resolved using workflow business rules"
        )

    def _apply_inspection_business_rules(self, local_data: Dict, server_data: Dict) -> Dict:
        """
        Apply business rules to resolve inspection conflicts
        """
        resolved_data = server_data.copy()  # Start with server data as base

        # Business Rule 1: Safety-critical fields - more restrictive value wins
        safety_fields = [
            'all_equipment_bonded_earthed',
            'socket_outlets_earthed',
            'circuit_conductors_correct_size',
            'overhead_lines_protected',
            'motor_installations_protected'
        ]

        for field in safety_fields:
            local_value = local_data.get(field)
            server_value = server_data.get(field)

            if local_value != server_value:
                # If one is 'fail' and other is 'pass', 'fail' wins
                if local_value == 'fail' or server_value == 'fail':
                    resolved_data[field] = 'fail'
                # If one is 'pass' and other is 'na', 'pass' wins
                elif local_value == 'pass' or server_value == 'pass':
                    resolved_data[field] = 'pass'

        # Business Rule 2: Last write wins for other fields
        local_updated = local_data.get('updated_at')
        server_updated = server_data.get('updated_at')

        if local_updated and server_updated:
            try:
                if isinstance(local_updated, str):
                    local_updated = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
                if isinstance(server_updated, str):
                    server_updated = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))

                if local_updated > server_updated:
                    # Local data is newer, use local for non-safety fields
                    for key, value in local_data.items():
                        if key not in safety_fields and key not in ['updated_at', 'created_at']:
                            resolved_data[key] = value
            except ValueError:
                pass

        return resolved_data

    def _apply_workflow_business_rules(self, local_data: Dict, server_data: Dict) -> Dict:
        """
        Apply business rules to resolve workflow conflicts
        """
        resolved_data = server_data.copy()

        # Business Rule: Status hierarchy - higher status wins
        local_status = local_data.get('status')
        server_status = server_data.get('status')

        status_hierarchy = {
            'application_submitted': 1,
            'assigned': 2,
            'inspection_scheduled': 3,
            'inspection_completed': 4,
            'e6_generated': 5,
            'e1_generated': 6,
            'workflow_completed': 7
        }

        if local_status and server_status:
            local_level = status_hierarchy.get(local_status, 0)
            server_level = status_hierarchy.get(server_status, 0)

            if server_level > local_level:
                # Server has higher status, use server data
                resolved_data.update(server_data)
            elif local_level > server_level:
                # Local has higher status, use local data
                resolved_data.update(local_data)
            else:
                # Same status level, use last write wins
                local_updated = local_data.get('updated_at')
                server_updated = server_data.get('updated_at')

                if local_updated and server_updated:
                    try:
                        if isinstance(local_updated, str):
                            local_updated = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
                        if isinstance(server_updated, str):
                            server_updated = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))

                        if local_updated > server_updated:
                            resolved_data.update(local_data)
                        else:
                            resolved_data.update(server_data)
                    except ValueError:
                        resolved_data.update(server_data)

        return resolved_data

    def _get_local_inspection_report(self, report_id: str) -> Optional[Dict]:
        """
        Get local inspection report data (placeholder for mobile local storage)
        """
        # This would interface with mobile local storage
        # For now, return None to indicate no local data
        return None

    def _create_inspection_from_queue(self, queue_item: UploadQueue):
        """
        Create inspection from queue data
        """
        data = queue_item.data

        with transaction.atomic():
            # Create or update inspection report
            inspection, created = InspectionReport.objects.update_or_create(
                id=data.get('id'),
                defaults={
                    'inspection_date': data.get('inspection_date'),
                    'service_no': data.get('service_no'),
                    'consumer_name': data.get('consumer_name'),
                    # Add other fields as needed
                }
            )

            if created:
                logger.info(f"Created inspection report {inspection.id}")
            else:
                logger.info(f"Updated inspection report {inspection.id}")

    def _update_inspection_from_queue(self, queue_item: UploadQueue):
        """
        Update inspection from queue data
        """
        # Similar to create but for updates
        self._create_inspection_from_queue(queue_item)

    def _upload_photo_from_queue(self, queue_item: UploadQueue):
        """
        Upload photo from queue data
        """
        # Placeholder for photo upload logic
        logger.info(f"Photo upload processed for item {queue_item.id}")

    # === Phase 2: Inspection Data Synchronization ===

    def sync_inspection_data(self, inspection_data: Dict[str, Any], user) -> Dict[str, Any]:
        """
        Sync inspection data (create or update)

        Args:
            inspection_data: Inspection data to sync
            user: User performing the sync

        Returns:
            Dict with sync results
        """
        try:
            # Validate inspection data
            validation_errors = self._validate_inspection_data(inspection_data)
            if validation_errors:
                return {
                    'success': False,
                    'errors': validation_errors,
                    'message': 'Validation failed'
                }

            inspection_id = inspection_data.get('id')

            if inspection_id:
                # Update existing inspection
                result = self._update_inspection(inspection_id, inspection_data, user)
                action = 'updated'
            else:
                # Create new inspection
                result = self._create_inspection(inspection_data, user)
                action = 'created'

            # Create sync operation record
            sync_op = SyncOperation.objects.create(
                operation_type='upload',
                user=user,
                status='completed',
                records_affected=1,
                metadata=create_sync_metadata('inspection_sync', 1, {'action': action})
            )

            return {
                'success': True,
                'action': action,
                'inspection_id': result['inspection_id'],
                'sync_operation': sync_op.id
            }

        except Exception as e:
            logger.exception(f"Failed to sync inspection data: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'message': 'Sync failed'
            }

    def download_inspection_data(self, inspection_ids: List[str], user) -> Dict[str, Any]:
        """
        Download inspection data for specified IDs

        Args:
            inspection_ids: List of inspection IDs to download
            user: User requesting the download

        Returns:
            Dict with downloaded inspection data
        """
        try:
            inspections = InspectionReport.objects.filter(
                id__in=inspection_ids,
                client_application__assignments__assigned_to=user,
                client_application__assignments__status__in=['assigned', 'accepted', 'in_progress']
            )

            serialized_data = []
            for inspection in inspections:
                serialized_data.append(self._serialize_inspection_for_sync(inspection))

            return {
                'success': True,
                'inspections': serialized_data,
                'count': len(serialized_data)
            }

        except Exception as e:
            logger.exception(f"Failed to download inspection data: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'message': 'Download failed'
            }

    def _create_inspection(self, inspection_data: Dict[str, Any], user) -> Dict[str, Any]:
        """
        Create new inspection from sync data
        """
        with transaction.atomic():
            # Get the application
            application_id = inspection_data.get('client_application_id')
            if not application_id:
                raise ValidationError("client_application_id is required for new inspections")

            try:
                application = ClientApplication.objects.get(id=application_id)
            except ClientApplication.DoesNotExist:
                raise ValidationError(f"Application {application_id} not found")

            # Create inspection
            inspection = InspectionReport.objects.create(
                client_application=application,
                inspector=user,
                **{k: v for k, v in inspection_data.items()
                   if k not in ['id', 'client_application_id', 'created_at', 'updated_at']}
            )

            return {
                'inspection_id': inspection.id,
                'created': True
            }

    def _update_inspection(self, inspection_id: str, inspection_data: Dict[str, Any], user) -> Dict[str, Any]:
        """
        Update existing inspection from sync data
        """
        with transaction.atomic():
            try:
                inspection = InspectionReport.objects.get(id=inspection_id)
            except InspectionReport.DoesNotExist:
                raise ValidationError(f"Inspection {inspection_id} not found")

            # Check if user has permission to update this inspection
            if not self._user_can_access_inspection(user, inspection):
                raise ValidationError("User does not have permission to update this inspection")

            # Update inspection fields
            for key, value in inspection_data.items():
                if key not in ['id', 'created_at', 'updated_at', 'client_application', 'inspector']:
                    setattr(inspection, key, value)

            inspection.save()

            return {
                'inspection_id': inspection.id,
                'updated': True
            }

    def _validate_inspection_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate inspection data for sync
        """
        errors = []

        # Required fields
        required_fields = ['consumer_name', 'inspection_date']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Field '{field}' is required")

        # Date validation
        inspection_date = data.get('inspection_date')
        if inspection_date:
            try:
                if isinstance(inspection_date, str):
                    from datetime import datetime
                    inspection_date = datetime.fromisoformat(inspection_date.replace('Z', '+00:00'))
                if inspection_date.date() > timezone.now().date():
                    errors.append("Inspection date cannot be in the future")
            except ValueError:
                errors.append("Invalid inspection date format")

        # Status validation
        status = data.get('status')
        if status and status not in ['pass', 'fail', 'pending']:
            errors.append("Invalid status value")

        return errors

    def _serialize_inspection_for_sync(self, inspection: InspectionReport) -> Dict[str, Any]:
        """
        Serialize inspection for sync operations
        """
        from .utils import sanitize_sync_data

        data = {
            'id': str(inspection.id),
            'inspection_date': inspection.inspection_date.isoformat() if inspection.inspection_date else None,
            'service_no': inspection.service_no,
            'reason_for_inspection': inspection.reason_for_inspection,
            'consumer_name': inspection.consumer_name,
            'property_supplied': inspection.property_supplied,
            'property_owner_name': inspection.property_owner_name,
            'property_owner_address': inspection.property_owner_address,
            'contractor': inspection.contractor,
            'contractor_address': inspection.contractor_address,
            'size_of_mains': inspection.size_of_mains,
            'size_of_mains_conduit': inspection.size_of_mains_conduit,
            'consumer_main_switch_type': inspection.consumer_main_switch_type,
            'consumer_main_switch_capacity': inspection.consumer_main_switch_capacity,
            'consumer_main_switch_setting': inspection.consumer_main_switch_setting,
            'neutrals_fused': inspection.neutrals_fused,
            'neutral_block_fitted': inspection.neutral_block_fitted,
            'earth_electrode_installed': inspection.earth_electrode_installed,
            'earth_electrode_type': inspection.earth_electrode_type,
            'all_equipment_bonded_earthed': inspection.all_equipment_bonded_earthed,
            'insulation_resistance_between': inspection.insulation_resistance_between,
            'insulation_resistance_to_earth': inspection.insulation_resistance_to_earth,
            'earth_continuity_resistance': inspection.earth_continuity_resistance,
            'polarity_switches_plugs': inspection.polarity_switches_plugs,
            'socket_outlets_earthed': inspection.socket_outlets_earthed,
            'socket_outlet_type': inspection.socket_outlet_type,
            'wiring_type': inspection.wiring_type,
            'circuit_conductors_correct_size': inspection.circuit_conductors_correct_size,
            'wiring_condition': inspection.wiring_condition,
            'flexible_cord_prohibited_positions': inspection.flexible_cord_prohibited_positions,
            'bathroom_switch_accessible': inspection.bathroom_switch_accessible,
            'unearthed_metal_switches': inspection.unearthed_metal_switches,
            'conduits_bushed': inspection.conduits_bushed,
            'conduits_bonded_earth': inspection.conduits_bonded_earth,
            'conduits_correct_size': inspection.conduits_correct_size,
            'conduits_adequately_supported': inspection.conduits_adequately_supported,
            'conduits_suitable_type': inspection.conduits_suitable_type,
            'max_lighting_points_per_circuit': inspection.max_lighting_points_per_circuit,
            'max_plug_points_per_circuit': inspection.max_plug_points_per_circuit,
            'total_lighting_points': inspection.total_lighting_points,
            'total_plug_points': inspection.total_plug_points,
            'appliances_wattages': inspection.appliances_wattages,
            'motors_plant_details': inspection.motors_plant_details,
            'overhead_lines_height': inspection.overhead_lines_height,
            'overhead_lines_conductor_size': inspection.overhead_lines_conductor_size,
            'overhead_lines_support': inspection.overhead_lines_support,
            'overhead_lines_general': inspection.overhead_lines_general,
            'overhead_earthwires_fitted': inspection.overhead_earthwires_fitted,
            'overhead_lines_protected': inspection.overhead_lines_protected,
            'outbuildings_protected': inspection.outbuildings_protected,
            'motor_installations_protected': inspection.motor_installations_protected,
            'commission_switch_details': inspection.commission_switch_details,
            'supply_connected_disconnected': inspection.supply_connected_disconnected,
            'contractor_notified_defects': inspection.contractor_notified_defects,
            'other_features_attention': inspection.other_features_attention,
            'status': inspection.status,
            'client_application_id': str(inspection.client_application.id) if inspection.client_application else None,
            'created_at': inspection.created_at.isoformat() if inspection.created_at else None,
            'updated_at': inspection.updated_at.isoformat() if inspection.updated_at else None,
        }

        return sanitize_sync_data(data)

    def _user_can_access_inspection(self, user, inspection: InspectionReport) -> bool:
        """
        Check if user has permission to access/modify inspection
        """
        # User can access if they are the inspector or assigned to the application
        if inspection.inspector == user:
            return True

        assignment = ApplicationAssignment.objects.filter(
            application=inspection.client_application,
            assigned_to=user,
            status__in=['assigned', 'accepted', 'in_progress']
        ).first()

        return assignment is not None

    def _detect_inspection_conflicts(self, local_data: Dict, server_data: Dict) -> List[str]:
        """
        Detect conflicts between local and server inspection data
        """
        conflicts = []

        # Check for timestamp conflicts
        local_updated = local_data.get('updated_at')
        server_updated = server_data.get('updated_at')

        if local_updated and server_updated:
            try:
                if isinstance(local_updated, str):
                    local_updated = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
                if isinstance(server_updated, str):
                    server_updated = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))

                if abs((local_updated - server_updated).total_seconds()) < 1:  # Same timestamp
                    pass  # No conflict
                elif local_updated > server_updated:
                    conflicts.append('local_data_newer')
                else:
                    conflicts.append('server_data_newer')
            except ValueError:
                conflicts.append('timestamp_parse_error')

        # Check for critical field conflicts
        critical_fields = ['status', 'consumer_name', 'inspection_date']
        for field in critical_fields:
            if local_data.get(field) != server_data.get(field):
                conflicts.append(f'{field}_conflict')

        return conflicts

    # Assignment processing methods
    def _create_assignment_from_queue(self, queue_item: UploadQueue):
        """Create assignment from queue data"""
        from approve.models import Approval, Process, Step, Workflow

        data = queue_item.data
        assignment = ApplicationAssignment.objects.create(
            application_id=data['application'],
            assigned_to_id=data['assigned_to'],
            assigned_by_id=data['assigned_by'],
            assignment_date=data['assignment_date'],
            due_date=data.get('due_date'),
            assignment_notes=data.get('assignment_notes', ''),
            status=data.get('status', 'assigned')
        )
        logger.info(f"Created assignment {assignment.id} from queue")

    def _update_assignment_from_queue(self, queue_item: UploadQueue):
        """Update assignment from queue data"""
        data = queue_item.data
        assignment = ApplicationAssignment.objects.get(id=data['id'])
        for key, value in data.items():
            if key != 'id':
                setattr(assignment, key, value)
        assignment.save()
        logger.info(f"Updated assignment {assignment.id} from queue")

    def _accept_assignment_from_queue(self, queue_item: UploadQueue):
        """Accept assignment from queue data"""
        data = queue_item.data
        assignment = ApplicationAssignment.objects.get(id=data['id'])
        assignment.accept_assignment()
        logger.info(f"Accepted assignment {assignment.id} from queue")

    def _complete_assignment_from_queue(self, queue_item: UploadQueue):
        """Complete assignment from queue data"""
        data = queue_item.data
        assignment = ApplicationAssignment.objects.get(id=data['id'])
        assignment.complete_assignment(data.get('completion_notes'))
        logger.info(f"Completed assignment {assignment.id} from queue")

    # Approval processing methods
    def _create_approval_from_queue(self, queue_item: UploadQueue):
        """Create approval from queue data"""
        from approve.models import Approval, Process, Step, Workflow

        data = queue_item.data
        approval = Approval.objects.create(
            step_id=data['step'],
            user_id=data['user'],
            process_id=data['process'],
            comment=data.get('comment', ''),
            approved=data.get('approved')
        )
        logger.info(f"Created approval {approval.id} from queue")

    def _update_approval_from_queue(self, queue_item: UploadQueue):
        """Update approval from queue data"""
        from approve.models import Approval, Process, Step, Workflow

        data = queue_item.data
        approval = Approval.objects.get(id=data['id'])
        for key, value in data.items():
            if key != 'id':
                setattr(approval, key, value)
        approval.save()
        logger.info(f"Updated approval {approval.id} from queue")

    def _transition_approval_from_queue(self, queue_item: UploadQueue):
        """Handle approval transition from queue data"""
        from approve.models import Approval, Process, Step, Workflow

        data = queue_item.data
        process = Process.objects.get(id=data['process_id'])
        step = Step.objects.get(id=data['step_id'])

        approval, created = Approval.objects.get_or_create(
            step=step,
            user=queue_item.created_by,
            process=process,
            defaults={
                'comment': data.get('comment', ''),
                'approved': 'Approved' if data['action'] == 'approve' else 'Rejected'
            }
        )

        if not created:
            approval.comment = data.get('comment', '')
            approval.approved = 'Approved' if data['action'] == 'approve' else 'Rejected'
            approval.approved_at = timezone.now()
            approval.save()

        logger.info(f"Processed approval transition {approval.id} from queue")

    def _process_merge_from_queue(self, queue_item: UploadQueue):
        """Process merge operation from queue data"""
        data = queue_item.data
        entity_type = data['entity_type']
        entity_id = data['entity_id']
        merge_strategy = data['merge_strategy']

        # Find existing conflict
        conflict = ConflictResolution.objects.get(
            entity_type=entity_type,
            entity_id=entity_id,
            resolution='manual'
        )

        # Apply merge strategy
        if merge_strategy == 'server_wins':
            conflict.resolve_with_server_data()
        elif merge_strategy == 'local_wins':
            conflict.resolve_with_local_data()
        elif merge_strategy == 'intelligent_merge':
            merged_data = self._perform_intelligent_merge(
                conflict.local_data,
                conflict.server_data,
                data.get('conflict_fields', [])
            )
            conflict.resolve_with_merged_data(merged_data)
        elif merge_strategy == 'manual_merge':
            conflict.resolve_with_merged_data(data['resolved_data'])

        conflict.resolved_by = queue_item.created_by
        conflict.save()

        logger.info(f"Processed merge operation for {entity_type}:{entity_id} from queue")

    def _perform_intelligent_merge(self, local_data, server_data, conflict_fields):
        """Perform intelligent merge of conflicting data"""
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


class UploadQueueManager:
    """
    Manager for handling upload queue operations
    """

    def add_to_queue(self, operation_type: str, data: Dict, priority: str = 'normal',
                    entity_type: str = None, entity_id: str = None,
                    created_by=None) -> UploadQueue:
        """
        Add an operation to the upload queue

        Args:
            operation_type: Type of operation
            data: Data to be synced
            priority: Priority level
            entity_type: Type of entity being synced
            entity_id: ID of entity being synced
            created_by: User who created the operation
        """
        return UploadQueue.objects.create(
            operation_type=operation_type,
            data=data,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            created_by=created_by
        )

    def get_pending_operations(self, limit: int = 100) -> List[UploadQueue]:
        """
        Get pending operations ordered by priority and creation time
        """
        return UploadQueue.objects.filter(
            status='pending'
        ).order_by('priority', 'created_at')[:limit]

    def process_queue_batch(self, batch_size: int = 10):
        """
        Process a batch of queue operations
        """
        pending_items = self.get_pending_operations(batch_size)

        for item in pending_items:
            sync_service = InspectionSyncService()
            try:
                sync_service._process_upload_item(item)
            except Exception as e:
                logger.error(f"Failed to process queue item {item.id}: {e}")


class ConflictResolver:
    """
    Service for handling conflict resolution
    """

    def record_conflict(self, conflict_type: str, entity_type: str, entity_id: str,
                       local_data: Dict, server_data: Dict,
                       sync_operation: SyncOperation) -> ConflictResolution:
        """
        Record a conflict for later resolution
        """
        return ConflictResolution.objects.create(
            conflict_type=conflict_type,
            entity_type=entity_type,
            entity_id=entity_id,
            local_data=local_data,
            server_data=server_data,
            resolution='manual',  # Default to manual resolution
            sync_operation=sync_operation
        )

    def get_user_conflicts(self, user) -> List[ConflictResolution]:
        """
        Get unresolved conflicts for a user
        """
        return ConflictResolution.objects.filter(
            sync_operation__user=user,
            resolution='manual'
        ).order_by('resolved_at')

    def resolve_conflict(self, conflict_id: str, resolution: str,
                        resolved_data: Dict = None, notes: str = None,
                        resolved_by=None):
        """
        Manually resolve a conflict
        """
        conflict = ConflictResolution.objects.get(id=conflict_id)

        if resolution == 'server_wins':
            conflict.resolve_with_server_data(notes)
        elif resolution == 'local_wins':
            conflict.resolve_with_local_data(notes)
        elif resolution == 'merged' and resolved_data:
            conflict.resolve_with_merged_data(resolved_data, notes)

        conflict.resolved_by = resolved_by
        conflict.save()

        logger.info(f"Conflict {conflict_id} resolved by {resolved_by.username if resolved_by else 'system'}")
