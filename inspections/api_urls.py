"""
API URL Configuration for Inspections App
Routes for mobile application API endpoints
"""

from django.urls import path
from . import api_views, sync_views

app_name = 'inspections_api'

urlpatterns = [
    # Application API endpoints
    path('v1/applications/assigned/', api_views.assigned_applications, name='assigned_applications'),
    path('v1/applications/<uuid:pk>/', api_views.application_detail, name='application_detail'),
    path('v1/applications/<uuid:pk>/accept/', api_views.accept_assignment, name='accept_assignment'),
    
    # Sync API endpoints - Downloads
    path('sync/download-inspection-batch/', sync_views.download_inspection_batch, name='download_inspection_batch'),
    path('sync/inspections/<uuid:id>/photos/', sync_views.download_inspection_photos, name='download_inspection_photos'),
    path('sync/defects/', sync_views.download_general_defects, name='download_general_defects'),
    
    # Sync API endpoints - Uploads (support both GET and POST)
    path('sync/mobile-sync-inspection/', sync_views.mobile_sync_inspection, name='mobile_sync_inspection'),
    path('sync/certificates/e6/', sync_views.download_e6_certificates, name='download_e6_certificates'),
    path('sync/defects/e1/', sync_views.download_e1_defects, name='download_e1_defects'),
    
    # Distribution Tracking & Audit API endpoints
    path('sync/distribution/record/', sync_views.record_document_distribution, name='record_document_distribution'),
    path('sync/distribution/history/', sync_views.get_distribution_history, name='get_distribution_history'),
    path('sync/audit/record/', sync_views.record_certificate_audit, name='record_certificate_audit'),
    path('sync/audit/history/', sync_views.get_audit_history, name='get_audit_history'),
]

