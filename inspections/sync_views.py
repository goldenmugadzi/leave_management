"""
Sync API Views for Mobile App Integration
Implements endpoints for downloading inspection data
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import base64

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_download
def download_e1_defects(request):
    """
    GET /inspections/sync/defects/e1/
    
    Download E1 defect reports for specified inspections.
    
    Query Parameters:
    - inspection_ids: Comma-separated list of E117 inspection IDs (optional)
    - limit: Number of records per page (default: 50)
    """
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_download
def download_e6_certificates(request):
    """
    GET /inspections/sync/certificates/e6/
    
    Download E6 certificates for specified inspections.
    
    Query Parameters:
    - inspection_ids: Comma-separated list of E117 inspection IDs (optional)
    - limit: Number of records per page (default: 50)
    """
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

