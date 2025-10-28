"""
API URL Configuration for Inspections App
Routes for mobile application API endpoints
"""

from django.urls import path
from . import api_views

app_name = 'inspections_api'

urlpatterns = [
    # Application API endpoints
    path('v1/applications/assigned/', api_views.assigned_applications, name='assigned_applications'),
    path('v1/applications/<uuid:pk>/', api_views.application_detail, name='application_detail'),
    path('v1/applications/<uuid:pk>/accept/', api_views.accept_assignment, name='accept_assignment'),
]

