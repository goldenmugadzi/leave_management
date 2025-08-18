"""
Optimized File Upload and Download Handlers for Direct Purchase
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
    """Optimized file handling without Base64 encoding - works with existing DirectPurchase models"""
    
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
            'uploaded_by': getattr(self.user, 'username', 'anonymous') if self.user else 'anonymous',
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
        """Save file with optimized approach (no Base64) - works with existing DirectPurchase models"""
        # Validate file
        self.validate_file(file)
        
        # Generate metadata
        metadata = self.generate_file_metadata(file)
        
        # Create directory structure for direct purchase
        year_month = datetime.now().strftime("%Y/%m")
        upload_path = f'direct_purchase/{year_month}'
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = hashlib.md5(f"{file.name}{timestamp}".encode()).hexdigest()[:8]
        filename = f"{timestamp}_{unique_id}_{file.name}"
        
        # Save file using Django's FileSystemStorage
        file_path = os.path.join(upload_path, filename)
        saved_path = self.fs.save(file_path, file)
        
        # Store metadata in cache for quick access
        cache_key = f"dp_file_metadata_{saved_path}"
        cache.set(cache_key, metadata, CACHE_TIMEOUT)
        
        return {
            'file_path': saved_path,
            'metadata': metadata,
            'download_url': f"/api/dp-files/download/{saved_path}/",
            'preview_url': f"/api/dp-files/preview/{saved_path}/"
        }
    
    def get_file_stream(self, file_path):
        """Get file stream for efficient download"""
        try:
            full_path = self.fs.path(file_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError("File not found")
            
            # Get metadata from cache
            cache_key = f"dp_file_metadata_{file_path}"
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

class OptimizedDirectPurchaseFileHandler:
    """Optimized file handling specifically for DirectPurchase models - no new tables needed"""
    
    def __init__(self, user):
        self.user = user
        self.file_handler = OptimizedFileHandler(user)
    
    def get_dp_file_metadata(self, dp_instance, file_field_name):
        """Get file metadata for DirectPurchase file fields (advert, bid_document, etc.)"""
        try:
            file_path = getattr(dp_instance, file_field_name, None)
            if not file_path or not os.path.exists(file_path):
                return None
            
            # Get file info
            file_info = self.file_handler.get_file_stream(file_path)
            
            return {
                'field_name': file_field_name,
                'name': os.path.basename(file_path),
                'size': file_info['metadata']['size'],
                'download_url': f"/api/dp-files/download/{file_path}/",
                'preview_url': f"/api/dp-files/preview/{file_path}/",
                'mime_type': file_info['metadata']['mime_type'],
                'uploaded_at': file_path.split('/')[-2] if '/' in file_path else None,
            }
            
        except Exception as e:
            logger.error(f"Error getting DP file metadata: {e}")
            return None
    
    def save_dp_file_optimized(self, file, dp_instance, field_name='advert'):
        """Save file for DirectPurchase instance with optimized approach"""
        try:
            # Save file using optimized handler
            file_info = self.file_handler.save_file_optimized(file, 'dp_' + field_name)
            
            # Update the model field (works with existing CharField for file paths)
            setattr(dp_instance, field_name, file_info['file_path'])
            dp_instance.save()
            
            return {
                'success': True,
                'file_path': file_info['file_path'],
                'metadata': file_info['metadata'],
                'download_url': file_info['download_url']
            }
            
        except Exception as e:
            logger.error(f"Error saving DP file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_advert_upload(self, file, dp_instance):
        """Handle advertisement file upload for DirectPurchase"""
        return self.save_dp_file_optimized(file, dp_instance, 'advert')
    
    def handle_bid_document_upload(self, file, dp_instance):
        """Handle bid document upload for DirectPurchase"""
        return self.save_dp_file_optimized(file, dp_instance, 'bid_document')
    
    def get_all_dp_files_metadata(self, dp_instance):
        """Get metadata for all file fields in a DirectPurchase instance"""
        file_fields = ['advert']  # Add other file fields as needed
        
        files_metadata = {}
        for field_name in file_fields:
            metadata = self.get_dp_file_metadata(dp_instance, field_name)
            if metadata:
                files_metadata[field_name] = metadata
        
        return files_metadata

# API Views for optimized file handling - works with existing DirectPurchase models
@login_required
@require_http_methods(["POST"])
def api_upload_dp_file_optimized(request):
    """Optimized file upload for DirectPurchase without Base64 encoding"""
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
def api_download_dp_file(request, file_path):
    """Download DirectPurchase file with streaming response"""
    try:
        file_handler = OptimizedFileHandler(request.user)
        file_info = file_handler.get_file_stream(file_path)
        
        # Create streaming response
        response = StreamingHttpResponse(
            file_info['stream'],
            content_type=file_info['metadata']['mime_type']
        )
        
        # Set headers for download
        response['Content-Disposition'] = f'attachment; filename="{file_info["metadata"]["original_name"]}"'
        response['Content-Length'] = file_info['metadata']['size']
        
        return response
        
    except FileNotFoundError:
        return JsonResponse({"error": "File not found"}, status=404)
    except Exception as e:
        logger.error(f"File download error: {e}")
        return JsonResponse({"error": "File download failed"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_preview_dp_file(request, file_path):
    """Preview DirectPurchase file content"""
    try:
        file_handler = OptimizedFileHandler(request.user)
        preview_data = file_handler.get_file_preview(file_path)
        
        if preview_data is None:
            return JsonResponse({"error": "Preview not available for this file type"}, status=400)
        
        return JsonResponse({
            "success": True,
            "preview": preview_data,
            "preview_type": 'base64' if isinstance(preview_data, str) else 'text'
        })
        
    except Exception as e:
        logger.error(f"File preview error: {e}")
        return JsonResponse({"error": "File preview failed"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_get_dp_file_metadata(request, file_path):
    """Get DirectPurchase file metadata"""
    try:
        file_handler = OptimizedFileHandler(request.user)
        file_info = file_handler.get_file_stream(file_path)
        
        return JsonResponse({
            "success": True,
            "metadata": file_info['metadata'],
            "download_url": f"/api/dp-files/download/{file_path}/",
            "preview_url": f"/api/dp-files/preview/{file_path}/"
        })
        
    except FileNotFoundError:
        return JsonResponse({"error": "File not found"}, status=404)
    except Exception as e:
        logger.error(f"File metadata error: {e}")
        return JsonResponse({"error": "Failed to get file metadata"}, status=500)

# Utility functions for backward compatibility
def get_dp_file_download_url(file_path):
    """Get download URL for DirectPurchase file"""
    if not file_path:
        return None
    return f"/api/dp-files/download/{file_path}/"

def get_dp_file_preview_url(file_path):
    """Get preview URL for DirectPurchase file"""
    if not file_path:
        return None
    return f"/api/dp-files/preview/{file_path}/"

def validate_dp_file(file):
    """Validate DirectPurchase file"""
    try:
        file_handler = OptimizedFileHandler(None)  # No user needed for validation
        file_handler.validate_file(file)
        return True
    except ValidationError:
        return False

def get_dp_file_size(file_path):
    """Get file size for DirectPurchase file"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    except Exception:
        return 0
