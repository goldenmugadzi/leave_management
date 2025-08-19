"""
URL patterns for optimized file handling endpoints
Replaces Base64 encoding with efficient streaming and metadata-based approaches
Works with existing models - no new tables or columns needed
"""

from django.urls import path
from .optimized_file_handlers import (
    api_upload_file_optimized,
    api_download_file_optimized,
    api_preview_file_optimized,
    api_get_attachments_optimized,
    api_get_create_data_optimized,
    api_get_cs_files_optimized,
    api_delete_file_optimized,
)

# URL patterns for optimized file handling
urlpatterns = [
    # File upload and download
    path('upload/', api_upload_file_optimized, name='api_upload_file_optimized'),
    path('download/<path:file_path>/', api_download_file_optimized, name='api_download_file_optimized'),
    path('preview/<path:file_path>/', api_preview_file_optimized, name='api_preview_file_optimized'),
    path('delete/<path:file_path>/', api_delete_file_optimized, name='api_delete_file_optimized'),
    
    # Attachment handling
    path('attachments/<str:pr_id>/', api_get_attachments_optimized, name='api_get_attachments_optimized'),
    path('create-data/<str:pr_id>/', api_get_create_data_optimized, name='api_get_create_data_optimized'),
    
    # Comparative Schedule files (works with existing model fields)
    path('cs-files/<str:cs_id>/', api_get_cs_files_optimized, name='api_get_cs_files_optimized'),
]
