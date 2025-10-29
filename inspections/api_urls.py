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
    
    # Sync API endpoints
    path('sync/download-inspection-batch/', sync_views.download_inspection_batch, name='download_inspection_batch'),
    path('sync/defects/e1/', sync_views.download_e1_defects, name='download_e1_defects'),
    path('sync/certificates/e6/', sync_views.download_e6_certificates, name='download_e6_certificates'),
    path('sync/inspections/<uuid:id>/photos/', sync_views.download_inspection_photos, name='download_inspection_photos'),
    path('sync/defects/', sync_views.download_general_defects, name='download_general_defects'),
]

