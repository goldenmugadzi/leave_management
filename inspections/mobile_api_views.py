from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
import logging

from .models import ClientApplication, ApplicationAssignment
from .serializers import (
    AssignmentResponseSerializer, ServerApplicationResponseSerializer,
    ApplicationDetailSerializer, AcceptAssignmentSerializer,
    UpdateStatusSerializer, CompleteAssignmentSerializer,
    ApplicationAttachmentCacheSerializer
)

logger = logging.getLogger(__name__)


def create_error_response(message, status_code, error_code=None, details=None):
    """Create standardized error response"""
    error_data = {
        "success": False,
        "error": {
            "message": message,
            "status": status_code,
            "code": error_code or "ERROR"
        }
    }
    if details:
        error_data["error"]["details"] = details
    return Response(error_data, status=status_code)


def create_success_response(data, message=None, meta=None):
    """Create standardized success response"""
    response_data = {
        "success": True,
        "data": data
    }
    if message:
        response_data["message"] = message
    if meta:
        response_data["meta"] = meta
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assigned_applications(request):
    """
    GET /applications/assigned
    Retrieves all applications assigned to the authenticated field officer.
    """
    try:
        # Get query parameters
        officer_id = request.GET.get('officer_id')
        include_details = request.GET.get('include_details', 'true').lower() == 'true'
        status_filter = request.GET.get('status')
        priority_filter = request.GET.get('priority')
        due_date_from = request.GET.get('due_date_from')
        due_date_to = request.GET.get('due_date_to')
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 per page

        # Validate officer_id matches authenticated user
        if officer_id and str(request.user.id) != officer_id:
            return create_error_response(
                "Officer ID does not match authenticated user",
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN"
            )

        # Get assignments for the authenticated user
        assignments_query = ApplicationAssignment.objects.filter(
            assigned_to=request.user
        ).select_related('application', 'application__customer', 'application__contractor')

        # Apply filters
        if status_filter:
            assignments_query = assignments_query.filter(status=status_filter)
        
        if priority_filter:
            assignments_query = assignments_query.filter(application__priority=priority_filter)
        
        if due_date_from:
            assignments_query = assignments_query.filter(due_date__gte=due_date_from)
        
        if due_date_to:
            assignments_query = assignments_query.filter(due_date__lte=due_date_to)

        # Order by assignment date (most recent first)
        assignments_query = assignments_query.order_by('-assignment_date')

        # Get applications from assignments
        applications = [assignment.application for assignment in assignments_query]

        # Calculate counts
        total_count = len(applications)
        pending_count = len([app for app in applications if app.status == 'submitted'])
        overdue_count = len([
            app for app in applications 
            if app.assignments.filter(assigned_to=request.user, due_date__lt=timezone.now()).exists()
        ])
        accepted_count = len([
            app for app in applications 
            if app.assignments.filter(assigned_to=request.user, status='accepted').exists()
        ])

        # Pagination
        paginator = Paginator(applications, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize applications
        context = {'request': request, 'user': request.user}
        applications_data = ServerApplicationResponseSerializer(
            page_obj.object_list, many=True, context=context
        ).data

        # Prepare response data
        response_data = {
            "applications": applications_data,
            "total_count": total_count,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
            "accepted_count": accepted_count
        }

        # Add pagination metadata
        meta = {
            "page": page,
            "limit": limit,
            "total": paginator.count,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous()
        }

        return create_success_response(response_data, meta=meta)

    except Exception as e:
        logger.error(f"Error in get_assigned_applications: {str(e)}")
        return create_error_response(
            "Internal server error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_application_details(request, application_id):
    """
    GET /applications/{id}
    Retrieves detailed information for a specific application.
    """
    try:
        # Get the application
        application = get_object_or_404(ClientApplication, id=application_id)
        
        # Check if user has access to this application
        assignment = application.assignments.filter(assigned_to=request.user).first()
        if not assignment:
            return create_error_response(
                "Application not found or access denied",
                status.HTTP_404_NOT_FOUND,
                "NOT_FOUND"
            )

        # Serialize application details
        context = {'request': request, 'user': request.user}
        application_data = ApplicationDetailSerializer(application, context=context).data

        return create_success_response(application_data)

    except ClientApplication.DoesNotExist:
        return create_error_response(
            "Application not found",
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND"
        )
    except Exception as e:
        logger.error(f"Error in get_application_details: {str(e)}")
        return create_error_response(
            "Internal server error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_assignment(request, application_id):
    """
    POST /applications/{id}/accept
    Allows a field officer to accept an assigned application.
    """
    try:
        # Get the application
        application = get_object_or_404(ClientApplication, id=application_id)
        
        # Get the assignment
        assignment = application.assignments.filter(assigned_to=request.user).first()
        if not assignment:
            return create_error_response(
                "Assignment not found or access denied",
                status.HTTP_404_NOT_FOUND,
                "NOT_FOUND"
            )

        # Check if already accepted
        if assignment.status == 'accepted':
            return create_error_response(
                "Assignment already accepted",
                status.HTTP_409_CONFLICT,
                "ASSIGNMENT_CONFLICT"
            )

        # Prepare request data with officer_id from authenticated user
        request_data = request.data.copy() if request.data else {}
        request_data['officer_id'] = str(request.user.id)
        
        # Validate request data
        serializer = AcceptAssignmentSerializer(data=request_data)
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                serializer.errors
            )

        # Accept the assignment
        assignment.accept_assignment()
        
        # Update application status if needed
        if application.status == 'assigned':
            application.status = 'in_progress'
            application.save()

        # Prepare response data
        response_data = {
            "id": str(application.id),
            "assignment_status": assignment.status,
            "accepted_at": assignment.accepted_date.isoformat(),
            "updated_at": assignment.updated_at.isoformat()
        }

        return create_success_response(
            response_data, 
            "Assignment accepted successfully"
        )

    except ClientApplication.DoesNotExist:
        return create_error_response(
            "Application not found",
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND"
        )
    except Exception as e:
        logger.error(f"Error in accept_assignment: {str(e)}")
        return create_error_response(
            "Internal server error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR"
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_assignment_status(request, application_id):
    """
    PATCH /applications/{id}/status
    Updates the status of an application assignment.
    """
    try:
        # Get the application
        application = get_object_or_404(ClientApplication, id=application_id)
        
        # Get the assignment
        assignment = application.assignments.filter(assigned_to=request.user).first()
        if not assignment:
            return create_error_response(
                "Assignment not found or access denied",
                status.HTTP_404_NOT_FOUND,
                "NOT_FOUND"
            )

        # Prepare request data with officer_id from authenticated user
        request_data = request.data.copy() if request.data else {}
        request_data['officer_id'] = str(request.user.id)
        
        # Validate request data
        serializer = UpdateStatusSerializer(data=request_data)
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                serializer.errors
            )

        # Update assignment status
        assignment.status = serializer.validated_data['assignment_status']
        assignment.save()

        # Update application status
        application.status = serializer.validated_data['status']
        application.save()

        # Prepare response data
        response_data = {
            "id": str(application.id),
            "assignment_status": assignment.status,
            "status": application.status,
            "updated_at": assignment.updated_at.isoformat()
        }

        return create_success_response(
            response_data, 
            "Status updated successfully"
        )

    except ClientApplication.DoesNotExist:
        return create_error_response(
            "Application not found",
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND"
        )
    except Exception as e:
        logger.error(f"Error in update_assignment_status: {str(e)}")
        return create_error_response(
            "Internal server error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_assignment(request, application_id):
    """
    POST /applications/{id}/complete
    Marks an application assignment as completed.
    """
    try:
        # Get the application
        application = get_object_or_404(ClientApplication, id=application_id)
        
        # Get the assignment
        assignment = application.assignments.filter(assigned_to=request.user).first()
        if not assignment:
            return create_error_response(
                "Assignment not found or access denied",
                status.HTTP_404_NOT_FOUND,
                "NOT_FOUND"
            )

        # Prepare request data with officer_id from authenticated user
        request_data = request.data.copy() if request.data else {}
        request_data['officer_id'] = str(request.user.id)
        
        # Validate request data
        serializer = CompleteAssignmentSerializer(data=request_data)
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                serializer.errors
            )

        # Complete the assignment
        completion_notes = serializer.validated_data.get('completion_notes', '')
        assignment.complete_assignment(completion_notes)

        # Update application status
        application.status = 'completed'
        application.save()

        # Prepare response data
        response_data = {
            "id": str(application.id),
            "assignment_status": assignment.status,
            "status": application.status,
            "completed_at": assignment.completed_date.isoformat(),
            "inspection_id": serializer.validated_data.get('inspection_id'),
            "updated_at": assignment.updated_at.isoformat()
        }

        return create_success_response(
            response_data, 
            "Assignment completed successfully"
        )

    except ClientApplication.DoesNotExist:
        return create_error_response(
            "Application not found",
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND"
        )
    except Exception as e:
        logger.error(f"Error in complete_assignment: {str(e)}")
        return create_error_response(
            "Internal server error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_application_attachments(request, application_id):
    """
    GET /applications/{id}/attachments
    Retrieves all attachments for a specific application.
    """
    try:
        # Get the application
        application = get_object_or_404(ClientApplication, id=application_id)
        
        # Check if user has access to this application
        assignment = application.assignments.filter(assigned_to=request.user).first()
        if not assignment:
            return create_error_response(
                "Application not found or access denied",
                status.HTTP_404_NOT_FOUND,
                "NOT_FOUND"
            )

        # Get attachments
        attachments = application.attachments.all().order_by('-uploaded_at')
        
        # Serialize attachments
        context = {'request': request}
        attachments_data = ApplicationAttachmentCacheSerializer(
            attachments, many=True, context=context
        ).data

        response_data = {
            "attachments": attachments_data
        }

        return create_success_response(response_data)

    except ClientApplication.DoesNotExist:
        return create_error_response(
            "Application not found",
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND"
        )
    except Exception as e:
        logger.error(f"Error in get_application_attachments: {str(e)}")
        return create_error_response(
            "Internal server error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR"
        )
