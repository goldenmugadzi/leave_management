from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse, FileResponse, HttpResponseNotFound, HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
import os
import logging
import mimetypes
from .models import ProcessDepartment, Process, ProcessDocument, BulkImportSession
from it.users.models import UserProfile, Regions
from approve.decorators import allowed_roles
from .ims_importer import IMSDocumentImporter
from .process_map_importer import ProcessMapImporter
from knowledge_center.models import KnowledgeCenter, KnowldgeCentreFile, FolderApplication, KnowledgeCentreFolder


# Set up logging for document access
logger = logging.getLogger(__name__)


def get_request_user_profile(request):
    """
    Safely return the UserProfile associated with the request user.
    Handles scenarios where the authenticated user *is* a UserProfile
    instance as well as when it is attached via a related attribute.
    """
    user = getattr(request, "user", None)
    if isinstance(user, UserProfile):
        return user
    if user and hasattr(user, "userprofile"):
        return user.userprofile
    return None


def sanitize_filename(filename):
    """
    Sanitize filename by removing or replacing invalid characters.
    """
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Ensure filename is not empty
    if not filename:
        filename = 'document'
    return filename


def log_process_activity(user, action, process=None, document=None, details=None):
    """
    Log process management activities for audit purposes.
    
    Args:
        user: User performing the action
        action: Action being performed (view, create, edit, delete, download, upload)
        process: Process object (if applicable)
        document: ProcessDocument object (if applicable)
        details: Additional details about the action
    """
    log_message = f"User {user.username} ({user.get_full_name()}) performed '{action}'"
    
    if process:
        log_message += f" on process '{process.name}' (ID: {process.id})"
    
    if document:
        log_message += f" on document '{document.filename}' (ID: {document.id})"
    
    if details:
        log_message += f" - Details: {details}"
    
    logger.info(log_message)


@login_required
def process_list_view(request):
    """
    Display processes in a table format with search functionality.
    Enhanced to show all processes in a spreadsheet-like view.
    
    Requirements: 1.1, 3.1, 3.3
    """
    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '')
    region_filter = request.GET.get('region', '')
    view_mode = request.GET.get('view', 'table')  # Default to table view as users prefer it
    
    # Log user access
    log_process_activity(request.user, 'view_process_list', details=f"Search query: '{search_query}'" if search_query else None)
    
    # Get all departments with process counts for department view
    departments = ProcessDepartment.objects.annotate(
        process_count=Count('processes', filter=Q(processes__is_active=True))
    ).order_by('order', 'name')
    
    # Get all processes for table view
    processes = Process.objects.filter(is_active=True).select_related(
        'department', 'region', 'created_by'
    ).prefetch_related('documents')
    
    # Apply filters
    if search_query:
        processes = processes.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(process_code__icontains=search_query)
        )
    
    if department_filter:
        processes = processes.filter(department_id=department_filter)
    
    if region_filter:
        processes = processes.filter(region_id=region_filter)
    
    # Order processes
    processes = processes.order_by('department__order', 'name')
    
    # Get available regions for filters
    available_regions = Regions.objects.all().order_by('region')
    
    # Pagination for table view
    paginator = Paginator(processes, 25)  # 25 processes per page for table view
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # For search results in department view
    search_results = None
    if search_query and view_mode == 'departments':
        search_results = {}
        for process in processes:
            dept_name = process.department.name
            if dept_name not in search_results:
                search_results[dept_name] = []
            search_results[dept_name].append(process)
    
    context = {
        'departments': departments,
        'processes': page_obj,
        'all_processes': processes,
        'search_query': search_query,
        'department_filter': department_filter,
        'region_filter': region_filter,
        'view_mode': view_mode,
        'search_results': search_results,
        'available_regions': available_regions,
        'total_processes': Process.objects.filter(is_active=True).count(),
        'filtered_count': processes.count(),
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'process_management/process_list.html', context)


@login_required
def process_department_view(request, department_id):
    """
    Display processes within a specific department with filtering and pagination.
    
    Requirements: 3.2, 3.3
    """
    department = get_object_or_404(ProcessDepartment, id=department_id)
    
    # Get filter parameters
    region_id = request.GET.get('region')
    search_query = request.GET.get('search', '').strip()
    
    # Start with all active processes in the department
    processes = Process.objects.filter(
        department=department,
        is_active=True
    ).select_related('department', 'region', 'created_by')
    
    # Apply search filter
    if search_query:
        processes = processes.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(process_code__icontains=search_query)
        )
    
    # Apply region filter
    if region_id:
        processes = processes.filter(region_id=region_id)
    
    # Order processes
    processes = processes.order_by('name')
    
    # Get available regions for filters
    from it.users.models import Regions
    available_regions = Regions.objects.all().order_by('region')
    
    # Pagination
    paginator = Paginator(processes, 12)  # 12 processes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'department': department,
        'processes': page_obj,
        'available_regions': available_regions,
        'selected_region': region_id,
        'search_query': search_query,
        'total_processes': processes.count(),
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'process_management/department_processes.html', context)


@login_required
def process_detail_view(request, process_id):
    """
    Display individual process with all components (process map, procedure, risk register).
    Handle missing document scenarios gracefully.
    
    Requirements: 1.2, 1.3, 1.4
    """
    process = get_object_or_404(Process, id=process_id, is_active=True)
    
    # Get documents grouped by type
    documents_by_type = process.get_documents_by_type()
    
    # Get document availability status
    document_status = {
        'process_map': {
            'available': process.has_process_map(),
            'document': documents_by_type.get('process_map'),
            'display_name': 'Process Map'
        },
        'procedure': {
            'available': process.has_procedure(),
            'document': documents_by_type.get('procedure'),
            'display_name': 'Procedure'
        },
        'risk_register': {
            'available': process.has_risk_register(),
            'document': documents_by_type.get('risk_register'),
            'display_name': 'Risk and Opportunity Register'
        },
        'objectives_targets': {
            'available': process.has_objectives_targets(),
            'document': documents_by_type.get('objectives_targets'),
            'display_name': 'Objectives and Targets'
        },
        'internal_external_issues': {
            'available': process.has_internal_external_issues(),
            'document': documents_by_type.get('internal_external_issues'),
            'display_name': 'Internal and External Issues'
        },
        'stakeholder_needs': {
            'available': process.has_stakeholder_needs(),
            'document': documents_by_type.get('stakeholder_needs'),
            'display_name': 'Stakeholders and Their Needs'
        },
        'legal_register': {
            'available': process.has_legal_register(),
            'document': documents_by_type.get('legal_register'),
            'display_name': 'Legal Register'
        }
    }
    
    # Get all document versions for each type (for version history)
    document_versions = {}
    all_document_types = ['process_map', 'procedure', 'risk_register', 'objectives_targets', 'internal_external_issues', 'stakeholder_needs', 'legal_register']
    for doc_type in all_document_types:
        versions = ProcessDocument.objects.filter(
            process=process,
            document_type=doc_type
        ).order_by('-uploaded_at')
        document_versions[doc_type] = versions
    
    # Calculate completeness percentage
    total_components = 7
    available_components = sum(1 for status in document_status.values() if status['available'])
    completeness_percentage = (available_components / total_components) * 100
    
    # Calculate stroke-dasharray for progress circle (circumference = 2 * π * r = 2 * 3.14159 * 50 = 314)
    stroke_dasharray = int(completeness_percentage * 3.14)
    
    context = {
        'process': process,
        'document_status': document_status,
        'document_versions': document_versions,
        'completeness_percentage': completeness_percentage,
        'stroke_dasharray': stroke_dasharray,
        'available_components': available_components,
        'total_components': total_components,
    }
    
    return render(request, 'process_management/process_detail.html', context)


@login_required
def document_download_view(request, document_id):
    """
    Secure file download function with access control, logging, and error handling.
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    try:
        # Get the document with related process information
        document = get_object_or_404(
            ProcessDocument.objects.select_related('process', 'uploaded_by'),
            id=document_id
        )
        
        # Access control - ensure user has permission to access this document
        # For now, all authenticated users can access documents
        # This can be extended with role-based permissions later
        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized access attempt to document {document_id} by anonymous user")
            return HttpResponseForbidden("Access denied")
        
        # Check if the document file exists
        if not document.file or not os.path.exists(document.file.path):
            logger.error(f"Document file not found: {document.file.path if document.file else 'No file path'} for document {document_id}")
            messages.error(request, "The requested document file could not be found.")
            return HttpResponseNotFound("Document file not found")
        
        # Log the download attempt
        log_process_activity(request.user, 'download_document', process=document.process, document=document)
        
        # Determine content type based on file extension
        content_type, _ = mimetypes.guess_type(document.filename)
        if not content_type:
            # Default content type for unknown files
            content_type = 'application/octet-stream'
        
        # Handle different document types appropriately
        file_extension = document.get_file_extension().lower()
        
        # For PDF files, try to display inline if possible
        if file_extension == 'pdf':
            content_type = 'application/pdf'
            disposition = 'inline'
        # For image files, display inline
        elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            disposition = 'inline'
        # For other files, force download
        else:
            disposition = 'attachment'
        
        try:
            # Create the file response
            response = FileResponse(
                open(document.file.path, 'rb'),
                content_type=content_type
            )
            
            # Set the content disposition header
            filename = document.filename
            if disposition == 'attachment':
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
            else:
                response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            # Add additional headers for security and caching
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['Cache-Control'] = 'private, max-age=3600'  # Cache for 1 hour
            
            # Log successful download
            logger.info(f"Document download successful: {filename} (ID: {document_id}) "
                       f"by user {request.user.username}")
            
            return response
            
        except IOError as e:
            logger.error(f"IO error reading document file {document.file.path}: {str(e)}")
            messages.error(request, "Error reading the document file.")
            return HttpResponseNotFound("Error reading document file")
            
    except ProcessDocument.DoesNotExist:
        logger.warning(f"Attempt to access non-existent document {document_id} by user {request.user.username}")
        return HttpResponseNotFound("Document not found")
        
    except Exception as e:
        logger.error(f"Unexpected error in document download for document {document_id}: {str(e)}")
        messages.error(request, "An unexpected error occurred while downloading the document.")
        return HttpResponseNotFound("Error processing download request")


@login_required
def document_download_by_process_and_type(request, process_id, document_type):
    """
    Download the current document of a specific type for a process.
    Convenience endpoint for direct access to process components.
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    try:
        # Validate document type
        valid_types = [choice[0] for choice in ProcessDocument.DOCUMENT_TYPES]
        if document_type not in valid_types:
            logger.warning(f"Invalid document type '{document_type}' requested by user {request.user.username}")
            return HttpResponseNotFound("Invalid document type")
        
        # Get the process
        process = get_object_or_404(Process, id=process_id, is_active=True)
        
        # Get the current document of the specified type
        try:
            document = ProcessDocument.objects.get(
                process=process,
                document_type=document_type,
                is_current=True
            )
            
            # Redirect to the main download view
            return document_download_view(request, document.id)
            
        except ProcessDocument.DoesNotExist:
            logger.info(f"No current {document_type} document found for process {process_id} "
                       f"requested by user {request.user.username}")
            messages.info(request, f"No {document_type.replace('_', ' ').title()} document is available for this process.")
            return HttpResponseNotFound(f"No {document_type} document found")
            
    except Process.DoesNotExist:
        logger.warning(f"Attempt to access documents for non-existent process {process_id} "
                      f"by user {request.user.username}")
        return HttpResponseNotFound("Process not found")
        
    except Exception as e:
        logger.error(f"Unexpected error in document download by type for process {process_id}, "
                    f"type {document_type}: {str(e)}")
        return HttpResponseNotFound("Error processing download request")


@login_required
# @allowed_roles(['Administrator', 'Process Manager', 'Department Manager'], ['process_management'])
def document_upload_view(request, process_id):
    """
    Handle document upload for a specific process with custom forms.
    
    Requirements: 2.2, 2.3
    """
    process = get_object_or_404(Process, id=process_id, is_active=True)
    
    if request.method == 'POST':
        return handle_document_upload(request, process)
    
    # GET request - display upload form
    selected_type = request.GET.get('type', '')
    context = {
        'process': process,
        'document_types': ProcessDocument.DOCUMENT_TYPES,
        'selected_type': selected_type,
        'max_file_size': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
        'allowed_extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
    }
    
    return render(request, 'process_management/document_upload.html', context)


def handle_document_upload(request, process):
    """
    Handle the actual document upload with validation and virus scanning.
    
    Requirements: 2.2, 2.3
    """
    try:
        # Get form data
        document_type = request.POST.get('document_type')
        version = request.POST.get('version', '1.0').strip()
        uploaded_file = request.FILES.get('document_file')
        replace_current = request.POST.get('replace_current') == 'on'
        
        # Validate required fields
        if not document_type or not uploaded_file:
            messages.error(request, "Document type and file are required.")
            return render(request, 'process_management/document_upload.html', {
                'process': process,
                'document_types': ProcessDocument.DOCUMENT_TYPES,
            })
        
        # Validate document type
        valid_types = [choice[0] for choice in ProcessDocument.DOCUMENT_TYPES]
        if document_type not in valid_types:
            messages.error(request, "Invalid document type selected.")
            return render(request, 'process_management/document_upload.html', {
                'process': process,
                'document_types': ProcessDocument.DOCUMENT_TYPES,
            })
        
        # Validate file
        validation_result = validate_uploaded_file(uploaded_file)
        if not validation_result['valid']:
            messages.error(request, validation_result['error'])
            return render(request, 'process_management/document_upload.html', {
                'process': process,
                'document_types': ProcessDocument.DOCUMENT_TYPES,
            })
        
        # Perform virus scanning (mock implementation)
        scan_result = perform_virus_scan(uploaded_file)
        if not scan_result['clean']:
            logger.warning(f"Virus detected in uploaded file {uploaded_file.name} "
                          f"by user {request.user.username}")
            messages.error(request, "File failed security scan. Please contact administrator.")
            return render(request, 'process_management/document_upload.html', {
                'process': process,
                'document_types': ProcessDocument.DOCUMENT_TYPES,
            })
        
        # Handle document versioning and replacement
        if replace_current:
            # Mark existing current documents as not current
            ProcessDocument.objects.filter(
                process=process,
                document_type=document_type,
                is_current=True
            ).update(is_current=False)
            is_current = True
        else:
            # Check if current document already exists
            current_exists = ProcessDocument.objects.filter(
                process=process,
                document_type=document_type,
                is_current=True
            ).exists()
            is_current = not current_exists
        
        # Create new document record
        document = ProcessDocument.objects.create(
            process=process,
            document_type=document_type,
            file=uploaded_file,
            filename=uploaded_file.name,
            version=version,
            is_current=is_current,
            uploaded_by=request.user
        )
        
        # Log successful upload
        logger.info(f"Document uploaded successfully: {uploaded_file.name} "
                   f"(ID: {document.id}) for process '{process.name}' "
                   f"by user {request.user.username}")
        
        # Success message
        doc_type_display = document.get_document_type_display()
        if replace_current:
            messages.success(request, f"{doc_type_display} has been updated successfully.")
        else:
            messages.success(request, f"{doc_type_display} has been uploaded successfully.")
        
        # Redirect to process detail page
        return redirect('process_management:process_detail', process_id=process.id)
        
    except Exception as e:
        logger.error(f"Error uploading document for process {process.id}: {str(e)}")
        messages.error(request, "An error occurred while uploading the document. Please try again.")
        return render(request, 'process_management/document_upload.html', {
            'process': process,
            'document_types': ProcessDocument.DOCUMENT_TYPES,
        })


@login_required
def manage_process_resources_view(request):
    """
    Provide a simple management interface for process departments and regions.
    Allows creating new department and region records without leaving the app.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_department':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            order_value = request.POST.get('order', '').strip()
            
            if not name:
                messages.error(request, "Department name is required.")
                return redirect('process_management:manage_resources')
            
            try:
                order = int(order_value) if order_value else 0
                if order < 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Order must be a non-negative integer.")
                return redirect('process_management:manage_resources')
            
            if ProcessDepartment.objects.filter(name__iexact=name).exists():
                messages.error(request, f"Department '{name}' already exists.")
                return redirect('process_management:manage_resources')
            
            try:
                ProcessDepartment.objects.create(
                    name=name,
                    description=description,
                    order=order
                )
                messages.success(request, f"Department '{name}' created successfully.")
            except Exception as exc:
                logger.error(f"Failed to create department '{name}': {exc}")
                messages.error(request, "Could not create department. Please try again.")
            
            return redirect('process_management:manage_resources')
        
        if action == 'create_region':
            region_name = request.POST.get('region', '').strip()
            region_code = request.POST.get('code', '').strip()
            
            if not region_name:
                messages.error(request, "Region name is required.")
                return redirect('process_management:manage_resources')
            
            if Regions.objects.filter(region__iexact=region_name).exists():
                messages.error(request, f"Region '{region_name}' already exists.")
                return redirect('process_management:manage_resources')
            
            try:
                Regions.objects.create(region=region_name, code=region_code)
                messages.success(request, f"Region '{region_name}' created successfully.")
            except Exception as exc:
                logger.error(f"Failed to create region '{region_name}': {exc}")
                messages.error(request, "Could not create region. Please try again.")
            
            return redirect('process_management:manage_resources')
        
        if action == 'update_department':
            department_id = request.POST.get('department_id')
            department = get_object_or_404(ProcessDepartment, id=department_id)
            
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            order_value = request.POST.get('order', '').strip()
            
            if not name:
                messages.error(request, "Department name is required.")
                return redirect(f"{request.path}?edit_department={department.id}")
            
            try:
                order = int(order_value) if order_value else 0
                if order < 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Order must be a non-negative integer.")
                return redirect(f"{request.path}?edit_department={department.id}")
            
            if ProcessDepartment.objects.filter(name__iexact=name).exclude(id=department.id).exists():
                messages.error(request, f"Another department already uses the name '{name}'.")
                return redirect(f"{request.path}?edit_department={department.id}")
            
            department.name = name
            department.description = description
            department.order = order
            
            try:
                department.save()
                messages.success(request, f"Department '{name}' updated successfully.")
            except Exception as exc:
                logger.error(f"Failed to update department '{department.id}': {exc}")
                messages.error(request, "Could not update department. Please try again.")
                return redirect(f"{request.path}?edit_department={department.id}")
            
            return redirect('process_management:manage_resources')
        
        if action == 'delete_department':
            department_id = request.POST.get('department_id')
            department = get_object_or_404(ProcessDepartment, id=department_id)
            
            if department.processes.exists():
                messages.error(request, "Cannot delete department while processes are assigned to it.")
                return redirect('process_management:manage_resources')
            
            try:
                department.delete()
                messages.success(request, f"Department '{department.name}' deleted successfully.")
            except Exception as exc:
                logger.error(f"Failed to delete department '{department.id}': {exc}")
                messages.error(request, "Could not delete department. Please try again.")
            
            return redirect('process_management:manage_resources')
        
        if action == 'update_region':
            region_id = request.POST.get('region_id')
            region = get_object_or_404(Regions, id=region_id)
            
            region_name = request.POST.get('region', '').strip()
            region_code = request.POST.get('code', '').strip()
            
            if not region_name:
                messages.error(request, "Region name is required.")
                return redirect(f"{request.path}?edit_region={region.id}")
            
            if Regions.objects.filter(region__iexact=region_name).exclude(id=region.id).exists():
                messages.error(request, f"Another region already uses the name '{region_name}'.")
                return redirect(f"{request.path}?edit_region={region.id}")
            
            region.region = region_name
            region.code = region_code
            
            try:
                region.save()
                messages.success(request, f"Region '{region_name}' updated successfully.")
            except Exception as exc:
                logger.error(f"Failed to update region '{region.id}': {exc}")
                messages.error(request, "Could not update region. Please try again.")
                return redirect(f"{request.path}?edit_region={region.id}")
            
            return redirect('process_management:manage_resources')
        
        if action == 'delete_region':
            region_id = request.POST.get('region_id')
            region = get_object_or_404(Regions, id=region_id)
            
            if Process.objects.filter(region=region).exists():
                messages.error(request, "Cannot delete region while processes reference it.")
                return redirect('process_management:manage_resources')
            
            try:
                region.delete()
                messages.success(request, f"Region '{region.region}' deleted successfully.")
            except Exception as exc:
                logger.error(f"Failed to delete region '{region.id}': {exc}")
                messages.error(request, "Could not delete region. Please try again.")
            
            return redirect('process_management:manage_resources')
    
    departments = ProcessDepartment.objects.all().order_by('order', 'name')
    regions = Regions.objects.all().order_by('region')
    edit_department = None
    edit_region = None
    
    edit_department_id = request.GET.get('edit_department')
    if edit_department_id:
        edit_department = get_object_or_404(ProcessDepartment, id=edit_department_id)
    
    edit_region_id = request.GET.get('edit_region')
    if edit_region_id:
        edit_region = get_object_or_404(Regions, id=edit_region_id)
    
    context = {
        'departments': departments,
        'regions': regions,
        'edit_department': edit_department,
        'edit_region': edit_region,
    }
    return render(request, 'process_management/manage_resources.html', context)


def validate_uploaded_file(uploaded_file):
    """
    Validate uploaded file for size, type, and other constraints.
    
    Requirements: 2.2, 2.3
    """
    # Define allowed file extensions and their MIME types
    ALLOWED_EXTENSIONS = {
        '.pdf': ['application/pdf'],
        '.doc': ['application/msword'],
        '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        '.xls': ['application/vnd.ms-excel'],
        '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        '.ppt': ['application/vnd.ms-powerpoint'],
        '.pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
    }
    
    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    
    try:
        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            return {
                'valid': False,
                'error': f"File size ({uploaded_file.size // (1024*1024)}MB) exceeds maximum allowed size (50MB)."
            }
        
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            allowed_exts = ', '.join(ALLOWED_EXTENSIONS.keys())
            return {
                'valid': False,
                'error': f"File type '{file_extension}' is not allowed. Allowed types: {allowed_exts}"
            }
        
        # Check MIME type (basic validation)
        if hasattr(uploaded_file, 'content_type'):
            allowed_mime_types = ALLOWED_EXTENSIONS[file_extension]
            if uploaded_file.content_type not in allowed_mime_types:
                return {
                    'valid': False,
                    'error': f"File content type '{uploaded_file.content_type}' does not match expected type for {file_extension} files."
                }
        
        # Check for empty file
        if uploaded_file.size == 0:
            return {
                'valid': False,
                'error': "Uploaded file is empty."
            }
        
        # Validate filename
        if not uploaded_file.name or len(uploaded_file.name.strip()) == 0:
            return {
                'valid': False,
                'error': "File must have a valid filename."
            }
        
        # Check for potentially dangerous filenames
        dangerous_patterns = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(pattern in uploaded_file.name for pattern in dangerous_patterns):
            return {
                'valid': False,
                'error': "Filename contains invalid characters."
            }
        
        return {'valid': True, 'error': None}
        
    except Exception as e:
        logger.error(f"Error validating uploaded file: {str(e)}")
        return {
            'valid': False,
            'error': "Error validating file. Please try again."
        }


def perform_virus_scan(uploaded_file):
    """
    Perform virus scanning on uploaded file.
    This is a mock implementation - in production, integrate with actual antivirus solution.
    
    Requirements: 2.2, 2.3
    """
    try:
        # Mock virus scanning - in production, integrate with ClamAV or similar
        # For now, we'll do basic checks for suspicious content
        
        # Read first few bytes to check for suspicious patterns
        uploaded_file.seek(0)
        file_header = uploaded_file.read(1024)
        uploaded_file.seek(0)  # Reset file pointer
        
        # Basic checks for suspicious content (this is very basic)
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in file_header.lower():
                logger.warning(f"Suspicious pattern detected in file: {uploaded_file.name}")
                return {
                    'clean': False,
                    'threat': 'Suspicious content detected'
                }
        
        # In production, you would integrate with an actual antivirus engine here
        # Example with ClamAV:
        # import pyclamd
        # cd = pyclamd.ClamdUnixSocket()
        # scan_result = cd.scan_stream(uploaded_file.read())
        # if scan_result:
        #     return {'clean': False, 'threat': scan_result}
        
        return {'clean': True, 'threat': None}
        
    except Exception as e:
        logger.error(f"Error during virus scan: {str(e)}")
        # In case of scan error, err on the side of caution
        return {
            'clean': False,
            'threat': 'Scan error - file rejected for security'
        }


@login_required
# @allowed_roles(['Administrator', 'Process Manager', 'Department Manager'], ['process_management'])
def document_replace_view(request, document_id):
    """
    Replace an existing document with a new version.
    
    Requirements: 2.2, 2.3
    """
    document = get_object_or_404(ProcessDocument, id=document_id)
    process = document.process
    
    if request.method == 'POST':
        # Handle replacement upload
        uploaded_file = request.FILES.get('document_file')
        version = request.POST.get('version', '1.0').strip()
        
        if not uploaded_file:
            messages.error(request, "Please select a file to upload.")
            return redirect('process_management:process_detail', process_id=process.id)
        
        # Validate file
        validation_result = validate_uploaded_file(uploaded_file)
        if not validation_result['valid']:
            messages.error(request, validation_result['error'])
            return redirect('process_management:process_detail', process_id=process.id)
        
        # Perform virus scanning
        scan_result = perform_virus_scan(uploaded_file)
        if not scan_result['clean']:
            messages.error(request, "File failed security scan. Please contact administrator.")
            return redirect('process_management:process_detail', process_id=process.id)
        
        try:
            # Mark current document as not current
            document.is_current = False
            document.save()
            
            # Create new document version
            new_document = ProcessDocument.objects.create(
                process=process,
                document_type=document.document_type,
                file=uploaded_file,
                filename=uploaded_file.name,
                version=version,
                is_current=True,
                uploaded_by=request.user
            )
            
            # Log the replacement
            logger.info(f"Document replaced: {document.filename} (ID: {document.id}) "
                       f"with {uploaded_file.name} (ID: {new_document.id}) "
                       f"by user {request.user.username}")
            
            messages.success(request, f"{document.get_document_type_display()} has been updated successfully.")
            
        except Exception as e:
            logger.error(f"Error replacing document {document_id}: {str(e)}")
            messages.error(request, "An error occurred while updating the document.")
        
        return redirect('process_management:process_detail', process_id=process.id)
    
    # GET request - show confirmation
    context = {
        'document': document,
        'process': process,
    }
    return render(request, 'process_management/document_replace.html', context)

@login_required
# @allowed_roles(['Administrator', 'Process Manager', 'Department Manager'], ['process_management'])
def process_create_view(request):
    """
    Create a new process with form validation.
    
    Requirements: 2.1
    """
    if request.method == 'POST':
        return handle_process_creation(request)
    
    selected_department = request.GET.get('department', '')
    
    context = {
        'departments': ProcessDepartment.objects.all().order_by('order', 'name'),
        'regions': Regions.objects.all().order_by('region'),

        'selected_department': selected_department,
        'form_title': 'Create New Process',
        'submit_text': 'Create Process',
    }
    
    return render(request, 'process_management/process_form.html', context)


def handle_process_creation(request):
    """
    Handle the actual process creation with validation.
    
    Requirements: 2.1
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        department_id = request.POST.get('department')
        region_id = request.POST.get('region') or None
        process_code = request.POST.get('process_code', '').strip()
        
        # Validate required fields
        if not name:
            messages.error(request, "Process name is required.")
            return redirect('process_management:process_create')
        
        if not department_id:
            messages.error(request, "Department is required.")
            return redirect('process_management:process_create')
        
        # Validate department exists
        try:
            department = ProcessDepartment.objects.get(id=department_id)
        except ProcessDepartment.DoesNotExist:
            messages.error(request, "Invalid department selected.")
            return redirect('process_management:process_create')
        
        # Process code is optional and no longer needs uniqueness validation
        # Create the process
        process = Process.objects.create(
            name=name,
            description=description,
            department=department,
            region_id=region_id if region_id else None,

            process_code=process_code if process_code else '',
            created_by=request.user
        )
        
        # Log the creation
        logger.info(f"Process created: '{name}' (ID: {process.id}) "
                   f"by user {request.user.username}")
        
        messages.success(request, f"Process '{name}' has been created successfully.")
        return redirect('process_management:process_detail', process_id=process.id)
        
    except Exception as e:
        logger.error(f"Error creating process: {str(e)}")
        messages.error(request, "An error occurred while creating the process. Please try again.")
        return redirect('process_management:process_create')


@login_required
# @allowed_roles(['Administrator', 'Process Manager', 'Department Manager'], ['process_management'])
def process_edit_view(request, process_id):
    """
    Edit an existing process.
    
    Requirements: 2.1
    """
    process = get_object_or_404(Process, id=process_id)
    
    if request.method == 'POST':
        return handle_process_update(request, process)
    
    # GET request - display edit form
    from it.users.models import Regions
    
    context = {
        'process': process,
        'departments': ProcessDepartment.objects.all().order_by('order', 'name'),
        'regions': Regions.objects.all().order_by('region'),

        'form_title': f'Edit Process: {process.name}',
        'submit_text': 'Update Process',
    }
    
    return render(request, 'process_management/process_form.html', context)


def handle_process_update(request, process):
    """
    Handle the actual process update with validation.
    
    Requirements: 2.1
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        department_id = request.POST.get('department')
        region_id = request.POST.get('region') or None
        process_code = request.POST.get('process_code', '').strip()
        
        # Validate required fields
        if not name:
            messages.error(request, "Process name is required.")
            return redirect('process_management:process_edit', process_id=process.id)
        
        if not department_id:
            messages.error(request, "Department is required.")
            return redirect('process_management:process_edit', process_id=process.id)
        
        # Validate department exists
        try:
            department = ProcessDepartment.objects.get(id=department_id)
        except ProcessDepartment.DoesNotExist:
            messages.error(request, "Invalid department selected.")
            return redirect('process_management:process_edit', process_id=process.id)
        
        # Process code is optional and no longer needs uniqueness validation
        
        # Update the process
        process.name = name
        process.description = description
        process.department = department
        process.region_id = region_id if region_id else None

        process.process_code = process_code if process_code else ''
        process.save()
        
        # Log the update
        logger.info(f"Process updated: '{name}' (ID: {process.id}) "
                   f"by user {request.user.username}")
        
        messages.success(request, f"Process '{name}' has been updated successfully.")
        return redirect('process_management:process_detail', process_id=process.id)
        
    except Exception as e:
        logger.error(f"Error updating process {process.id}: {str(e)}")
        messages.error(request, "An error occurred while updating the process. Please try again.")
        return redirect('process_management:process_edit', process_id=process.id)


@login_required
# @allowed_roles(['Administrator', 'Process Manager'], ['process_management'])
def process_delete_view(request, process_id):
    """
    Delete (archive) a process.
    
    Requirements: 2.4
    """
    process = get_object_or_404(Process, id=process_id)
    
    if request.method == 'POST':
        try:
            # Archive the process instead of deleting
            process.is_active = False
            process.save()
            
            # Log the deletion
            logger.info(f"Process archived: '{process.name}' (ID: {process.id}) "
                       f"by user {request.user.username}")
            
            messages.success(request, f"Process '{process.name}' has been archived successfully.")
            return redirect('process_management:department_processes', department_id=process.department.id)
            
        except Exception as e:
            logger.error(f"Error archiving process {process.id}: {str(e)}")
            messages.error(request, "An error occurred while archiving the process.")
            return redirect('process_management:process_detail', process_id=process.id)
    
    # GET request - show confirmation
    context = {
        'process': process,
    }
    return render(request, 'process_management/process_delete_confirm.html', context)


# ===== IMS IMPORT VIEWS =====

@login_required
# @allowed_roles(['Global Admin', 'System Admin'], ['process_management'])
def ims_import_view(request):
    """
    IMS Document Register import interface.
    Allows importing processes from Excel files or using predefined data.
    """
    if request.method == 'POST':
        import_type = request.POST.get('import_type')
        
        if import_type == 'predefined':
            # Import predefined IMS processes
            importer = IMSDocumentImporter()
            result = importer.populate_predefined_ims_processes()
            
            if result['success']:
                messages.success(request, 
                    f"Successfully imported IMS processes! "
                    f"Created: {result['processes_created']}, "
                    f"Updated: {result['processes_updated']}")
                
                # Log the import
                log_process_activity(
                    user=request.user,
                    action='ims_import_predefined',
                    details=f"Created: {result['processes_created']}, Updated: {result['processes_updated']}"
                )
            else:
                messages.error(request, f"Import failed: {result.get('error', 'Unknown error')}")
                
        elif import_type == 'excel' and 'excel_file' in request.FILES:
            # Import from Excel file
            excel_file = request.FILES['excel_file']
            
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                temp_path = tmp_file.name
            
            try:
                importer = IMSDocumentImporter()
                result = importer.import_from_excel(temp_path)
                
                if result['success']:
                    messages.success(request, 
                        f"Successfully imported from Excel! "
                        f"Created: {result['processes_created']}, "
                        f"Updated: {result['processes_updated']}")
                    
                    # Log the import
                    log_process_activity(
                        user=request.user,
                        action='ims_import_excel',
                        details=f"File: {excel_file.name}, Created: {result['processes_created']}"
                    )
                else:
                    messages.error(request, f"Import failed: {result.get('error', 'Unknown error')}")
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
        else:
            messages.error(request, "Please select a valid import option.")
            
        return redirect('process_management:ims_import')
    
    # GET request - show import form
    context = {
        'departments': ProcessDepartment.objects.all().order_by('order'),
        'total_processes': Process.objects.count(),
        'ims_processes': Process.objects.filter(ims_reference__startswith='ZETDC-HRE').count(),
    }
    return render(request, 'process_management/ims_import.html', context)


@login_required
def ims_processes_view(request):
    """
    Display IMS processes organized by department with enhanced features.
    """
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '')
    iso_clause_filter = request.GET.get('iso_clause', '')
    
    # Base queryset for IMS processes
    processes = Process.objects.filter(ims_reference__startswith='ZETDC-HRE').select_related('department')
    
    # Apply filters
    if search_query:
        processes = processes.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(ims_reference__icontains=search_query) |
            Q(iso_clause__icontains=search_query)
        )
    
    if department_filter:
        processes = processes.filter(department__name=department_filter)
        
    if iso_clause_filter:
        processes = processes.filter(iso_clause__icontains=iso_clause_filter)
    
    # Order by department and name
    processes = processes.order_by('department__order', 'name')
    
    # Group by department
    departments_data = {}
    for process in processes:
        dept_name = process.department.name
        if dept_name not in departments_data:
            departments_data[dept_name] = {
                'department': process.department,
                'processes': []
            }
        departments_data[dept_name]['processes'].append(process)
    
    # Get filter options
    all_departments = ProcessDepartment.objects.all().order_by('order')
    iso_clauses = Process.objects.filter(
        ims_reference__startswith='ZETDC-HRE',
        iso_clause__gt=''
    ).values_list('iso_clause', flat=True).distinct().order_by('iso_clause')
    
    context = {
        'departments_data': departments_data,
        'all_departments': all_departments,
        'iso_clauses': iso_clauses,
        'search_query': search_query,
        'department_filter': department_filter,
        'iso_clause_filter': iso_clause_filter,
        'total_processes': processes.count(),
    }
    
    return render(request, 'process_management/ims_processes.html', context)


@login_required
def ims_process_detail_view(request, process_id):
    """
    Enhanced process detail view for IMS processes with compliance tracking.
    """
    process = get_object_or_404(Process, id=process_id)
    
    # Log the view
    log_process_activity(request.user, 'view_ims_process', process=process)
    
    # Get all document types and their status
    document_types = ProcessDocument.DOCUMENT_TYPES
    document_grid = []
    
    for doc_type, doc_type_display in document_types:
        current_doc = process.documents.filter(
            document_type=doc_type, 
            is_current=True
        ).first()
        
        document_grid.append({
            'type': doc_type,
            'type_display': doc_type_display,
            'document': current_doc,
            'has_document': current_doc is not None,
            'is_accessible': current_doc.is_active if current_doc else False,
            'compliance_status': current_doc.compliance_status if current_doc else 'missing',
            'review_due_date': current_doc.review_due_date if current_doc else None,
            'is_overdue': current_doc.is_review_overdue() if current_doc else False,
        })
    
    # Calculate compliance metrics
    total_docs = len(document_types)
    available_docs = sum(1 for item in document_grid if item['has_document'])
    compliance_percentage = (available_docs / total_docs * 100) if total_docs > 0 else 0
    
    context = {
        'process': process,
        'document_grid': document_grid,
        'compliance_percentage': compliance_percentage,
        'total_document_types': total_docs,
        'available_documents': available_docs,
        'missing_documents': total_docs - available_docs,
    }
    
    return render(request, 'process_management/ims_process_detail.html', context)


@login_required
def knowledge_center_file_search(request):
    """
    API endpoint for searching knowledge center files with autocomplete functionality.
    Returns JSON response with file suggestions for the upload form.
    
    Requirements: File import from knowledge center
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'files': []})
    
    try:
        logger.info("Knowledge center file search started | query='%s'", query)

        # Search in KnowldgeCentreFile model (primary data source)
        kcf_files = (
            KnowldgeCentreFile.objects.filter(archived=False)
            .filter(
                Q(filename__icontains=query)
                | Q(name__icontains=query)
                | Q(folder__name__icontains=query)
                | Q(section__section__icontains=query)
                | Q(region__region__icontains=query)
            )
            .select_related('folder', 'section', 'region', 'created_by')
            .order_by('name', 'filename')
        )
        kcf_count = kcf_files.count()
        logger.debug(
            "Knowledge center file search queryset prepared | query='%s' | archived=False | count=%s",
            query,
            kcf_count,
        )
        results = []
        
        # Process KnowldgeCentreFile results - include all matches, flag availability
        for file in kcf_files:
            storage_path = getattr(file.file, 'name', None) if file.file else None
            file_exists = file.file and storage_path and default_storage.exists(storage_path)

            if not file_exists:
                logger.warning(
                    "Knowledge center file search match missing storage | id=%s | name='%s' | storage_path='%s'",
                    getattr(file, 'id', None),
                    getattr(file, 'name', None) or getattr(file, 'filename', None),
                    storage_path,
                )

            results.append({
                'id': f"kcf_{file.id}",
                'name': file.name or file.filename,
                'type': 'knowledge_centre_file',
                'file_type': 'File',
                'section': file.section.section if file.section else 'Unknown',
                'region': file.region.region if file.region else 'Unknown',
                'created_at': file.created_on.isoformat() if file.created_on else None,
                'file_path': file.file.url if file.file else None,
                'folder': file.folder.name if file.folder else 'Unknown',
                'is_available': file_exists,
            })
        
        logger.info(
            "Knowledge center file search completed | query='%s' | queryset_count=%s | result_count=%s",
            query,
            kcf_count,
            len(results),
        )
        # Sort results by relevance (exact matches first, then by name)
        results.sort(key=lambda x: (
            0 if query.lower() in x['name'].lower() else 1,
            x['name'].lower()
        ))
        
        return JsonResponse({
            'files': results,
            'query': query,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in knowledge center file search: {str(e)}")
        return JsonResponse({
            'files': [],
            'error': 'Search failed. Please try again.'
        }, status=500)


@login_required
def import_knowledge_center_file(request, process_id):
    """
    Import a file from knowledge center and attach it to a process.
    
    Requirements: File import from knowledge center
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        process = get_object_or_404(Process, id=process_id, is_active=True)
        
        # Get form data
        file_id = request.POST.get('file_id')
        document_type = request.POST.get('document_type')
        version = request.POST.get('version', '1.0').strip()
        replace_current = request.POST.get('replace_current') == 'on'
        
        # Debug logging
        logger.info(f"Import request data - file_id: {file_id}, document_type: '{document_type}' (length: {len(document_type) if document_type else 0}), version: {version}, replace_current: {replace_current}")
        
        if not file_id or not document_type:
            return JsonResponse({
                'error': 'File ID and document type are required.'
            }, status=400)
        
        # Validate document type
        valid_types = [choice[0] for choice in ProcessDocument.DOCUMENT_TYPES]
        if document_type not in valid_types:
            return JsonResponse({
                'error': 'Invalid document type selected.'
            }, status=400)
        
        # Parse file ID to determine source
        if file_id.startswith('kc_'):
            # KnowledgeCenter file
            kc_id = file_id.replace('kc_', '')
            source_file = get_object_or_404(KnowledgeCenter, id=kc_id, archived=False)
            
            # Get the actual file path
            if not source_file.filepath or not os.path.exists(source_file.filepath):
                return JsonResponse({
                    'error': 'Source file not found or inaccessible.'
                }, status=404)
            
            # Create a copy of the file
            with open(source_file.filepath, 'rb') as f:
                file_content = f.read()
            
            # Create a new file object for the process document
            new_filename = sanitize_filename(source_file.filename)
            uploaded_file = ContentFile(file_content, name=new_filename)
            
        elif file_id.startswith('kcf_'):
            # KnowldgeCentreFile
            kcf_id = file_id.replace('kcf_', '')
            source_file = get_object_or_404(KnowldgeCentreFile, id=kcf_id, archived=False)
            
            if not source_file.file or not source_file.file.name:
                return JsonResponse({
                    'error': 'Source file not found or inaccessible.'
                }, status=404)
            
            # Get the file from storage
            if not default_storage.exists(source_file.file.name):
                return JsonResponse({
                    'error': 'Source file not found in storage.'
                }, status=404)
            
            # Create a copy of the file
            file_content = default_storage.open(source_file.file.name).read()
            new_filename = sanitize_filename(source_file.filename)
            uploaded_file = ContentFile(file_content, name=new_filename)
            
        else:
            return JsonResponse({
                'error': 'Invalid file ID format.'
            }, status=400)
        
        # Check if current document already exists
        current_exists = ProcessDocument.objects.filter(
            process=process,
            document_type=document_type,
            is_current=True
        ).exists()
        
        # Handle document versioning and replacement
        if replace_current:
            # Mark existing current documents as not current
            ProcessDocument.objects.filter(
                process=process,
                document_type=document_type,
                is_current=True
            ).update(is_current=False)
            is_current = True
        else:
            is_current = not current_exists
        
        # If there's already a current document and we're not replacing it,
        # we should update the existing one instead of creating a new one
        if current_exists and not replace_current:
            # Update the existing current document
            existing_doc = ProcessDocument.objects.get(
                process=process,
                document_type=document_type,
                is_current=True
            )
            existing_doc.file = uploaded_file
            existing_doc.filename = new_filename
            existing_doc.version = version
            existing_doc.uploaded_by = get_request_user_profile(request)
            existing_doc.save()
            
            # Log successful update
            logger.info(f"Document updated from knowledge center: {new_filename} "
                       f"(ID: {existing_doc.id}) for process '{process.name}' "
                       f"by user {request.user.username}")
            
            # Success response - redirect to process detail page
            doc_type_display = existing_doc.get_document_type_display()
            try:
                messages.success(request, f"{doc_type_display} has been updated successfully.")
            except:
                # Messages middleware not available (e.g., in testing)
                pass
            
            return redirect('process_management:process_detail', process_id=process.id)
        
        # Create new document record
        document = ProcessDocument.objects.create(
            process=process,
            document_type=document_type,
            file=uploaded_file,
            filename=new_filename,
            version=version,
            is_current=is_current,
            uploaded_by=get_request_user_profile(request)
        )
        
        # Log successful import
        logger.info(f"Document imported from knowledge center: {new_filename} "
                   f"(ID: {document.id}) for process '{process.name}' "
                   f"by user {request.user.username}")
        
        # Success response - redirect to process detail page
        doc_type_display = document.get_document_type_display()
        try:
            messages.success(request, f"{doc_type_display} has been imported successfully.")
        except:
            # Messages middleware not available (e.g., in testing)
            pass
        
        # Redirect to process detail page
        return redirect('process_management:process_detail', process_id=process.id)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error importing knowledge center file: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        return JsonResponse({
            'error': 'Failed to import file. Please try again.',
            'debug': str(e) if settings.DEBUG else None
        }, status=500)


# ===== BULK IMPORT VIEWS =====

@login_required
def bulk_import_dashboard(request):
    """
    Dashboard for managing bulk import sessions.
    Shows recent imports and allows creating new import sessions.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        messages.error(request, "No user profile associated with your account. Please contact the administrator.")
        return redirect('process_management:process_list')

    # Get recent import sessions
    recent_imports = BulkImportSession.objects.filter(
        created_by=user_profile
    ).order_by('-created_at')[:10]

    # Get import statistics
    total_imports = BulkImportSession.objects.filter(
        created_by=user_profile
    ).count()
    completed_imports = BulkImportSession.objects.filter(
        created_by=user_profile, status='completed'
    ).count()
    failed_imports = BulkImportSession.objects.filter(
        created_by=user_profile, status='failed'
    ).count()

    # Get active imports (analyzing or importing)
    active_imports = BulkImportSession.objects.filter(
        created_by=user_profile,
        status__in=['analyzing', 'importing']
    ).order_by('-created_at')

    context = {
        'recent_imports': recent_imports,
        'total_imports': total_imports,
        'completed_imports': completed_imports,
        'failed_imports': failed_imports,
        'active_imports': active_imports,
        'page_title': 'Bulk Import Dashboard'
    }

    return render(request, 'process_management/bulk_import_dashboard.html', context)


@login_required
def bulk_import_process_maps(request):
    """
    Interface for selecting and configuring bulk import of process maps.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        messages.error(request, "No user profile associated with your account. Please contact the administrator.")
        return redirect('process_management:bulk_import_dashboard')

    if request.method == 'POST':
        # Create new import session
        import_session = BulkImportSession.objects.create(
            import_id=f"bulk_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            import_type='process_maps',
            application_name=request.POST.get('application_name', "PROCESSES AND PROCEDURES"),
            folder_name=request.POST.get('folder_name', "PROCESS MAPS"),
            selected_folders=request.POST.getlist('selected_folders'),
            created_by=user_profile
        )

        # Redirect to preview
        return redirect('process_management:bulk_import_preview', import_id=import_session.import_id)

    # Get available applications and folders
    applications = FolderApplication.objects.all()
    root_folders = KnowledgeCentreFolder.objects.filter(parent__isnull=True)

    context = {
        'applications': applications,
        'root_folders': root_folders,
        'page_title': 'Bulk Import Process Maps'
    }

    return render(request, 'process_management/bulk_import_process_maps.html', context)


@login_required
def bulk_import_preview(request, import_id):
    """
    Preview what will be imported before execution.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        messages.error(request, "No user profile associated with your account. Please contact the administrator.")
        return redirect('process_management:bulk_import_dashboard')

    try:
        import_session = BulkImportSession.objects.get(
            import_id=import_id,
            created_by=user_profile
        )
    except BulkImportSession.DoesNotExist:
        messages.error(request, "Import session not found.")
        return redirect('process_management:bulk_import_dashboard')

    if request.method == 'POST':
        # Start the import process
        return redirect('process_management:bulk_import_execute', import_id=import_session.import_id)

    # If preview not ready, trigger analysis
    if import_session.status == 'created':
        # Start analysis in background (for now, do it synchronously)
        analyzer = BulkImportAnalyzer(import_session)
        preview_data = analyzer.analyze()
        import_session.preview_data = preview_data
        import_session.total_items = preview_data.get('total_files', 0)
        import_session.save(update_fields=['preview_data', 'total_items'])
        import_session.mark_preview_ready()

    context = {
        'import_session': import_session,
        'preview_data': import_session.preview_data,
        'page_title': f'Import Preview - {import_session.import_id}'
    }

    return render(request, 'process_management/bulk_import_preview.html', context)


@login_required
def bulk_import_execute(request, import_id):
    """
    Execute the bulk import process.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        messages.error(request, "No user profile associated with your account. Please contact the administrator.")
        return redirect('process_management:bulk_import_dashboard')

    try:
        import_session = BulkImportSession.objects.get(
            import_id=import_id,
            created_by=user_profile
        )
    except BulkImportSession.DoesNotExist:
        messages.error(request, "Import session not found.")
        return redirect('process_management:bulk_import_dashboard')

    if import_session.status not in ['preview_ready', 'importing']:
        messages.error(request, "Import session is not ready for execution.")
        return redirect('process_management:bulk_import_preview', import_id=import_id)

    # Start import if not already started
    if import_session.status == 'preview_ready':
        import_session.mark_importing()
        # Execute the import process
        execute_bulk_import(import_session)

    context = {
        'import_session': import_session,
        'page_title': f'Import Progress - {import_session.import_id}'
    }

    return render(request, 'process_management/bulk_import_execute.html', context)


@login_required
def bulk_import_progress(request, import_id):
    """
    API endpoint for getting real-time import progress.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        return JsonResponse({'error': 'User profile not found'}, status=403)

    try:
        import_session = BulkImportSession.objects.get(import_id=import_id)
    except BulkImportSession.DoesNotExist:
        return JsonResponse({'error': 'Import session not found'}, status=404)

    # Check if user owns this session
    if import_session.created_by != user_profile:
        return JsonResponse({'error': 'Access denied'}, status=403)

    progress_data = {
        'status': import_session.status,
        'progress_percentage': import_session.get_progress_percentage(),
        'total_items': import_session.total_items,
        'processed_items': import_session.processed_items,
        'successful_items': import_session.successful_items,
        'failed_items': import_session.failed_items,
        'skipped_items': import_session.skipped_items,
        'last_updated': import_session.last_updated.isoformat() if import_session.last_updated else None,
        'error_message': import_session.error_message,
    }

    return JsonResponse(progress_data)


@login_required
def bulk_import_cancel(request, import_id):
    """
    Cancel an active import session.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        return JsonResponse({'error': 'User profile not found'}, status=403)

    try:
        import_session = BulkImportSession.objects.get(
            import_id=import_id,
            created_by=user_profile
        )
    except BulkImportSession.DoesNotExist:
        return JsonResponse({'error': 'Import session not found'}, status=404)

    if not import_session.can_cancel():
        return JsonResponse({'error': 'Import session cannot be cancelled'}, status=400)

    import_session.mark_cancelled()
    return JsonResponse({'success': True, 'message': 'Import cancelled successfully'})


@login_required
def bulk_import_results(request, import_id):
    """
    Display final import results.
    """
    user_profile = get_request_user_profile(request)
    if not user_profile:
        messages.error(request, "No user profile associated with your account. Please contact the administrator.")
        return redirect('process_management:bulk_import_dashboard')

    try:
        import_session = BulkImportSession.objects.get(
            import_id=import_id,
            created_by=user_profile
        )
    except BulkImportSession.DoesNotExist:
        messages.error(request, "Import session not found.")
        return redirect('process_management:bulk_import_dashboard')

    context = {
        'import_session': import_session,
        'import_results': import_session.import_results,
        'page_title': f'Import Results - {import_session.import_id}'
    }

    return render(request, 'process_management/bulk_import_results.html', context)


class BulkImportAnalyzer:
    """
    Helper class for analyzing what will be imported.
    """

    def __init__(self, import_session):
        self.session = import_session
        self.importer = ProcessMapImporter()

    def analyze(self):
        """
        Analyze the selected folders and return preview data.
        """
        selected_folder_ids = self.session.selected_folders
        if not selected_folder_ids:
            return {'error': 'No folders selected'}

        analysis_results = {
            'selected_folders': [],
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'estimated_processes': 0,
            'existing_processes': 0,
            'file_details': []
        }

        for folder_id in selected_folder_ids:
            try:
                folder = KnowledgeCentreFolder.objects.get(id=int(folder_id))
                folder_analysis = self._analyze_folder(folder)
                analysis_results['selected_folders'].append({
                    'id': folder.id,
                    'name': folder.name,
                    'files_count': folder_analysis['files_count'],
                    'valid_files': folder_analysis['valid_files'],
                    'invalid_files': folder_analysis['invalid_files']
                })
                analysis_results['total_files'] += folder_analysis['files_count']
                analysis_results['valid_files'] += folder_analysis['valid_files']
                analysis_results['invalid_files'] += folder_analysis['invalid_files']
                analysis_results['file_details'].extend(folder_analysis['file_details'])
            except (ValueError, KnowledgeCentreFolder.DoesNotExist):
                continue

        # Estimate processes (rough calculation)
        analysis_results['estimated_processes'] = analysis_results['valid_files']

        return analysis_results

    def _analyze_folder(self, folder):
        """
        Analyze a single folder and its contents.
        """
        # Get all files in this folder hierarchy
        folder_ids = []
        self._collect_folder_ids(folder, folder_ids)

        files = KnowldgeCentreFile.objects.filter(
            folder_id__in=folder_ids,
            archived=False
        ).select_related('folder')

        analysis = {
            'files_count': files.count(),
            'valid_files': 0,
            'invalid_files': 0,
            'file_details': []
        }

        for file in files:
            metadata = self.importer._parse_metadata(file.filename or file.name)
            is_valid = metadata is not None

            file_detail = {
                'id': file.id,
                'filename': file.filename or file.name,
                'folder': file.folder.name,
                'is_valid': is_valid,
                'parsed_process_name': metadata.process_name if metadata else None,
                'parsed_department': metadata.department_name if metadata else None,
                'parsed_region': metadata.region_name if metadata else None,
            }

            analysis['file_details'].append(file_detail)

            if is_valid:
                analysis['valid_files'] += 1
            else:
                analysis['invalid_files'] += 1

        return analysis

    def _collect_folder_ids(self, folder, folder_ids):
        """
        Recursively collect all folder IDs in the hierarchy.
        """
        folder_ids.append(folder.id)
        for subfolder in folder.subfolders.all():
            self._collect_folder_ids(subfolder, folder_ids)


def execute_bulk_import(import_session):
    """
    Execute the bulk import process for the given session.
    """
    from knowledge_center.models import KnowldgeCentreFile

    importer = ProcessMapImporter()
    selected_folder_ids = import_session.selected_folders

    # Get all files from selected folders
    folder_ids = set()
    for folder_id in selected_folder_ids:
        try:
            from knowledge_center.models import KnowledgeCentreFolder
            folder = KnowledgeCentreFolder.objects.get(id=int(folder_id))
            _collect_folder_ids_recursive(folder, folder_ids)
        except (ValueError, KnowledgeCentreFolder.DoesNotExist):
            continue

    files = KnowldgeCentreFile.objects.filter(
        folder_id__in=folder_ids,
        archived=False
    ).select_related('folder')

    # Process each file
    for file in files:
        try:
            result = importer.import_file(file)
            if result.get('status') == 'created':
                import_session.update_progress(successful=1, processed=1)
            elif result.get('status') == 'skipped':
                import_session.update_progress(skipped=1, processed=1)
            else:
                import_session.update_progress(failed=1, processed=1)
        except Exception as e:
            import_session.update_progress(failed=1, processed=1)
            # Log error but continue

    # Mark as completed
    import_session.mark_completed()


def _collect_folder_ids_recursive(folder, folder_ids):
    """
    Recursively collect all folder IDs in the hierarchy.
    """
    folder_ids.add(folder.id)
    for subfolder in folder.subfolders.all():
        _collect_folder_ids_recursive(subfolder, folder_ids)