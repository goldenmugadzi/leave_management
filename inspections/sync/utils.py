"""
Utility functions for inspection data synchronization
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import InspectionReport, ClientApplication, InspectionWorkflow


def calculate_data_hash(data: Dict[str, Any]) -> str:
    """
    Calculate a hash of the data for change detection

    Args:
        data: Dictionary of data to hash

    Returns:
        SHA256 hash of the data
    """
    # Create a normalized JSON string for consistent hashing
    normalized_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(normalized_data.encode()).hexdigest()


def detect_data_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect what fields have changed between two data versions

    Args:
        old_data: Original data
        new_data: Updated data

    Returns:
        Dictionary of changed fields with old and new values
    """
    changes = {}

    # Get all unique keys from both data sets
    all_keys = set(old_data.keys()) | set(new_data.keys())

    for key in all_keys:
        old_value = old_data.get(key)
        new_value = new_data.get(key)

        # Handle None vs empty string differences
        if old_value != new_value:
            if old_value is None and new_value == '':
                continue  # Consider empty string same as None
            if old_value == '' and new_value is None:
                continue  # Consider None same as empty string

            changes[key] = {
                'old': old_value,
                'new': new_value
            }

    return changes


def validate_inspection_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate inspection data for sync operations

    Args:
        data: Inspection data to validate

    Returns:
        List of validation error messages
    """
    errors = []

    # Required fields validation
    required_fields = [
        'service_no',
        'consumer_name',
        'inspection_date'
    ]

    for field in required_fields:
        if not data.get(field):
            errors.append(f"Field '{field}' is required")

    # Date validation
    inspection_date = data.get('inspection_date')
    if inspection_date:
        try:
            if isinstance(inspection_date, str):
                inspection_date = datetime.fromisoformat(inspection_date.replace('Z', '+00:00'))
            if inspection_date > timezone.now():
                errors.append("Inspection date cannot be in the future")
        except ValueError:
            errors.append("Invalid inspection date format")

    # Status validation
    status = data.get('status')
    if status and status not in ['pass', 'fail', 'pending']:
        errors.append("Invalid status value")

    # Safety checks validation (if status is pass/fail)
    if status in ['pass', 'fail']:
        safety_checks = [
            'all_equipment_bonded_earthed',
            'socket_outlets_earthed',
            'circuit_conductors_correct_size'
        ]

        for check in safety_checks:
            if check not in data:
                errors.append(f"Safety check '{check}' is required for status '{status}'")

    return errors


def merge_inspection_data(local_data: Dict[str, Any], server_data: Dict[str, Any],
                         merge_strategy: str = 'last_write_wins') -> Dict[str, Any]:
    """
    Merge local and server inspection data based on strategy

    Args:
        local_data: Local inspection data
        server_data: Server inspection data
        merge_strategy: Strategy for merging ('last_write_wins', 'server_wins', 'local_wins')

    Returns:
        Merged data dictionary
    """
    if merge_strategy == 'server_wins':
        return server_data.copy()

    if merge_strategy == 'local_wins':
        return local_data.copy()

    # Default: last_write_wins
    local_updated = local_data.get('updated_at')
    server_updated = server_data.get('updated_at')

    if local_updated and server_updated:
        if isinstance(local_updated, str):
            local_updated = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
        if isinstance(server_updated, str):
            server_updated = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))

        if local_updated > server_updated:
            return local_data.copy()
        else:
            return server_data.copy()

    # If no timestamps, prefer server data
    return server_data.copy()


def get_sync_status_summary(user) -> Dict[str, Any]:
    """
    Get a summary of sync status for a user

    Args:
        user: User to get sync status for

    Returns:
        Dictionary with sync status summary
    """
    from .models import SyncOperation, UploadQueue, ConflictResolution

    # Get recent sync operations
    recent_syncs = SyncOperation.objects.filter(
        user=user,
        started_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-started_at')[:5]

    # Get pending uploads
    pending_uploads = UploadQueue.objects.filter(
        created_by=user,
        status='pending'
    ).count()

    # Get unresolved conflicts
    unresolved_conflicts = ConflictResolution.objects.filter(
        sync_operation__user=user,
        resolution='manual'
    ).count()

    # Calculate success rate
    total_syncs = recent_syncs.count()
    successful_syncs = recent_syncs.filter(status='completed').count()
    success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0

    return {
        'recent_syncs_count': total_syncs,
        'successful_syncs_count': successful_syncs,
        'success_rate': round(success_rate, 2),
        'pending_uploads': pending_uploads,
        'unresolved_conflicts': unresolved_conflicts,
        'last_sync': recent_syncs.first().started_at if recent_syncs else None,
        'sync_health': 'good' if success_rate > 90 else 'warning' if success_rate > 70 else 'critical'
    }


def create_sync_metadata(operation_type: str, records_affected: int = 0,
                        additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create metadata for sync operations

    Args:
        operation_type: Type of sync operation
        records_affected: Number of records affected
        additional_data: Additional metadata

    Returns:
        Metadata dictionary
    """
    metadata = {
        'operation_type': operation_type,
        'records_affected': records_affected,
        'timestamp': timezone.now().isoformat(),
        'server_version': getattr(settings, 'SYNC_API_VERSION', '1.0'),
    }

    if additional_data:
        metadata.update(additional_data)

    return metadata


def is_sync_data_fresh(last_sync: datetime, max_age_hours: int = 24) -> bool:
    """
    Check if sync data is still fresh based on last sync time

    Args:
        last_sync: Last sync timestamp
        max_age_hours: Maximum age in hours for data to be considered fresh

    Returns:
        True if data is fresh, False otherwise
    """
    if not last_sync:
        return False

    max_age = timedelta(hours=max_age_hours)
    return timezone.now() - last_sync < max_age


def get_inspection_sync_priority(inspection_data: Dict[str, Any]) -> str:
    """
    Determine sync priority for inspection data

    Args:
        inspection_data: Inspection data dictionary

    Returns:
        Priority level ('low', 'normal', 'high', 'critical')
    """
    # Critical priority for urgent statuses
    if inspection_data.get('status') in ['fail', 'pending']:
        return 'high'

    # High priority for recently updated inspections
    updated_at = inspection_data.get('updated_at')
    if updated_at:
        try:
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            if timezone.now() - updated_at < timedelta(hours=1):
                return 'high'
        except ValueError:
            pass

    # Normal priority for regular updates
    return 'normal'


def sanitize_sync_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize data before sync operations

    Args:
        data: Raw data to sanitize

    Returns:
        Sanitized data dictionary
    """
    sanitized = {}

    for key, value in data.items():
        # Remove sensitive fields
        if key in ['password', 'token', 'secret']:
            continue

        # Convert datetime objects to ISO strings
        if isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        # Handle UUID fields
        elif hasattr(value, 'hex'):
            sanitized[key] = str(value)
        # Handle nested dictionaries
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sync_data(value)
        # Handle lists
        elif isinstance(value, list):
            sanitized[key] = [
                item.isoformat() if isinstance(item, datetime)
                else str(item) if hasattr(item, 'hex')
                else sanitize_sync_data(item) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def retry_with_exponential_backoff(func, max_attempts: int = 3, base_delay: float = 1.0,
                                  max_delay: float = 60.0):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    def wrapper(*args, **kwargs):
        import time
        import random

        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e

                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                time.sleep(delay)

        return None

    return wrapper
