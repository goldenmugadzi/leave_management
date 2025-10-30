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
    (inspections from applications assigned to the user)
    """
    assignments = ApplicationAssignment.objects.filter(assigned_to=user)
    application_ids = assignments.values_list('application_id', flat=True)
    
    # Get inspection reports for these applications
    inspection_ids = InspectionReport.objects.filter(
        client_application_id__in=application_ids
    ).values_list('id', flat=True)
    
    return list(inspection_ids)


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
        logger.info(f"[UPLOAD] POST /inspections/sync/mobile-sync-inspection/")
        logger.info(f"[UPLOAD] User: {request.user.username}")
        logger.info(f"[UPLOAD] Request data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}")
        
        data = request.data.copy()
        
        # Log received data (excluding large fields like signatures)
        log_data = {k: v if not isinstance(v, str) or len(v) < 100 else f"{len(v)} chars" for k, v in data.items()}
        logger.info(f"[UPLOAD] Request payload: {log_data}")
        
        # Extract id if present (mobile sends mobile_id or id)
        inspection_id = data.get('id') or data.get('mobile_id')
        
        # Check if inspection already exists by id (if it's a valid UUID)
        existing_inspection = None
        if inspection_id:
            try:
                # Try to parse as UUID and check if inspection exists
                try:
                    uuid_obj = uuid_lib.UUID(str(inspection_id))
                    existing_inspection = InspectionReport.objects.filter(id=uuid_obj).first()
                    if existing_inspection:
                        logger.info(f"[UPLOAD] Found existing inspection with id: {inspection_id}")
                except (ValueError, AttributeError):
                    # Not a valid UUID, will create new inspection
                    logger.info(f"[UPLOAD] Provided id '{inspection_id}' is not a UUID, will create new inspection")
                    pass
            except Exception as e:
                logger.warn(f"[UPLOAD] Error checking for existing inspection: {str(e)}")
                # Continue to create new inspection
                pass
        
        # Remove fields that aren't in the model
        # Note: Most fields are now in the model. Only remove fields that truly shouldn't be stored
        fields_to_remove = [
            'server_id', 'last_synced',  # Not model fields
        ]
        removed_fields = []
        for field in fields_to_remove:
            if field in data:
                data.pop(field)
                removed_fields.append(field)
        
        if removed_fields:
            logger.info(f"[UPLOAD] Removed mobile-only fields: {removed_fields}")
        
        # Create or update inspection
        if existing_inspection:
            # Update existing
            serializer = InspectionReportSyncSerializer(existing_inspection, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"[UPLOAD] Successfully updated inspection: {existing_inspection.id}")
                return Response({
                    'success': True,
                    'inspection_id': str(existing_inspection.id),
                    'message': 'Inspection updated successfully'
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"[UPLOAD] Validation errors: {serializer.errors}")
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
            
            # Create new
            serializer = InspectionReportSyncSerializer(data=data)
            if serializer.is_valid():
                inspection = serializer.save()
                logger.info(f"[UPLOAD] Successfully created inspection: {inspection.id}")
                return Response({
                    'success': True,
                    'inspection_id': str(inspection.id),
                    'message': 'Inspection created successfully'
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"[UPLOAD] Validation errors: {serializer.errors}")
                return Response({
                    'success': False,
                    'error': {
                        'message': 'Validation failed',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        logger.error(f"[UPLOAD] Exception: {str(e)}", exc_info=True)
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
        logger.info(f"[UPLOAD] POST /inspections/sync/defects/e1/")
        logger.info(f"[UPLOAD] User: {request.user.username}")
        logger.info(f"[UPLOAD] Request data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}")
        
        data = request.data.copy()
        
        # Extract inspection_report_id (server ID)
        inspection_id = data.get('inspection_report_id') or data.get('inspection_id')
        if not inspection_id:
            logger.error("[UPLOAD] Missing inspection_report_id")
            return Response({
                'success': False,
                'error': {
                    'message': 'Inspection must be synced first. Missing inspection_report_id',
                    'code': 'MISSING_INSPECTION_ID'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify inspection exists and user has access
        try:
            inspection = get_object_or_404(InspectionReport, id=inspection_id)
            user_inspection_ids = get_user_inspection_ids(request.user)
            if str(inspection.id) not in [str(i) for i in user_inspection_ids]:
                logger.error(f"[UPLOAD] User {request.user.username} does not have access to inspection {inspection_id}")
                return Response({
                    'success': False,
                    'error': {
                        'message': 'You do not have access to this inspection',
                        'code': 'FORBIDDEN'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"[UPLOAD] Inspection not found: {inspection_id} - {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': f'Inspection not found: {inspection_id}',
                    'code': 'INSPECTION_NOT_FOUND'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Set inspection_report_id
        data['inspection_report_id'] = inspection_id
        
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
                    if existing_report:
                        logger.info(f"[UPLOAD] Found existing E1 report with id: {report_id}")
                except (ValueError, AttributeError):
                    # Not a valid UUID, will create new report
                    pass
            except Exception as e:
                logger.warn(f"[UPLOAD] Error checking for existing E1 report: {str(e)}")
        
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
            report = serializer.save()
            logger.info(f"[UPLOAD] Successfully saved E1 report: {report.id}")
            return Response({
                'success': True,
                'report_id': str(report.id),
                'message': 'E1 defect report uploaded successfully'
            }, status=status.HTTP_201_CREATED if not existing_report else status.HTTP_200_OK)
        else:
            logger.error(f"[UPLOAD] Validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"[UPLOAD] Exception: {str(e)}", exc_info=True)
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
        logger.info(f"[UPLOAD] POST /inspections/sync/certificates/e6/")
        logger.info(f"[UPLOAD] User: {request.user.username}")
        logger.info(f"[UPLOAD] Request data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}")
        
        data = request.data.copy()
        
        # Extract inspection_report_id (server ID)
        inspection_id = data.get('inspection_report_id') or data.get('inspection_id')
        if not inspection_id:
            logger.error("[UPLOAD] Missing inspection_report_id")
            return Response({
                'success': False,
                'error': {
                    'message': 'Inspection must be synced first. Missing inspection_report_id',
                    'code': 'MISSING_INSPECTION_ID'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify inspection exists and user has access
        try:
            inspection = get_object_or_404(InspectionReport, id=inspection_id)
            user_inspection_ids = get_user_inspection_ids(request.user)
            if str(inspection.id) not in [str(i) for i in user_inspection_ids]:
                logger.error(f"[UPLOAD] User {request.user.username} does not have access to inspection {inspection_id}")
                return Response({
                    'success': False,
                    'error': {
                        'message': 'You do not have access to this inspection',
                        'code': 'FORBIDDEN'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"[UPLOAD] Inspection not found: {inspection_id} - {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': f'Inspection not found: {inspection_id}',
                    'code': 'INSPECTION_NOT_FOUND'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Set inspection_report_id
        data['inspection_report_id'] = inspection_id
        
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
                    if existing_cert:
                        logger.info(f"[UPLOAD] Found existing E6 certificate with id: {cert_id}")
                except (ValueError, AttributeError):
                    # Not a valid UUID, will create new certificate
                    pass
            except Exception as e:
                logger.warn(f"[UPLOAD] Error checking for existing E6 certificate: {str(e)}")
        
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
            cert = serializer.save()
            logger.info(f"[UPLOAD] Successfully saved E6 certificate: {cert.id}")
            return Response({
                'success': True,
                'certificate_id': str(cert.id),
                'message': 'E6 certificate uploaded successfully'
            }, status=status.HTTP_201_CREATED if not existing_cert else status.HTTP_200_OK)
        else:
            logger.error(f"[UPLOAD] Validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"[UPLOAD] Exception: {str(e)}", exc_info=True)
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

