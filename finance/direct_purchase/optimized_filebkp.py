"""
URL Configuration for Optimized File Handlers in Direct Purchase
Provides endpoints for file upload, download, preview, and metadata retrieval
"""

from django.urls import path
from .optimized_file_handlers import (
    api_upload_dp_file_optimized,
    api_download_dp_file,
    api_preview_dp_file,
    api_get_dp_file_metadata
)

app_name = 'dp_files'

urlpatterns = [
    # File upload endpoint
    path('upload/', api_upload_dp_file_optimized, name='upload_file'),
    
    # File download endpoint (with file path)
    path('download/<path:file_path>/', api_download_dp_file, name='download_file'),
    
    # File preview endpoint (with file path)
    path('preview/<path:file_path>/', api_preview_dp_file, name='preview_file'),
    
    # File metadata endpoint (with file path)
    path('metadata/<path:file_path>/', api_get_dp_file_metadata, name='file_metadata'),
]
