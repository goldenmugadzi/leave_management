from django.urls import path
from . import views

app_name = 'circuit_breaker_maintenance'

urlpatterns = [
    # Circuit Breaker URLs
    path('circuit-breakers/', views.circuit_breaker_list, name='circuit_breaker_list'),
    path('circuit-breakers/create/', views.circuit_breaker_create, name='circuit_breaker_create'),
    path('circuit-breakers/<int:pk>/', views.circuit_breaker_detail, name='circuit_breaker_detail'),
    path('circuit-breakers/<int:pk>/edit/', views.circuit_breaker_edit, name='circuit_breaker_edit'),
    
    # AJAX endpoints
    path('api/substations/', views.get_substations_ajax, name='get_substations_ajax'),
    
    # Maintenance Record URLs (existing)
    path('', views.maintenance_record_list, name='record_list'),
    path('maintenance/create/', views.maintenance_record_create, name='record_create'),
    path('maintenance/<uuid:pk>/', views.maintenance_record_detail, name='record_detail'),
    path('maintenance/<uuid:pk>/edit/', views.maintenance_record_edit, name='record_edit'),
]