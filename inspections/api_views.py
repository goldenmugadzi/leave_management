"""
API Views for Inspections App - Mobile App Integration
Provides REST API endpoints for the mobile application
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import ClientApplication, ApplicationAssignment, Customer, Contractor, ApplicationAttachment


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assigned_applications(request):
    """
    GET /inspections/api/v1/applications/assigned/
    
    Get applications assigned to the authenticated field officer.
    Returns applications with full customer and contractor details.
    
    Query Parameters:
    - since: ISO timestamp for incremental sync (optional)
    - status: Filter by assignment status (optional)
    """
    try:
        user = request.user
        
        # Get all assignments for the current user
        assignments = ApplicationAssignment.objects.filter(
            assigned_to=user
        ).select_related('application', 'application__customer', 'application__contractor')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            assignments = assignments.filter(status=status_filter)
        else:
            # Default: only show active assignments
            assignments = assignments.filter(status__in=['assigned', 'accepted', 'in_progress'])
        
        # Filter by since timestamp for incremental sync
        since = request.GET.get('since')
        if since:
            try:
                since_date = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
                assignments = assignments.filter(updated_at__gte=since_date)
            except (ValueError, AttributeError):
                pass
        
        # Prepare response data
        applications_data = []
        for assignment in assignments:
            app = assignment.application
            
            # Get attachments
            attachments = ApplicationAttachment.objects.filter(application=app)
            attachments_data = [
                {
                    'id': str(att.id),
                    'file_url': request.build_absolute_uri(att.file.url) if att.file else None,
                    'file_type': att.file_type,
                    'description': att.description or '',
                    'file_size': att.file.size if att.file else 0,
                    'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None,
                }
                for att in attachments
            ]
            
            # Build application data
            app_data = {
                'id': str(app.id),
                'application_number': app.application_number,
                'application_type': app.application_type,
                'priority': app.priority,
                'status': app.status,
                'submission_date': app.submission_date.isoformat() if app.submission_date else None,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                
                # Assignment info
                'assignment_status': assignment.status,
                'assignment_date': assignment.assignment_date.isoformat() if assignment.assignment_date else None,
                'assigned_by': str(assignment.assigned_by.id) if assignment.assigned_by else None,
                'accepted_at': assignment.accepted_at.isoformat() if assignment.accepted_at else None,
                
                # Customer information
                'customer': {
                    'id': str(app.customer.id),
                    'customer_id': app.customer.customer_id,
                    'full_name': app.customer.full_name,
                    'phone': app.customer.phone or '',
                    'email': app.customer.email or '',
                    'stand_plot_number': app.customer.stand_plot_number or '',
                    'farm_street_name': app.customer.farm_street_name or '',
                    'suburb_township': app.customer.suburb_township or '',
                    'city': app.customer.city or '',
                } if app.customer else None,
                
                # Contractor information
                'contractor': {
                    'id': str(app.contractor.id),
                    'contractor_id': app.contractor.contractor_id,
                    'business_name': app.contractor.business_name,
                    'contact_person': app.contractor.contact_person or '',
                    'phone': app.contractor.phone or '',
                    'email': app.contractor.email or '',
                    'address': app.contractor.address or '',
                } if app.contractor else None,
                
                # Application details
                'supply_type': app.supply_type,
                'purpose': app.purpose,
                'application_details': app.application_details or {},
                
                # Attachments
                'attachments': attachments_data,
                
                # Audit fields
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'updated_at': app.updated_at.isoformat() if app.updated_at else None,
            }
            
            applications_data.append(app_data)
        
        # Calculate counts
        now = timezone.now()
        all_assignments = ApplicationAssignment.objects.filter(assigned_to=user)
        total_count = all_assignments.count()
        pending_count = all_assignments.filter(status='assigned').count()
        accepted_count = all_assignments.filter(status='accepted').count()
        overdue_count = all_assignments.filter(
            due_date__lt=now,
            status__in=['assigned', 'accepted', 'in_progress']
        ).count()
        
        response_data = {
            'applications': applications_data,
            'total_count': total_count,
            'pending_count': pending_count,
            'accepted_count': accepted_count,
            'overdue_count': overdue_count,
            'sync_timestamp': timezone.now().isoformat(),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': str(e),
                'message': 'Failed to fetch assigned applications'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_detail(request, pk):
    """
    GET /inspections/api/v1/applications/<id>/
    
    Get detailed information about a specific application
    """
    try:
        app = get_object_or_404(ClientApplication, pk=pk)
        
        # Check if user has access to this application
        assignment = ApplicationAssignment.objects.filter(
            application=app,
            assigned_to=request.user
        ).first()
        
        if not assignment:
            return Response(
                {'error': 'You do not have access to this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get attachments
        attachments = ApplicationAttachment.objects.filter(application=app)
        attachments_data = [
            {
                'id': str(att.id),
                'file_url': request.build_absolute_uri(att.file.url) if att.file else None,
                'file_type': att.file_type,
                'description': att.description or '',
                'file_size': att.file.size if att.file else 0,
                'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None,
            }
            for att in attachments
        ]
        
        app_data = {
            'id': str(app.id),
            'application_number': app.application_number,
            'application_type': app.application_type,
            'priority': app.priority,
            'status': app.status,
            'submission_date': app.submission_date.isoformat() if app.submission_date else None,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            
            # Assignment info
            'assignment_status': assignment.status,
            'assignment_date': assignment.assignment_date.isoformat() if assignment.assignment_date else None,
            'assigned_by': str(assignment.assigned_by.id) if assignment.assigned_by else None,
            'accepted_at': assignment.accepted_at.isoformat() if assignment.accepted_at else None,
            
            # Customer information
            'customer': {
                'id': str(app.customer.id),
                'customer_id': app.customer.customer_id,
                'full_name': app.customer.full_name,
                'phone': app.customer.phone or '',
                'email': app.customer.email or '',
                'stand_plot_number': app.customer.stand_plot_number or '',
                'farm_street_name': app.customer.farm_street_name or '',
                'suburb_township': app.customer.suburb_township or '',
                'city': app.customer.city or '',
            } if app.customer else None,
            
            # Contractor information
            'contractor': {
                'id': str(app.contractor.id),
                'contractor_id': app.contractor.contractor_id,
                'business_name': app.contractor.business_name,
                'contact_person': app.contractor.contact_person or '',
                'phone': app.contractor.phone or '',
                'email': app.contractor.email or '',
                'address': app.contractor.address or '',
            } if app.contractor else None,
            
            # Application details
            'supply_type': app.supply_type,
            'purpose': app.purpose,
            'application_details': app.application_details or {},
            
            # Attachments
            'attachments': attachments_data,
            
            # Audit fields
            'created_at': app.created_at.isoformat() if app.created_at else None,
            'updated_at': app.updated_at.isoformat() if app.updated_at else None,
        }
        
        return Response(app_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': str(e),
                'message': 'Failed to fetch application details'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_assignment(request, pk):
    """
    POST /inspections/api/v1/applications/<id>/accept/
    
    Accept an assigned application
    """
    try:
        app = get_object_or_404(ClientApplication, pk=pk)
        assignment = get_object_or_404(
            ApplicationAssignment,
            application=app,
            assigned_to=request.user
        )
        
        if assignment.status == 'assigned':
            assignment.accept_assignment()
            return Response(
                {
                    'success': True,
                    'message': 'Assignment accepted successfully',
                    'assignment_status': assignment.status,
                    'accepted_at': assignment.accepted_at.isoformat() if assignment.accepted_at else None,
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'error': f'Assignment is already {assignment.status}',
                    'assignment_status': assignment.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except ApplicationAssignment.DoesNotExist:
        return Response(
            {'error': 'Assignment not found or you do not have access'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {
                'error': str(e),
                'message': 'Failed to accept assignment'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

