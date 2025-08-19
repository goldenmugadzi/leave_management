"""
Enhanced File Management for Comparative Schedules
Addresses security, performance, and user experience issues
"""

import os
import uuid
import hashlib
import json
import base64
import zipfile
import tempfile
import magic
import logging
from datetime import datetime
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)

class ComparativeScheduleAttachment(models.Model):
    """Enhanced attachment model with comprehensive metadata and security"""
    
    ATTACHMENT_TYPES = [
        ('advert', 'Advertisement'),
        ('bid', 'Bid Document'),
        ('compliance', 'Compliance Document'),
        ('committee', 'Committee Document'),
        ('general', 'General Document'),
        ('specification', 'Technical Specification'),
        ('drawing', 'Drawing/Diagram'),
        ('photo', 'Photograph'),
        ('contract', 'Contract Document'),
    ]
    
    # Core fields
    cs = models.ForeignKey('ComparativeSchedules', on_delete=models.CASCADE, related_name='attachments')
    file = models.CharField(max_length=500)  # Store file path as string since files are in BASE_DIR/uploads
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='general')
    
    # Metadata fields
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey('it.users.UserProfile', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    checksum = models.CharField(max_length=64)  # SHA-256
    
    # Additional metadata
    description = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    is_compressed = models.BooleanField(default=False)
    thumbnail_path = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['cs', 'file_type']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
            models.Index(fields=['mime_type']),
            models.Index(fields=['is_public']),
        ]
        verbose_name = "Comparative Schedule Attachment"
        verbose_name_plural = "Comparative Schedule Attachments"
    
    def __str__(self):
        return f"{self.original_filename} ({self.cs.cs_id})"
    
    def save(self, *args, **kwargs):
        """Override save to calculate metadata automatically"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        if self.file and not self.checksum:
            self.checksum = self._calculate_checksum()
        
        if self.file and not self.mime_type:
            self.mime_type = self._detect_mime_type()
        
        super().save(*args, **kwargs)
    
    def _calculate_checksum(self):
        """Calculate SHA-256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        for chunk in self.file.chunks():
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _detect_mime_type(self):
        """Detect MIME type using python-magic"""
        try:
            with open(self.file.path, 'rb') as f:
                return magic.from_buffer(f.read(1024), mime=True)
        except Exception as e:
            logger.error(f"Error detecting MIME type: {e}")
            return 'application/octet-stream'
    
    def get_file_url(self):
        """Get secure file URL"""
        return f"/api/cs-attachments/{self.id}/download/"
    
    def get_preview_url(self):
        """Get file preview URL if available"""
        if self.thumbnail_path:
            return f"/api/cs-attachments/{self.id}/preview/"
        return None
    
    def can_access(self, user):
        """Check if user can access this file"""
        # Creator can always access
        if self.uploaded_by == user:
            return True
        
        # CS creator can access
        if self.cs.created_by == user:
            return True
        
        # Public files can be accessed by anyone
        if self.is_public:
            return True
        
        # Check role-based permissions
        user_role = user.get_user_role_for_application('comparative_schedules')
        if user_role and user_role.role in ['finance_manager', 'general_manager']:
            return True
        
        return False

class SecureFileUploadService:
    """Secure file upload with comprehensive validation and processing"""
    
    ALLOWED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        'txt': 'text/plain',
        'csv': 'text/csv',
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_FILES_PER_CS = 20  # Maximum files per comparative schedule
    
    def __init__(self, user):
        self.user = user
    
    def validate_file(self, file):
        """Comprehensive file validation"""
        # Size validation
        if file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large. Maximum size is {self.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Extension validation
        ext = os.path.splitext(file.name)[1].lower()[1:]
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(f"File type '{ext}' not allowed")
        
        # MIME type validation
        try:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # Reset file pointer
            
            if mime_type != self.ALLOWED_EXTENSIONS[ext]:
                raise ValidationError(f"File content doesn't match extension")
        except Exception as e:
            logger.warning(f"MIME type validation failed: {e}")
            # Continue without MIME validation if magic is not available
        
        return True
    
    def validate_file_count(self, cs_id):
        """Validate maximum files per CS"""
        current_count = ComparativeScheduleAttachment.objects.filter(cs_id=cs_id).count()
        if current_count >= self.MAX_FILES_PER_CS:
            raise ValidationError(f"Maximum {self.MAX_FILES_PER_CS} files allowed per schedule")
    
    def process_file(self, file, file_type, cs_id, description=None, tags=None):
        """Process and save file securely"""
        # Validate file
        self.validate_file(file)
        self.validate_file_count(cs_id)
        
        # Generate secure filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(file.name)[1].lower()
        filename = f"{timestamp}_{unique_id}{ext}"
        
        # Create directory structure (use BASE_DIR since files are not in MEDIA_ROOT)
        upload_path = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, filename)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Store relative path in database for consistency with existing models
        relative_file_path = os.path.join('uploads', 'comparative', 'adverts', filename)
        
        # Create attachment record
        attachment = ComparativeScheduleAttachment.objects.create(
            cs_id=cs_id,
            file=relative_file_path,
            original_filename=file.name,
            file_type=file_type,
            file_size=file.size,
            description=description,
            tags=tags or [],
            uploaded_by=self.user,
        )
        
        # Process file (compression, thumbnails, etc.)
        self._post_process_file(attachment)
        
        return attachment
    
    def _post_process_file(self, attachment):
        """Post-process file (compression, thumbnails)"""
        try:
            # Create thumbnail for images
            if attachment.mime_type.startswith('image/'):
                thumbnail_path = self._create_thumbnail(attachment.file.path)
                if thumbnail_path:
                    attachment.thumbnail_path = thumbnail_path
            
            # Compress large images
            if attachment.mime_type.startswith('image/') and attachment.file_size > 1024 * 1024:  # 1MB
                if self._compress_image(attachment.file.path):
                    attachment.is_compressed = True
            
            attachment.save()
            
        except Exception as e:
            logger.error(f"Error in post-processing file {attachment.id}: {e}")
    
    def _create_thumbnail(self, file_path, size=(200, 200)):
        """Create thumbnail for images"""
        try:
            from PIL import Image
            
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                with Image.open(file_path) as img:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    thumbnail_path = file_path.replace('.', '_thumb.')
                    img.save(thumbnail_path, 'JPEG', quality=85)
                    return thumbnail_path
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
        
        return None
    
    def _compress_image(self, file_path, quality=85):
        """Compress image file"""
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                
                # Compress and save
                compressed_path = file_path.replace('.', '_compressed.')
                img.save(compressed_path, 'JPEG', quality=quality, optimize=True)
                
                # Replace original if compression was successful
                original_size = os.path.getsize(file_path)
                compressed_size = os.path.getsize(compressed_path)
                
                if compressed_size < original_size:
                    os.replace(compressed_path, file_path)
                    return True
        except Exception as e:
            logger.error(f"Error compressing image: {e}")
        
        return False

class OptimizedFileDownloadService:
    """Optimized file download with streaming and caching"""
    
    def __init__(self, user):
        self.user = user
    
    def get_file_stream(self, attachment_id):
        """Get file stream for download"""
        try:
            attachment = ComparativeScheduleAttachment.objects.select_related('cs').get(id=attachment_id)
            
            # Check permissions
            if not attachment.can_access(self.user):
                raise PermissionError("Access denied")
            
            # Check if file exists
            if not os.path.exists(attachment.file.path):
                raise FileNotFoundError("File not found")
            
            return {
                'file_path': attachment.file.path,
                'filename': attachment.original_filename,
                'mime_type': attachment.mime_type,
                'file_size': attachment.file_size,
                'stream': open(attachment.file.path, 'rb')
            }
            
        except ComparativeScheduleAttachment.DoesNotExist:
            raise FileNotFoundError("Attachment not found")
    
    def get_file_preview(self, attachment_id):
        """Get file preview for supported types"""
        try:
            attachment = ComparativeScheduleAttachment.objects.get(id=attachment_id)
            
            if not attachment.can_access(self.user):
                raise PermissionError("Access denied")
            
            if attachment.mime_type.startswith('image/'):
                # Return image data for preview
                with open(attachment.file.path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            
            elif attachment.mime_type == 'application/pdf':
                # Return PDF preview (first page)
                # This would require additional PDF processing library
                pass
            
            return None
            
        except ComparativeScheduleAttachment.DoesNotExist:
            raise FileNotFoundError("Attachment not found")
    
    def create_download_response(self, attachment_id):
        """Create HTTP response for file download"""
        try:
            file_info = self.get_file_stream(attachment_id)
            
            response = HttpResponse(
                file_info['stream'],
                content_type=file_info['mime_type']
            )
            response['Content-Disposition'] = f'attachment; filename="{file_info["filename"]}"'
            response['Content-Length'] = file_info['file_size']
            
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)

class FileSearchService:
    """File search and indexing service"""
    
    def search_files(self, query, cs_id=None, file_type=None, user=None, limit=50):
        """Search files by various criteria"""
        from django.db.models import Q
        
        queryset = ComparativeScheduleAttachment.objects.all()
        
        # Filter by CS if specified
        if cs_id:
            queryset = queryset.filter(cs_id=cs_id)
        
        # Filter by file type
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        # Filter by user permissions
        if user:
            queryset = queryset.filter(
                Q(uploaded_by=user) | 
                Q(cs__created_by=user) |
                Q(is_public=True)
            )
        
        # Search in filename and metadata
        if query:
            queryset = queryset.filter(
                Q(original_filename__icontains=query) |
                Q(cs__cs_id__icontains=query) |
                Q(uploaded_by__username__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__contains=[query])
            )
        
        return queryset.order_by('-uploaded_at')[:limit]
    
    def get_file_statistics(self, cs_id=None, user=None):
        """Get file statistics"""
        queryset = ComparativeScheduleAttachment.objects
        
        if cs_id:
            queryset = queryset.filter(cs_id=cs_id)
        
        if user:
            queryset = queryset.filter(
                models.Q(uploaded_by=user) | 
                models.Q(cs__created_by=user) |
                models.Q(is_public=True)
            )
        
        stats = queryset.aggregate(
            total_files=models.Count('id'),
            total_size=models.Sum('file_size'),
            avg_size=models.Avg('file_size'),
            file_types=models.Count('file_type', distinct=True)
        )
        
        # Add file type breakdown
        type_breakdown = queryset.values('file_type').annotate(
            count=models.Count('id'),
            total_size=models.Sum('file_size')
        )
        
        stats['type_breakdown'] = list(type_breakdown)
        
        return stats

class BulkFileOperationService:
    """Bulk file operations service"""
    
    def __init__(self, user):
        self.user = user
    
    def bulk_upload(self, files, cs_id, file_type='general', descriptions=None):
        """Bulk upload multiple files"""
        results = []
        upload_service = SecureFileUploadService(self.user)
        
        for i, file in enumerate(files):
            try:
                description = descriptions[i] if descriptions and i < len(descriptions) else None
                attachment = upload_service.process_file(file, file_type, cs_id, description)
                results.append({
                    'success': True,
                    'filename': file.name,
                    'attachment_id': attachment.id,
                    'file_size': attachment.file_size
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'filename': file.name,
                    'error': str(e)
                })
        
        return results
    
    def bulk_download(self, attachment_ids):
        """Create zip file for bulk download"""
        import tempfile
        
        # Validate permissions
        attachments = ComparativeScheduleAttachment.objects.filter(id__in=attachment_ids)
        accessible_attachments = [
            att for att in attachments 
            if att.can_access(self.user)
        ]
        
        if not accessible_attachments:
            raise ValueError("No accessible files found")
        
        # Create temporary zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                for attachment in accessible_attachments:
                    if os.path.exists(attachment.file.path):
                        zip_file.write(
                            attachment.file.path,
                            attachment.original_filename
                        )
            
            return tmp_file.name

# API Views
@login_required
@require_http_methods(["POST"])
def api_upload_attachment(request):
    """Enhanced file upload API"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)
        
        file = request.FILES['file']
        cs_id = request.POST.get('cs_id')
        file_type = request.POST.get('file_type', 'general')
        description = request.POST.get('description', '')
        tags = json.loads(request.POST.get('tags', '[]'))
        
        if not cs_id:
            return JsonResponse({"error": "CS ID required"}, status=400)
        
        # Process file
        upload_service = SecureFileUploadService(request.user)
        attachment = upload_service.process_file(
            file, file_type, cs_id, description, tags
        )
        
        return JsonResponse({
            "success": True,
            "attachment_id": attachment.id,
            "filename": attachment.original_filename,
            "file_size": attachment.file_size,
            "mime_type": attachment.mime_type,
            "preview_url": attachment.get_preview_url(),
            "download_url": attachment.get_file_url()
        })
        
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return JsonResponse({"error": "File upload failed"}, status=500)

@login_required
@require_http_methods(["GET"])
def api_download_attachment(request, attachment_id):
    """Enhanced file download API"""
    try:
        download_service = OptimizedFileDownloadService(request.user)
        return download_service.create_download_response(attachment_id)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)

@login_required
@require_http_methods(["GET"])
def api_preview_attachment(request, attachment_id):
    """File preview API"""
    try:
        download_service = OptimizedFileDownloadService(request.user)
        preview_data = download_service.get_file_preview(attachment_id)
        
        if preview_data:
            return JsonResponse({
                "success": True,
                "preview_data": preview_data
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Preview not available for this file type"
            })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)

@login_required
@require_http_methods(["GET"])
def api_search_attachments(request):
    """File search API"""
    try:
        query = request.GET.get('query', '')
        cs_id = request.GET.get('cs_id')
        file_type = request.GET.get('file_type')
        limit = int(request.GET.get('limit', 50))
        
        search_service = FileSearchService()
        results = search_service.search_files(
            query, cs_id, file_type, request.user, limit
        )
        
        attachments_data = []
        for attachment in results:
            attachments_data.append({
                'id': attachment.id,
                'filename': attachment.original_filename,
                'file_type': attachment.file_type,
                'file_size': attachment.file_size,
                'mime_type': attachment.mime_type,
                'uploaded_at': attachment.uploaded_at.isoformat(),
                'uploaded_by': attachment.uploaded_by.username,
                'description': attachment.description,
                'tags': attachment.tags,
                'preview_url': attachment.get_preview_url(),
                'download_url': attachment.get_file_url()
            })
        
        return JsonResponse({
            "success": True,
            "attachments": attachments_data,
            "total": len(attachments_data)
        })
        
    except Exception as e:
        logger.error(f"File search error: {e}")
        return JsonResponse({"error": "Search failed"}, status=500)

@login_required
@require_http_methods(["DELETE"])
def api_delete_attachment(request, attachment_id):
    """Delete attachment API"""
    try:
        attachment = ComparativeScheduleAttachment.objects.get(id=attachment_id)
        
        # Check permissions
        if not attachment.can_access(request.user):
            return JsonResponse({"error": "Access denied"}, status=403)
        
        # Delete file from filesystem
        if os.path.exists(attachment.file.path):
            os.remove(attachment.file.path)
        
        # Delete thumbnail if exists
        if attachment.thumbnail_path and os.path.exists(attachment.thumbnail_path):
            os.remove(attachment.thumbnail_path)
        
        # Delete database record
        attachment.delete()
        
        return JsonResponse({"success": True})
        
    except ComparativeScheduleAttachment.DoesNotExist:
        return JsonResponse({"error": "Attachment not found"}, status=404)
    except Exception as e:
        logger.error(f"Delete attachment error: {e}")
        return JsonResponse({"error": "Delete failed"}, status=500)
