from django.urls import path
from . import views

app_name = 'equipment_management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Equipment URLs
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/create/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/edit/', views.equipment_edit, name='equipment_edit'),
    # path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),
    
    # Operation URLs
    path('operations/', views.operation_list, name='operation_list'),
    path('operations/<int:pk>/', views.operation_detail, name='operation_detail'),
    path('operations/create/', views.operation_create, name='operation_create'),
    path('operations/<int:pk>/edit/', views.operation_edit, name='operation_edit'),
    # path('operations/<int:pk>/approve/', views.operation_approve, name='operation_approve'),
    
    # API endpoints
    path('api/equipment/search/', views.equipment_search_api, name='equipment_search_api'),
]
