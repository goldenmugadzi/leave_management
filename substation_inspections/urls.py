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
    
    # Phase 2: Scheduling & Monitoring
    path('monitoring/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('inspector-workload/', views.inspector_workload, name='inspector_workload'),
    path('auto-assign/', views.auto_assign_inspections, name='auto_assign_inspections'),
    path('reports/<uuid:pk>/reassign/', views.reassign_inspection, name='reassign_inspection'),
    path('notifications/', views.send_notifications, name='send_notifications'),
    path('generate-inspections/', views.generate_inspections, name='generate_inspections'),
    
    # HTMX endpoints for real-time updates
    path('htmx/dashboard-stats/', views.dashboard_stats_partial, name='dashboard_stats_partial'),
    path('htmx/upcoming-inspections/', views.upcoming_inspections_partial, name='upcoming_inspections_partial'),
    path('htmx/overdue-inspections/', views.overdue_inspections_partial, name='overdue_inspections_partial'),
    
    # API endpoints
    path('api/substation/<uuid:pk>/', views.get_substation_details, name='api_substation_details'),
    path('api/stats/', views.get_inspection_stats, name='api_inspection_stats'),
]
