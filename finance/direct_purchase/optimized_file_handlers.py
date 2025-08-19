"""
Optimized File Upload and Download Handlers
Replaces Base64 encoding with efficient streaming and metadata-based approaches
Works with existing models - no new tables or columns needed
"""

import os
import hashlib
import json
import logging
import mimetypes
from datetime import datetime
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction

logger = logging.getLogger(__name__)

# File handling constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_REQUEST = 10
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif',
    'zip', 'rar', 'txt', 'csv', 'ppt', 'pptx'
}
CACHE_TIMEOUT = 300  # 5 minutes

class OptimizedFileHandler:
    """Optimized file handling without Base64 encoding - works with existing models"""
    
    def __init__(self, user):
        self.user = user
        self.fs = FileSystemStorage()
    
    def validate_file(self, file):
        """Validate file size, type, and content"""
        # Size validation
        if file.size > MAX_FILE_SIZE:
            raise ValidationError(f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Extension validation
        ext = os.path.splitext(file.name)[1].lower()[1:]
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"File type '{ext}' not allowed")
        
        return True
    
    def generate_file_metadata(self, file):
        """Generate comprehensive file metadata"""
        import magic
        
        # Basic metadata
        metadata = {
            'original_name': file.name,
            'size': file.size,
            'extension': os.path.splitext(file.name)[1].lower(),
            'uploaded_by': self.user.username,
            'uploaded_at': datetime.now().isoformat(),
        }
        
        # MIME type detection
        try:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # Reset file pointer
            metadata['mime_type'] = mime_type
        except Exception as e:
            logger.warning(f"MIME type detection failed: {e}")
            metadata['mime_type'] = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        
        # Calculate checksum
        try:
            hash_md5 = hashlib.md5()
            for chunk in file.chunks():
                hash_md5.update(chunk)
            metadata['checksum'] = hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Checksum calculation failed: {e}")
            metadata['checksum'] = None
        
        return metadata
    
    def save_file_optimized(self, file, file_type='general', description=None):
        """Save file with optimized approach (no Base64) - works with existing models"""
        # Validate file
        self.validate_file(file)
        
        # Generate metadata
        metadata = self.generate_file_metadata(file)
        
        # Create directory structure (use BASE_DIR since files are not in MEDIA_ROOT)
        upload_path = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
        os.makedirs(upload_path, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = hashlib.md5(f"{file.name}{timestamp}".encode()).hexdigest()[:8]
        filename = f"{timestamp}_{unique_id}_{file.name}"
        
        # Save file directly (not using FileSystemStorage since it's outside MEDIA_ROOT)
        file_path = os.path.join(upload_path, filename)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Store relative path for database consistency
        relative_file_path = os.path.join('uploads', 'comparative', 'adverts', filename)
        
        # Store metadata in cache for quick access
        cache_key = f"file_metadata_{relative_file_path}"
        cache.set(cache_key, metadata, CACHE_TIMEOUT)
        
        return {
            'file_path': relative_file_path,
            'metadata': metadata,
            'download_url': f"/api/cs-files/download/{relative_file_path}/",
            'preview_url': f"/api/cs-files/preview/{relative_file_path}/"
        }
    
    def get_file_stream(self, file_path):
        """Get file stream for efficient download"""
        try:
            full_path = self.fs.path(file_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError("File not found")
            
            # Get metadata from cache
            cache_key = f"file_metadata_{file_path}"
            metadata = cache.get(cache_key)
            
            if not metadata:
                # Reconstruct metadata if not in cache
                metadata = {
                    'original_name': os.path.basename(file_path),
                    'size': os.path.getsize(full_path),
                    'mime_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                }
            
            return {
                'file_path': full_path,
                'metadata': metadata,
                'stream': open(full_path, 'rb')
            }
            
        except Exception as e:
            logger.error(f"Error getting file stream: {e}")
            raise
    
    def get_file_preview(self, file_path, max_size=1024*1024):  # 1MB limit for preview
        """Get file preview for supported types"""
        try:
            file_info = self.get_file_stream(file_path)
            
            # Only preview small files
            if file_info['metadata']['size'] > max_size:
                return None
            
            mime_type = file_info['metadata']['mime_type']
            
            if mime_type.startswith('image/'):
                # Return image data for preview
                with open(file_info['file_path'], 'rb') as f:
                    import base64
                    return base64.b64encode(f.read()).decode('utf-8')
            
            elif mime_type == 'text/plain' or mime_type == 'text/csv':
                # Return text content for preview
                with open(file_info['file_path'], 'r', encoding='utf-8') as f:
                    content = f.read(5000)  # First 5000 characters
                    return content
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file preview: {e}")
            return None

class OptimizedAttachmentHandler:
    """Optimized attachment handling for existing models - no new tables needed"""
    
    def __init__(self, user):
        self.user = user
        self.file_handler = OptimizedFileHandler(user)
    
    def get_attachments_metadata(self, attachments, include_preview=False):
        """Get attachment metadata without Base64 encoding - works with existing Attachment model"""
        attachments_data = []
        
        for attachment in attachments:
            try:
                if not attachment.file or not os.path.exists(attachment.file.path):
                    continue
                
                # Basic metadata using existing model fields
                attachment_info = {
                    'id': attachment.id,
                    'name': os.path.basename(attachment.file.name),
                    'size': attachment.file.size,
                    'url': attachment.file.url,
                    'download_url': f"/api/cs-attachments/{attachment.id}/download/",
                    'uploaded_at': attachment.file.name.split('/')[-2] if '/' in attachment.file.name else None,
                }
                
                # Add preview if requested and file is small
                if include_preview and attachment.file.size < 1024 * 1024:  # 1MB
                    preview_data = self.file_handler.get_file_preview(attachment.file.name)
                    if preview_data:
                        attachment_info['preview'] = preview_data
                        attachment_info['preview_type'] = 'base64' if isinstance(preview_data, str) else 'text'
                
                attachments_data.append(attachment_info)
                
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.id}: {e}")
                continue
        
        return attachments_data
    
    def save_attachment_optimized(self, file, related_object, field_name='file'):
        """Save attachment with optimized approach - works with existing model fields"""
        try:
            # Save file using optimized handler
            file_info = self.file_handler.save_file_optimized(file)
            
            # Update the model field (works with existing CharField for file paths)
            setattr(related_object, field_name, file_info['file_path'])
            related_object.save()
            
            return {
                'success': True,
                'file_path': file_info['file_path'],
                'metadata': file_info['metadata'],
                'download_url': file_info['download_url']
            }
            
        except Exception as e:
            logger.error(f"Error saving attachment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_cs_file_metadata(self, cs_instance, file_field_name):
        """Get file metadata for ComparativeSchedules file fields (advert, bid_document, etc.)"""
        try:
            file_path = getattr(cs_instance, file_field_name, None)
            if not file_path or not os.path.exists(file_path):
                return None
            
            # Get file info
            file_info = self.file_handler.get_file_stream(file_path)
            
            return {
                'field_name': file_field_name,
                'name': os.path.basename(file_path),
                'size': file_info['metadata']['size'],
                'download_url': f"/api/cs-files/download/{file_path}/",
                'preview_url': f"/api/cs-files/preview/{file_path}/",
                'mime_type': file_info['metadata']['mime_type'],
                'uploaded_at': file_path.split('/')[-2] if '/' in file_path else None,
            }
            
        except Exception as e:
            logger.error(f"Error getting CS file metadata: {e}")
            return None

# API Views for optimized file handling - works with existing models
@login_required
@require_http_methods(["POST"])
def api_upload_file_optimized(request):
    """Optimized file upload without Base64 encoding - works with existing models"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)
        
        file = request.FILES['file']
        file_type = request.POST.get('file_type', 'general')
        description = request.POST.get('description', '')
        
        # Initialize handler
        file_handler = OptimizedFileHandler(request.user)
        
        # Save file
        result = file_handler.save_file_optimized(file, file_type, description)
        
        return JsonResponse({
            "success": True,
            "file_path": result['file_path'],
            "metadata": result['metadata'],
            "download_url": result['download_url'],
            "preview_url": result['preview_url']
        })
        
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return JsonResponse({"error": "File upload failed"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_download_file_optimized(request, file_path):
    """Optimized file download with streaming - works with existing file paths"""
    try:
        file_handler = OptimizedFileHandler(request.user)
        file_info = file_handler.get_file_stream(file_path)
        
        # Create streaming response
        response = StreamingHttpResponse(
            file_info['stream'],
            content_type=file_info['metadata']['mime_type']
        )
        response['Content-Disposition'] = f'attachment; filename="{file_info["metadata"]["original_name"]}"'
        response['Content-Length'] = file_info['metadata']['size']
        
        # Add caching headers
        response['Cache-Control'] = 'public, max-age=3600'  # 1 hour cache
        response['ETag'] = f'"{file_info["metadata"]["checksum"]}"'
        
        return response
        
    except FileNotFoundError:
        return JsonResponse({"error": "File not found"}, status=404)
    except Exception as e:
        logger.error(f"File download error: {e}")
        return JsonResponse({"error": "File download failed"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_preview_file_optimized(request, file_path):
    """File preview without Base64 for large files - works with existing file paths"""
    try:
        file_handler = OptimizedFileHandler(request.user)
        preview_data = file_handler.get_file_preview(file_path)
        
        if preview_data:
            return JsonResponse({
                "success": True,
                "preview": preview_data,
                "preview_type": "base64" if isinstance(preview_data, str) else "text"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Preview not available for this file type or size"
            })
            
    except Exception as e:
        logger.error(f"File preview error: {e}")
        return JsonResponse({"error": "File preview failed"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_get_attachments_optimized(request, pr_id):
    """Get PR attachments without Base64 encoding - uses existing Attachment model"""
    try:
        from finance.purchase_request.models import PurchaseRequest, Attachment
        
        if not pr_id.startswith("PR"):
            pr_id = "PR" + pr_id
        
        purchase_request = PurchaseRequest.objects.prefetch_related('attachment_set').get(id=pr_id)
        
        # Initialize handler
        attachment_handler = OptimizedAttachmentHandler(request.user)
        
        # Get attachments with metadata only
        include_preview = request.GET.get('include_preview', 'false').lower() == 'true'
        attachments_data = attachment_handler.get_attachments_metadata(
            purchase_request.attachment_set.all(),
            include_preview=include_preview
        )
        
        return JsonResponse({
            "success": True,
            "pr_attachments": attachments_data,
            "total_count": len(attachments_data)
        })
        
    except PurchaseRequest.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        })
    except Exception as e:
        logger.error(f"Get attachments error: {e}")
        return JsonResponse({"error": "Failed to get attachments"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_get_create_data_optimized(request, pr_id):
    """Optimized get_create_data without Base64 encoding - uses existing models"""
    try:
        from finance.purchase_request.models import PurchaseRequest, Attachment, PrItem, UnitOfMeasurement
        from finance.comparative_schedules.models import ProcPlan, Currency, Supplier
        from it.users.models import UserProfile
        
        # check is pr_id started with PR or not
        if not pr_id.startswith("PR"):
            pr_id = "PR" + pr_id
        
        purchase_request = PurchaseRequest.objects.filter(id=pr_id).first()
        if not purchase_request:
            return JsonResponse({
                "success": False,
                "message": "PR not found",
            })
        
        request_user = request.user
        request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
        user_comparative_schedule_role = request_user_profile.get_user_role_for_application('comparative_schedule')
        
        # Get reference data with caching
        proc_plans = cache.get('all_proc_plans')
        if proc_plans is None:
            proc_plans = list(ProcPlan.objects.values('id', 'proc_ref', 'description'))
            cache.set('all_proc_plans', proc_plans, CACHE_TIMEOUT * 4)
        
        currencies = cache.get('all_currencies')
        if currencies is None:
            currencies = list(Currency.objects.values('id', 'currency'))
            cache.set('all_currencies', currencies, CACHE_TIMEOUT * 4)
        
        suppliers = cache.get('all_suppliers')
        if suppliers is None:
            suppliers = list(Supplier.objects.values('id', 'name'))
            cache.set('all_suppliers', suppliers, CACHE_TIMEOUT * 2)
        
        users = cache.get('all_users')
        if users is None:
            users = list(UserProfile.objects.values('id', 'username', 'first_name', 'last_name'))
            cache.set('all_users', users, CACHE_TIMEOUT)
        
        uom = cache.get('all_uom')
        if uom is None:
            uom = list(UnitOfMeasurement.objects.values('unit', 'name'))
            cache.set('all_uom', uom, CACHE_TIMEOUT * 4)
        
        # Get PR items
        pr_items = PrItem.objects.filter(purchase_request=purchase_request, ordered=False).all()
        pr_item_list = []
        for pr_item in pr_items:
            pr_item_list.append({
                "id": pr_item.id,
                "item_required": pr_item.item_required,
                "quantity": pr_item.quantity,
                "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
                "ordered": pr_item.ordered,
            })
        
        # Get attachments without Base64 encoding - uses existing Attachment model
        attachment_handler = OptimizedAttachmentHandler(request.user)
        pr_attachments = Attachment.objects.filter(purchase_request=purchase_request).all()
        pr_at_list = attachment_handler.get_attachments_metadata(pr_attachments)
        
        return JsonResponse({
            "success": True,
            "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
            "message": "PR details retrieved successfully",
            "pr_id": pr_id,
            "scope_of_work": purchase_request.scope_of_work if purchase_request.scope_of_work else "",
            "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
            "proc_plan": {
                "id": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                "description": purchase_request.procurement_plan_reference.name if purchase_request.procurement_plan_reference else "",
            } if purchase_request.procurement_plan_reference else {},
            "pr_date": purchase_request.created_at.strftime("%Y-%m-%d") if purchase_request.created_at else "",
            "pr_items": pr_item_list,
            "pr_attachments": pr_at_list,
            "proc_plans": proc_plans,
            "uom": uom,
            "currencies": currencies,
            "suppliers": suppliers,
            "users": users,
        }, safe=False)
        
    except Exception as e:
        logger.error(f"Get create data error: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_get_cs_files_optimized(request, cs_id):
    """Get Comparative Schedule files without Base64 encoding - uses existing file fields"""
    try:
        from finance.comparative_schedules.models import ComparativeSchedules, Bids
        
        cs = ComparativeSchedules.objects.get(cs_id=cs_id)
        attachment_handler = OptimizedAttachmentHandler(request.user)
        
        # Get files from existing model fields
        cs_files = []
        
        # Check advert field
        if cs.advert:
            advert_metadata = attachment_handler.get_cs_file_metadata(cs, 'advert')
            if advert_metadata:
                cs_files.append(advert_metadata)
        
        # Get bid documents from Bids model
        bids = Bids.objects.filter(cs_id=cs)
        for bid in bids:
            if bid.bid_document:
                bid_metadata = attachment_handler.get_cs_file_metadata(bid, 'bid_document')
                if bid_metadata:
                    bid_metadata['bid_id'] = bid.id
                    bid_metadata['supplier'] = bid.sup_id.name if bid.sup_id else None
                    cs_files.append(bid_metadata)
        
        return JsonResponse({
            "success": True,
            "cs_files": cs_files,
            "total_count": len(cs_files)
        })
        
    except ComparativeSchedules.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Comparative Schedule not found",
        })
    except Exception as e:
        logger.error(f"Get CS files error: {e}")
        return JsonResponse({"error": "Failed to get CS files"}, status=500)

@login_required
@require_http_methods(["DELETE"])
def api_delete_file_optimized(request, file_path):
    """Delete file with cleanup - works with existing file paths"""
    try:
        file_handler = OptimizedFileHandler(request.user)
        full_path = file_handler.fs.path(file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            
            # Remove metadata from cache
            cache_key = f"file_metadata_{file_path}"
            cache.delete(cache_key)
            
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "File not found"}, status=404)
            
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return JsonResponse({"error": "File deletion failed"}, status=500)

# Utility functions for migration from Base64
def migrate_base64_to_optimized():
    """Migration utility to convert Base64-based responses to optimized format"""
    # This function can be used to update existing endpoints
    pass

def get_file_statistics():
    """Get file usage statistics - works with existing file structure"""
    try:
        upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_files += 1
                total_size += os.path.getsize(file_path)
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'average_size_mb': (total_size / total_files) / (1024 * 1024) if total_files > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting file statistics: {e}")
        return None
