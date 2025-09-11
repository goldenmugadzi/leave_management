from django.urls import path
from . import views

app_name = 'e60_inspections'

urlpatterns = [
    # List and create views
    path('', views.e60_inspection_list, name='e60_inspection_list'),
    path('create/', views.e60_inspection_create, name='e60_inspection_create'),
    
    # Detail and editing views
    path('<uuid:pk>/', views.e60_inspection_detail, name='e60_inspection_detail'),
    path('<uuid:pk>/edit/', views.e60_inspection_edit, name='e60_inspection_edit'),
    path('<uuid:pk>/delete/', views.e60_inspection_delete, name='e60_inspection_delete'),
    
    # Section-specific editing views
    path('<uuid:pk>/edit/transformer/', views.e60_transformer_edit, name='e60_transformer_edit'),
    path('<uuid:pk>/edit/circuit-breaker/', views.e60_circuit_breaker_edit, name='e60_circuit_breaker_edit'),
    path('<uuid:pk>/edit/metering/', views.e60_metering_edit, name='e60_metering_edit'),
    path('<uuid:pk>/edit/housing/', views.e60_housing_edit, name='e60_housing_edit'),
    path('<uuid:pk>/edit/fuse/', views.e60_fuse_edit, name='e60_fuse_edit'),
    path('<uuid:pk>/edit/surge-arrestor/', views.e60_surge_arrestor_edit, name='e60_surge_arrestor_edit'),
    path('<uuid:pk>/edit/general-state/', views.e60_general_state_edit, name='e60_general_state_edit'),
    path('<uuid:pk>/edit/safety/', views.e60_safety_edit, name='e60_safety_edit'),
    path('<uuid:pk>/edit/consumer-installation/', views.e60_consumer_installation_edit, name='e60_consumer_installation_edit'),
    
    # Export and print views
    path('<uuid:pk>/print/', views.e60_inspection_print, name='e60_inspection_print'),
    path('<uuid:pk>/pdf/', views.e60_inspection_pdf, name='e60_inspection_pdf'),
    path('<uuid:pk>/export/', views.e60_inspection_export, name='e60_inspection_export'),
    
    # Status management
    path('<uuid:pk>/approve/', views.e60_inspection_approve, name='e60_inspection_approve'),
    path('<uuid:pk>/submit/', views.e60_inspection_submit, name='e60_inspection_submit'),
    
    # Dashboard and analytics
    path('dashboard/', views.e60_dashboard, name='e60_dashboard'),
    path('analytics/', views.e60_analytics, name='e60_analytics'),
]
