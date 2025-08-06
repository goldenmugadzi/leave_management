from django.urls import path
from . import views

app_name = 'inspections'

urlpatterns = [
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
    path('inspections/<uuid:pk>/', views.inspection_detail, name='inspection_detail'),
    
    # E6 Certificates
    path('e6-certificates/<uuid:pk>/', views.e6_certificate_detail, name='e6_certificate_detail'),
    
    # E1 Defect Reports
    path('e1-reports/<uuid:pk>/', views.e1_defect_report_detail, name='e1_defect_report_detail'),
    
    # Assignment Management
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<uuid:pk>/accept/', views.assignment_accept, name='assignment_accept'),
    path('assignments/<uuid:pk>/complete/', views.assignment_complete, name='assignment_complete'),
    
    # API Endpoints
    path('api/my-assignments/', views.api_my_assignments, name='api_my_assignments'),
    path('api/assignments/<uuid:pk>/accept/', views.api_accept_assignment, name='api_accept_assignment'),
] 