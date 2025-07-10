from django.urls import path
from . import views

app_name = 'circuit_breaker_maintenance'

urlpatterns = [
    # Circuit Breaker URLs
    path('circuit-breakers/', views.circuit_breaker_list, name='circuit_breaker_list'),
    path('circuit-breakers/create/', views.circuit_breaker_create, name='circuit_breaker_create'),
    # path('circuit-breakers/quick-create/', views.circuit_breaker_quick_create, name='circuit_breaker_quick_create'),
    # path('circuit-breakers/bulk-import/', views.circuit_breaker_bulk_import, name='circuit_breaker_bulk_import'),
    # path('circuit-breakers/bulk-status-change/', views.circuit_breaker_bulk_status_change, name='circuit_breaker_bulk_status_change'),
    # path('circuit-breakers/status-report/', views.circuit_breaker_status_report, name='circuit_breaker_status_report'),
    path('circuit-breakers/<int:pk>/', views.circuit_breaker_detail, name='circuit_breaker_detail'),
    path('circuit-breakers/<int:pk>/edit/', views.circuit_breaker_edit, name='circuit_breaker_edit'),
    path('circuit-breakers/<int:pk>/toggle-status/', views.circuit_breaker_toggle_status, name='circuit_breaker_toggle_status'),
    # path('circuit-breakers/<int:pk>/history/', views.circuit_breaker_history, name='circuit_breaker_history'),
    # path('circuit-breakers/<int:pk>/activation-check/', views.circuit_breaker_activation_check, name='circuit_breaker_activation_check'),
    # path('circuit-breakers/<int:pk>/deactivation-reasons/', views.circuit_breaker_deactivation_reasons, name='circuit_breaker_deactivation_reasons'),
    
    # AJAX endpoints
    # path('api/substations/', views.get_substations_ajax, name='get_substations_ajax'),
    # path('api/suggestions/', views.get_circuit_breaker_suggestions, name='get_suggestions'),
    
    # Maintenance Record URLs
    path('', views.maintenance_record_list, name='record_list'),
    path('maintenance/create/', views.maintenance_record_create, name='record_create'),
    path('maintenance/<uuid:pk>/', views.maintenance_record_detail, name='record_detail'),
    path('maintenance/<uuid:pk>/edit/', views.maintenance_record_edit, name='record_edit'),
]