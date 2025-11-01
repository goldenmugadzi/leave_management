"""
Sync API Views for Mobile App Integration
Implements endpoints for downloading and uploading inspection data
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from datetime import datetime
import base64
import logging
import uuid as uuid_lib

from .models import (
    InspectionReport, E1DefectReport, E6Certificate, 
    InspectionPhoto, ApplicationAssignment
)
from .sync_serializers import (
    InspectionReportSyncSerializer, E1DefectReportSyncSerializer,
    E6CertificateSyncSerializer, InspectionPhotoSerializer,
    DefectSerializer
)
from .decorators import rate_limit_download

logger = logging.getLogger(__name__)


def get_user_inspection_ids(user):
    """
    Get list of inspection IDs that the user has access to
    (inspections from applications assigned to the user OR inspections created by the user)
    """
    # Method 1: Get inspections from assigned applications
    assignments = ApplicationAssignment.objects.filter(assigned_to=user)
    application_ids = assignments.values_list('application_id', flat=True)
    
    assigned_inspection_ids = InspectionReport.objects.filter(
        client_application_id__in=application_ids
    ).values_list('id', flat=True)
    
    # Method 2: Get inspections created by the user (for mobile sync)
    # This handles inspections created via mobile sync that don't have client_application_id
    user_created_inspection_ids = InspectionReport.objects.filter(
        inspector=user
    ).values_list('id', flat=True)
    
    # Combine both sets of IDs
    all_inspection_ids = list(assigned_inspection_ids) + list(user_created_inspection_ids)
    
    # Remove duplicates while preserving order
    unique_inspection_ids = []
    seen = set()
    for inspection_id in all_inspection_ids:
        if inspection_id not in seen:
            unique_inspection_ids.append(inspection_id)
            seen.add(inspection_id)
    
    return unique_inspection_ids


def check_user_has_access_to_inspection(user, inspection_id):
    """
    Check if user has access to inspection.
    Returns (has_access, inspection_object) tuple.
    """
    try:
        inspection = InspectionReport.objects.get(id=inspection_id)
        
        # Check if user has access via get_user_inspection_ids
        user_inspection_ids = get_user_inspection_ids(user)
        if str(inspection.id) in [str(i) for i in user_inspection_ids]:
            return True, inspection
        
        # Fallback: If inspector field is not set but inspection exists,
        # allow access if user is authenticated (for backward compatibility)
        # This handles old inspections created before inspector field was set
        if not inspection.inspector:
            print(f"[PERMISSION] Inspection {inspection_id} has no inspector set, allowing access to authenticated user {user.username}")
            return True, inspection
        
        return False, inspection
    except InspectionReport.DoesNotExist:
        return False, None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_download
def download_inspection_batch(request):
    """
    GET /inspections/sync/download-inspection-batch/
    
    Download E117 inspection reports assigned to the authenticated user.
    Supports incremental sync with modified_after timestamp and cursor pagination.
    
    Query Parameters:
    - modified_after: ISO timestamp for incremental sync (optional)
    - cursor: Pagination cursor from previous response (optional)
    - limit: Number of records per page (default: 50)
    """
    try:
        user = request.user
        
        # Get inspections for user's assigned applications
        user_inspection_ids = get_user_inspection_ids(user)
        inspections = InspectionReport.objects.filter(id__in=user_inspection_ids)
        
        # Filter by modified_after for incremental sync
        modified_after = request.GET.get('modified_after')
        if modified_after:
            try:
                modified_date = datetime.fromisoformat(modified_after.replace('Z', '+00:00'))
                inspections = inspections.filter(updated_at__gte=modified_date)
            except (ValueError, AttributeError) as e:
                return Response(
                    {
                        'success': False,
                        'error': {
                            'message': f'Invalid modified_after format: {str(e)}',
                            'code': 'INVALID_PARAMETER'
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Pagination
        limit = int(request.GET.get('limit', 50))
        cursor = request.GET.get('cursor')
        
        # Simple cursor pagination based on ID
        if cursor:
            try:
                inspections = inspections.filter(id__gt=cursor)
            except Exception:
                pass
        
        inspections = inspections.order_by('id')[:limit + 1]
        inspections_list = list(inspections)
        
        # Check if there are more results
        has_more = len(inspections_list) > limit
        if has_more:
            inspections_list = inspections_list[:limit]
            next_cursor = str(inspections_list[-1].id)
        else:
            next_cursor = None
        
        # Serialize data
        serializer = InspectionReportSyncSerializer(
            inspections_list, 
            many=True,
            context={'request': request}
        )
        
        response_data = {
            'success': True,
            'inspections': serializer.data,
            'next_cursor': next_cursor,
            'server_time': timezone.now().isoformat(),
            'count': len(serializer.data)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'Internal server error',
                    'code': 'SERVER_ERROR',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_sync_inspection(request):
    """
    POST /inspections/sync/mobile-sync-inspection/
    
    Upload E117 inspection report from mobile app.
    
    Request Body: E117 inspection data in snake_case format
    """
    try:
        # Log raw request data received (sanitized for large fields)
        log_data = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in request.data.items()}
        print(f"[INSPECTION UPLOAD] Raw request data received - User: {request.user.username}, Keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}, Data: {log_data}")
        
        data = request.data.copy()
        
        # Extract id if present (mobile sends mobile_id or id)
        inspection_id = data.get('id') or data.get('mobile_id')
        
        # Check if inspection already exists by id (if it's a valid UUID)
        existing_inspection = None
        lookup_method = None
        if inspection_id:
            try:
                # Try to parse as UUID and check if inspection exists
                try:
                    uuid_obj = uuid_lib.UUID(str(inspection_id))
                    existing_inspection = InspectionReport.objects.filter(id=uuid_obj).first()
                    if existing_inspection:
                        lookup_method = 'uuid'
                except (ValueError, AttributeError):
                    # Not a valid UUID, will check by service_no or mobile_id below
                    pass
            except Exception as e:
                print(f"[INSPECTION UPLOAD] Error checking for existing inspection: {str(e)}")
        
        # Fallback: Check by service_no if UUID lookup failed
        if not existing_inspection and data.get('service_no'):
            existing_inspection = InspectionReport.objects.filter(
                service_no=data['service_no']
            ).first()
            if existing_inspection:
                lookup_method = 'service_no'
        
        # Fallback: Check by mobile_id if still not found
        if not existing_inspection and data.get('mobile_id'):
            existing_inspection = InspectionReport.objects.filter(
                mobile_id=data['mobile_id']
            ).first()
            if existing_inspection:
                lookup_method = 'mobile_id'
        
        # Log data after processing
        print(f"[INSPECTION UPLOAD] Data after processing - Inspection ID from request: {inspection_id}, Existing found: {existing_inspection is not None}, Lookup method: {lookup_method}, Existing ID: {str(existing_inspection.id) if existing_inspection else None}")
        
        # Remove fields that aren't in the model
        fields_to_remove = [
            'server_id', 'last_synced',  # Not model fields
        ]
        removed_fields = []
        for field in fields_to_remove:
            if field in data:
                data.pop(field)
                removed_fields.append(field)
        
        # Create or update inspection
        if existing_inspection:
            # Update existing - preserve client_application_id if not in payload
            if 'client_application_id' not in data or not data.get('client_application_id'):
                if hasattr(existing_inspection, 'client_application_id') and existing_inspection.client_application_id:
                    data['client_application_id'] = existing_inspection.client_application_id
                    print(f"[INSPECTION UPLOAD] Preserving existing client_application_id from database: {existing_inspection.client_application_id}")
            
            serializer_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in data.items()}
            print(f"[INSPECTION UPLOAD] Data sent to serializer (update) - Existing ID: {str(existing_inspection.id)}, Client App ID: {data.get('client_application_id')}, Data: {serializer_data_log}")
            
            serializer = InspectionReportSyncSerializer(existing_inspection, data=data, partial=True)
            if serializer.is_valid():
                # Log validated data from serializer
                validated_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in serializer.validated_data.items()}
                print(f"[INSPECTION UPLOAD] Validated data from serializer (update) - Data: {validated_data_log}")
                
                # Ensure inspector is set to current user (for permissions)
                inspection = serializer.save(inspector=request.user)
                
                # Log final saved object
                print(f"[INSPECTION UPLOAD] Final saved object (update) - ID: {str(inspection.id)}, Service No: {inspection.service_no if hasattr(inspection, 'service_no') else None}, Client App ID: {str(inspection.client_application_id) if hasattr(inspection, 'client_application_id') else None}, Inspector: {inspection.inspector.username if hasattr(inspection, 'inspector') and inspection.inspector else None}, Action: updated")
                
                return Response({
                    'success': True,
                    'inspection_id': str(inspection.id),
                    'message': 'Inspection updated successfully'
                }, status=status.HTTP_200_OK)
            else:
                print(f"[INSPECTION UPLOAD] Validation errors (update) - Errors: {serializer.errors}")
                return Response({
                    'success': False,
                    'error': {
                        'message': 'Validation failed',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Create new - remove id from data if it's not a valid UUID so Django generates a new one
            if 'id' in data:
                try:
                    uuid_lib.UUID(str(data['id']))
                    # Valid UUID, keep it
                except (ValueError, AttributeError):
                    # Not a valid UUID, remove it so Django generates a new one
                    data.pop('id')
            
            serializer_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in data.items()}
            print(f"[INSPECTION UPLOAD] Data sent to serializer (create) - Data: {serializer_data_log}")
            
            # Create new
            serializer = InspectionReportSyncSerializer(data=data)
            if serializer.is_valid():
                # Log validated data from serializer
                validated_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in serializer.validated_data.items()}
                print(f"[INSPECTION UPLOAD] Validated data from serializer (create) - Data: {validated_data_log}")
                
                # Set inspector to current user (for permissions)
                inspection = serializer.save(inspector=request.user)
                
                # Log final saved object
                print(f"[INSPECTION UPLOAD] Final saved object (create) - ID: {str(inspection.id)}, Service No: {inspection.service_no if hasattr(inspection, 'service_no') else None}, Client App ID: {str(inspection.client_application_id) if hasattr(inspection, 'client_application_id') else None}, Inspector: {inspection.inspector.username if hasattr(inspection, 'inspector') and inspection.inspector else None}, Action: created")
                
                return Response({
                    'success': True,
                    'inspection_id': str(inspection.id),
                    'message': 'Inspection created successfully'
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"[INSPECTION UPLOAD] Validation errors (create) - Errors: {serializer.errors}")
                return Response({
                    'success': False,
                    'error': {
                        'message': 'Validation failed',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        import traceback
        print(f"[INSPECTION UPLOAD] Exception - Error: {str(e)}, Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': {
                'message': 'Internal server error',
                'code': 'SERVER_ERROR',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def upload_e1_defect(request):
    """
    POST /inspections/sync/defects/e1/
    
    Upload E1 defect report from mobile app.
    """
    try:
        # Log raw request data received (sanitized for large fields)
        log_data = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in request.data.items()}
        print(f"[E1 DEFECT REPORT UPLOAD] Raw request data received - User: {request.user.username}, Keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}, Data: {log_data}")
        
        data = request.data.copy()
        
        # Extract inspection_report_id (server ID)
        inspection_id = data.get('inspection_report_id') or data.get('inspection_id')
        if not inspection_id:
            return Response({
                'success': False,
                'error': {
                    'message': 'Inspection must be synced first. Missing inspection_report_id',
                    'code': 'MISSING_INSPECTION_ID'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify inspection exists and user has access
        try:
            has_access, inspection = check_user_has_access_to_inspection(request.user, inspection_id)
            if not has_access:
                return Response({
                    'success': False,
                    'error': {
                        'message': 'You do not have access to this inspection',
                        'code': 'FORBIDDEN'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            print(f"[E1 DEFECT REPORT UPLOAD] Inspection not found: {inspection_id} - {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': f'Inspection not found: {inspection_id}',
                    'code': 'INSPECTION_NOT_FOUND'
                }
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Set inspection_report_id
        data['inspection_report_id'] = inspection_id
        
        # Set client_application_id - REQUIRED for E1/E6 models
        # Priority: 1) From payload, 2) From inspection.client_application, 3) Error if missing
        original_client_app_id = data.get('client_application_id')
        if 'client_application_id' not in data or not data.get('client_application_id'):
            if hasattr(inspection, 'client_application') and inspection.client_application:
                data['client_application_id'] = inspection.client_application.id
            elif hasattr(inspection, 'client_application_id') and inspection.client_application_id:
                data['client_application_id'] = inspection.client_application_id
        
        # Log data after processing
        client_app_source = 'payload' if original_client_app_id else ('inspection.client_application' if hasattr(inspection, 'client_application') and inspection.client_application else ('inspection.client_application_id' if hasattr(inspection, 'client_application_id') else 'none'))
        print(f"[E1 DEFECT REPORT UPLOAD] Data after processing - Inspection ID: {inspection_id}, Inspection Report ID: {data.get('inspection_report_id')}, Client App ID Source: {client_app_source}, Client App ID: {data.get('client_application_id')}")
        
        # Verify client_application_id is set - REQUIRED for E1/E6
        if not data.get('client_application_id'):
            print(f"[E1 DEFECT REPORT UPLOAD] Inspection {inspection_id} does not have client_application_id - cannot create E1/E6 without it")
            return Response({
                'success': False,
                'error': {
                    'message': 'Inspection must have a client application before creating defect report/certificate',
                    'code': 'MISSING_CLIENT_APPLICATION'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove mobile_id from data if present (not a model field)
        if 'mobile_id' in data:
            data.pop('mobile_id')
        
        # Check if report already exists by id (if it's a valid UUID)
        existing_report = None
        report_id = data.get('id')
        if report_id:
            try:
                try:
                    uuid_obj = uuid_lib.UUID(str(report_id))
                    existing_report = E1DefectReport.objects.filter(id=uuid_obj).first()
                except (ValueError, AttributeError):
                    # Not a valid UUID, will create new report
                    pass
            except Exception as e:
                print(f"[E1 DEFECT REPORT UPLOAD] Error checking for existing E1 report: {str(e)}")
        
        # Log data sent to serializer
        serializer_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in data.items()}
        print(f"[E1 DEFECT REPORT UPLOAD] Data sent to serializer - Is Update: {existing_report is not None}, Existing Report ID: {str(existing_report.id) if existing_report else None}, Data: {serializer_data_log}")
        
        # Create or update
        if existing_report:
            serializer = E1DefectReportSyncSerializer(existing_report, data=data, partial=True)
        else:
            # Remove id if not a valid UUID so Django generates a new one
            if 'id' in data:
                try:
                    uuid_lib.UUID(str(data['id']))
                    # Valid UUID, keep it
                except (ValueError, AttributeError):
                    data.pop('id')
            serializer = E1DefectReportSyncSerializer(data=data)
        
        if serializer.is_valid():
            # Log validated data from serializer
            validated_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in serializer.validated_data.items()}
            print(f"[E1 DEFECT REPORT UPLOAD] Validated data from serializer - Data: {validated_data_log}")
            
            report = serializer.save()
            
            # Log final saved object
            print(f"[E1 DEFECT REPORT UPLOAD] Final saved object - Report ID: {str(report.id)}, Report Number: {report.report_number if hasattr(report, 'report_number') else None}, Inspection Report ID: {str(report.inspection_report_id) if hasattr(report, 'inspection_report_id') else None}, Client App ID: {str(report.client_application_id) if hasattr(report, 'client_application_id') else None}, Action: {'updated' if existing_report else 'created'}")
            
            return Response({
                'success': True,
                'report_id': str(report.id),
                'message': 'E1 defect report uploaded successfully'
            }, status=status.HTTP_201_CREATED if not existing_report else status.HTTP_200_OK)
        else:
            print(f"[E1 DEFECT REPORT UPLOAD] Validation errors - Errors: {serializer.errors}, Input Data Keys: {list(data.keys())}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        import traceback
        print(f"[E1 DEFECT REPORT UPLOAD] Exception - Error: {str(e)}, Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': {
                'message': 'Internal server error',
                'code': 'SERVER_ERROR',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def download_e1_defects(request):
    """
    GET /inspections/sync/defects/e1/
    
    Download E1 defect reports for specified inspections.
    
    Query Parameters:
    - inspection_ids: Comma-separated list of E117 inspection IDs (optional)
    - limit: Number of records per page (default: 50)
    """
    if request.method == 'POST':
        return upload_e1_defect(request)
    
    try:
        user = request.user
        user_inspection_ids = get_user_inspection_ids(user)
        
        # Start with E1 reports for user's inspections
        reports = E1DefectReport.objects.filter(
            inspection_report_id__in=user_inspection_ids
        )
        
        # Filter by specific inspection IDs if provided
        inspection_ids_param = request.GET.get('inspection_ids')
        if inspection_ids_param:
            requested_ids = [id.strip() for id in inspection_ids_param.split(',') if id.strip()]
            # Only allow user to access their own inspections
            allowed_ids = [id for id in requested_ids if id in [str(i) for i in user_inspection_ids]]
            reports = reports.filter(inspection_report_id__in=allowed_ids)
        
        # Pagination
        limit = int(request.GET.get('limit', 50))
        reports = reports.order_by('-created_at')[:limit]
        
        # Serialize data
        serializer = E1DefectReportSyncSerializer(
            reports,
            many=True,
            context={'request': request}
        )
        
        response_data = {
            'success': True,
            'defect_reports': serializer.data,
            'count': len(serializer.data)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'Internal server error',
                    'code': 'SERVER_ERROR',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def upload_e6_certificate(request):
    """
    POST /inspections/sync/certificates/e6/
    
    Upload E6 certificate from mobile app.
    """
    try:
        # Log raw request data received (sanitized for large fields)
        log_data = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in request.data.items()}
        print(f"[E6 CERTIFICATE UPLOAD] Raw request data received - User: {request.user.username}, Keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}, Data: {log_data}")
        
        data = request.data.copy()
        
        # Extract inspection_report_id (server ID)
        inspection_id = data.get('inspection_report_id') or data.get('inspection_id')
        if not inspection_id:
            return Response({
                'success': False,
                'error': {
                    'message': 'Inspection must be synced first. Missing inspection_report_id',
                    'code': 'MISSING_INSPECTION_ID'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify inspection exists and user has access
        try:
            has_access, inspection = check_user_has_access_to_inspection(request.user, inspection_id)
            if not has_access:
                return Response({
                    'success': False,
                    'error': {
                        'message': 'You do not have access to this inspection',
                        'code': 'FORBIDDEN'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            print(f"[E6 CERTIFICATE UPLOAD] Inspection not found: {inspection_id} - {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': f'Inspection not found: {inspection_id}',
                    'code': 'INSPECTION_NOT_FOUND'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Set inspection_report_id
        data['inspection_report_id'] = inspection_id
        
        # Set client_application_id - REQUIRED for E1/E6 models
        # Priority: 1) From payload, 2) From inspection.client_application, 3) Error if missing
        original_client_app_id = data.get('client_application_id')
        if 'client_application_id' not in data or not data.get('client_application_id'):
            if hasattr(inspection, 'client_application') and inspection.client_application:
                data['client_application_id'] = inspection.client_application.id
            elif hasattr(inspection, 'client_application_id') and inspection.client_application_id:
                data['client_application_id'] = inspection.client_application_id
        
        # Log data after processing
        client_app_source = 'payload' if original_client_app_id else ('inspection.client_application' if hasattr(inspection, 'client_application') and inspection.client_application else ('inspection.client_application_id' if hasattr(inspection, 'client_application_id') else 'none'))
        print(f"[E6 CERTIFICATE UPLOAD] Data after processing - Inspection ID: {inspection_id}, Inspection Report ID: {data.get('inspection_report_id')}, Client App ID Source: {client_app_source}, Client App ID: {data.get('client_application_id')}")
        
        # Verify client_application_id is set - REQUIRED for E1/E6
        if not data.get('client_application_id'):
            print(f"[E6 CERTIFICATE UPLOAD] Inspection {inspection_id} does not have client_application_id - cannot create E1/E6 without it")
            return Response({
                'success': False,
                'error': {
                    'message': 'Inspection must have a client application before creating defect report/certificate',
                    'code': 'MISSING_CLIENT_APPLICATION'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove mobile_id from data if present (not a model field)
        if 'mobile_id' in data:
            data.pop('mobile_id')
        
        # Check if certificate already exists by id (if it's a valid UUID)
        existing_cert = None
        cert_id = data.get('id')
        if cert_id:
            try:
                try:
                    uuid_obj = uuid_lib.UUID(str(cert_id))
                    existing_cert = E6Certificate.objects.filter(id=uuid_obj).first()
                except (ValueError, AttributeError):
                    # Not a valid UUID, will create new certificate
                    pass
            except Exception as e:
                print(f"[E6 CERTIFICATE UPLOAD] Error checking for existing E6 certificate: {str(e)}")
        
        # Log data sent to serializer
        serializer_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in data.items()}
        print(f"[E6 CERTIFICATE UPLOAD] Data sent to serializer - Is Update: {existing_cert is not None}, Existing Cert ID: {str(existing_cert.id) if existing_cert else None}, Data: {serializer_data_log}")
        
        # Create or update
        if existing_cert:
            serializer = E6CertificateSyncSerializer(existing_cert, data=data, partial=True)
        else:
            # Remove id if not a valid UUID so Django generates a new one
            if 'id' in data:
                try:
                    uuid_lib.UUID(str(data['id']))
                    # Valid UUID, keep it
                except (ValueError, AttributeError):
                    data.pop('id')
            serializer = E6CertificateSyncSerializer(data=data)
        
        if serializer.is_valid():
            # Log validated data from serializer
            validated_data_log = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in serializer.validated_data.items()}
            print(f"[E6 CERTIFICATE UPLOAD] Validated data from serializer - Data: {validated_data_log}")
            
            cert = serializer.save()
            
            # Log final saved object
            print(f"[E6 CERTIFICATE UPLOAD] Final saved object - Certificate ID: {str(cert.id)}, Certificate Number: {cert.certificate_number if hasattr(cert, 'certificate_number') else None}, Inspection Report ID: {str(cert.inspection_report_id) if hasattr(cert, 'inspection_report_id') else None}, Client App ID: {str(cert.client_application_id) if hasattr(cert, 'client_application_id') else None}, Action: {'updated' if existing_cert else 'created'}")
            
            return Response({
                'success': True,
                'certificate_id': str(cert.id),
                'message': 'E6 certificate uploaded successfully'
            }, status=status.HTTP_201_CREATED if not existing_cert else status.HTTP_200_OK)
        else:
            print(f"[E6 CERTIFICATE UPLOAD] Validation errors - Errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        import traceback
        print(f"[E6 CERTIFICATE UPLOAD] Exception - Error: {str(e)}, Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': {
                'message': 'Internal server error',
                'code': 'SERVER_ERROR',
                'details': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def download_e6_certificates(request):
    """
    GET /inspections/sync/certificates/e6/
    
    Download E6 certificates for specified inspections.
    
    Query Parameters:
    - inspection_ids: Comma-separated list of E117 inspection IDs (optional)
    - limit: Number of records per page (default: 50)
    """
    if request.method == 'POST':
        return upload_e6_certificate(request)
    
    try:
        user = request.user
        user_inspection_ids = get_user_inspection_ids(user)
        
        # Start with E6 certificates for user's inspections
        certificates = E6Certificate.objects.filter(
            inspection_report_id__in=user_inspection_ids
        )
        
        # Filter by specific inspection IDs if provided
        inspection_ids_param = request.GET.get('inspection_ids')
        if inspection_ids_param:
            requested_ids = [id.strip() for id in inspection_ids_param.split(',') if id.strip()]
            # Only allow user to access their own inspections
            allowed_ids = [id for id in requested_ids if id in [str(i) for i in user_inspection_ids]]
            certificates = certificates.filter(inspection_report_id__in=allowed_ids)
        
        # Pagination
        limit = int(request.GET.get('limit', 50))
        certificates = certificates.order_by('-created_at')[:limit]
        
        # Serialize data
        serializer = E6CertificateSyncSerializer(
            certificates,
            many=True,
            context={'request': request}
        )
        
        response_data = {
            'success': True,
            'certificates': serializer.data,
            'count': len(serializer.data)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'Internal server error',
                    'code': 'SERVER_ERROR',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_download
def download_inspection_photos(request, id):
    """
    GET /inspections/sync/inspections/<id>/photos/
    
    Download photos for a specific inspection.
    
    URL Parameters:
    - id: E117 inspection UUID
    """
    try:
        user = request.user
        user_inspection_ids = get_user_inspection_ids(user)
        
        # Verify user has access to this inspection
        if str(id) not in [str(i) for i in user_inspection_ids]:
            return Response(
                {
                    'success': False,
                    'error': {
                        'message': 'You do not have access to this inspection',
                        'code': 'FORBIDDEN'
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get inspection
        inspection = get_object_or_404(InspectionReport, id=id)
        
        # Get photos
        photos = InspectionPhoto.objects.filter(inspection_report=inspection)
        
        # Serialize data
        serializer = InspectionPhotoSerializer(
            photos,
            many=True,
            context={'request': request}
        )
        
        response_data = {
            'success': True,
            'photos': serializer.data,
            'count': len(serializer.data)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except InspectionReport.DoesNotExist:
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'Inspection not found',
                    'code': 'NOT_FOUND'
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'Internal server error',
                    'code': 'SERVER_ERROR',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_download
def download_general_defects(request):
    """
    GET /inspections/sync/defects/
    
    Download general defects extracted from E1 reports.
    
    Query Parameters:
    - inspection_ids: Comma-separated list of inspection IDs (optional)
    - limit: Number of records per page (default: 100)
    """
    try:
        user = request.user
        user_inspection_ids = get_user_inspection_ids(user)
        
        # Get E1 reports for user's inspections
        reports = E1DefectReport.objects.filter(
            inspection_report_id__in=user_inspection_ids
        )
        
        # Filter by specific inspection IDs if provided
        inspection_ids_param = request.GET.get('inspection_ids')
        if inspection_ids_param:
            requested_ids = [id.strip() for id in inspection_ids_param.split(',') if id.strip()]
            allowed_ids = [id for id in requested_ids if id in [str(i) for i in user_inspection_ids]]
            reports = reports.filter(inspection_report_id__in=allowed_ids)
        
        # Pagination
        limit = int(request.GET.get('limit', 100))
        reports = reports.order_by('-created_at')[:limit]
        
        # Extract defects from E1 reports
        defects = []
        for report in reports:
            if report.defects_requiring_attention:
                # Parse defects - assuming newline separated
                defect_lines = report.defects_requiring_attention.split('\n')
                for idx, line in enumerate(defect_lines):
                    if line.strip():
                        defects.append({
                            'id': f"{report.id}-{idx}",
                            'inspection_id': str(report.inspection_report_id),
                            'inspection_type': 'e117',
                            'defect_description': line.strip(),
                            'defect_category': 'safety',
                            'severity': 'critical',
                            'rectification_required': 'Immediate',
                            'compliance_standard': 'ZESA Standard 001',
                            'status': 'identified',
                            'rectification_date': None,
                            'verification_date': None,
                            'photos': [],
                            'notes': f"From E1 Report: {report.report_number}",
                            'created_at': report.created_at,
                            'updated_at': report.updated_at
                        })
        
        # Serialize data
        serializer = DefectSerializer(defects, many=True)
        
        response_data = {
            'success': True,
            'defects': serializer.data,
            'count': len(serializer.data)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': {
                    'message': 'Internal server error',
                    'code': 'SERVER_ERROR',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

