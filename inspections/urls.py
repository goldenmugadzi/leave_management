from django.urls import path, include
from . import views

app_name = 'inspections'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Client Applications
    path('applications/', views.application_list, name='application_list'),
    path('applications/create/', views.application_create, name='application_create'),
    path('applications/<uuid:pk>/', views.application_detail, name='application_detail'),
    path('applications/<uuid:pk>/edit/', views.application_edit, name='application_edit'),
    
    # Inspection Reports
    path('inspections/', views.inspection_list, name='inspection_list'),
    path('inspections/create/', views.inspection_create, name='inspection_create'),
    path('inspections/<uuid:pk>/', views.inspection_detail, name='inspection_detail'),
    path('inspections/<uuid:pk>/edit/', views.inspection_edit, name='inspection_edit'),
    
    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<uuid:pk>/accept/', views.assignment_accept, name='assignment_accept'),
    path('assignments/<uuid:pk>/complete/', views.assignment_complete, name='assignment_complete'),
    
    # API endpoints for mobile app
    path('api/my-assignments/', views.api_my_assignments, name='api_my_assignments'),
    path('api/assignments/<uuid:pk>/accept/', views.api_accept_assignment, name='api_accept_assignment'),
] 