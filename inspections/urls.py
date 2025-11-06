from django.urls import path, include
from . import views
from . import mobile_api_views

app_name = 'inspections'

urlpatterns = [
    # REST API endpoints (for mobile app)
    path('api/', include('inspections.api_urls')),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Customer Management
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<uuid:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<uuid:pk>/edit/', views.customer_edit, name='customer_edit'),
    
    # Contractor Management
    path('contractors/', views.contractor_list, name='contractor_list'),
    path('contractors/create/', views.contractor_create, name='contractor_create'),
    path('contractors/<uuid:pk>/', views.contractor_detail, name='contractor_detail'),
    path('contractors/<uuid:pk>/edit/', views.contractor_edit, name='contractor_edit'),
    
    # Application Management
    path('applications/', views.application_list, name='application_list'),
    path('applications/create/', views.application_create, name='application_create'),
    path('applications/<uuid:pk>/', views.application_detail, name='application_detail'),
    path('applications/<uuid:pk>/edit/', views.application_edit, name='application_edit'),
    
    # Inspection Reports (E117)
    path('inspections/', views.inspection_list, name='inspection_list'),
    path('inspections/create/', views.inspection_create, name='inspection_create'),
    path('inspections/<uuid:pk>/', views.inspection_detail, name='inspection_detail'),
    
    # E6 Certificates
    path('e6-certificates/', views.e6_certificate_list, name='e6_certificate_list'),
    path('e6-certificates/<uuid:pk>/', views.e6_certificate_detail, name='e6_certificate_detail'),
    
    # E1 Defect Reports
    path('e1-reports/', views.e1_defect_report_list, name='e1_defect_report_list'),
    path('e1-reports/<uuid:pk>/', views.e1_defect_report_detail, name='e1_defect_report_detail'),
    
    # Workflows
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/<uuid:pk>/', views.workflow_detail, name='workflow_detail'),
    
    # Assignment Management
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<uuid:pk>/accept/', views.assignment_accept, name='assignment_accept'),
    path('assignments/<uuid:pk>/complete/', views.assignment_complete, name='assignment_complete'),
    
    # API Endpoints
    path('api/my-assignments/', views.api_my_assignments, name='api_my_assignments'),
    path('api/assignments/<uuid:pk>/accept/', views.api_accept_assignment, name='api_accept_assignment'),
    
    # Mobile API Endpoints
    path('api/v1/applications/assigned/', mobile_api_views.get_assigned_applications, name='mobile_api_assigned_applications'),
    path('api/v1/applications/<uuid:application_id>/', mobile_api_views.get_application_details, name='mobile_api_application_details'),
    path('api/v1/applications/<uuid:application_id>/accept/', mobile_api_views.accept_assignment, name='mobile_api_accept_assignment'),
    path('api/v1/applications/<uuid:application_id>/status/', mobile_api_views.update_assignment_status, name='mobile_api_update_status'),
    path('api/v1/applications/<uuid:application_id>/complete/', mobile_api_views.complete_assignment, name='mobile_api_complete_assignment'),
    path('api/v1/applications/<uuid:application_id>/attachments/', mobile_api_views.get_application_attachments, name='mobile_api_application_attachments'),

    # Sync API Endpoints
    path('sync/', include('inspections.sync.urls')),
] 