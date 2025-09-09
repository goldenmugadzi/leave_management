from django.urls import path
from . import views

app_name = 'substation_inspections'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Substation management
    path('substations/', views.substation_list, name='substation_list'),
    path('substations/create/', views.substation_create, name='substation_create'),
    path('substations/<uuid:pk>/', views.substation_detail, name='substation_detail'),
    path('substations/<uuid:pk>/edit/', views.substation_edit, name='substation_edit'),
    
    # Inspection reports
    path('reports/', views.inspection_report_list, name='inspection_report_list'),
    path('reports/create/', views.inspection_report_create, name='inspection_report_create'),
    path('reports/<uuid:pk>/', views.inspection_report_detail, name='inspection_report_detail'),
    path('reports/<uuid:pk>/edit/', views.inspection_report_edit, name='inspection_report_edit'),
    
    # Inspection schedules
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<uuid:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    
    # Checklist items
    path('checklist/', views.checklist_item_list, name='checklist_item_list'),
    path('checklist/create/', views.checklist_item_create, name='checklist_item_create'),
    path('checklist/<uuid:pk>/edit/', views.checklist_item_edit, name='checklist_item_edit'),
    
    # Bulk operations
    path('bulk-assignment/', views.bulk_assignment, name='bulk_assignment'),
    
    # API endpoints
    path('api/substation/<uuid:pk>/', views.get_substation_details, name='api_substation_details'),
    path('api/stats/', views.get_inspection_stats, name='api_inspection_stats'),
]
