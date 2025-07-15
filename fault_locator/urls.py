from django.urls import path
from . import views
from . import role_views

urlpatterns = [
    # Dashboard and home
    path('', views.fault_locator_dashboard, name='fault_locator_home'),
    path('dashboard/', views.fault_locator_dashboard, name='fault_locator_dashboard'),
    
    # New Role-Based Dashboard
    path('role-dashboard/', role_views.role_based_dashboard, name='role_based_dashboard'),
    path('assign-role/', role_views.assign_role, name='assign_role'),
    
    # Simplified mobile-friendly views (these exist)
    path('simple-faults/', views.simple_fault_list, name='simple_fault_list'),
    path('quick-report/', views.quick_fault_report, name='quick_fault_report'),
    path('create-fault/', views.create_fault, name='create_fault'),
    path('field-update/<int:fault_id>/', views.field_update, name='field_update'),
    path('simple-assign/<int:fault_id>/', views.simple_assign_fault, name='simple_assign_fault'),
    path('simple-assign/', views.simple_assign_fault, name='assign_fault'),
    
    # Team management (these exist)
    path('team-overview/', views.team_overview, name='team_overview'),
    path('teams/', views.team_overview, name='team_list'),  # Redirect to team_overview
    path('my-work/', views.my_work, name='my_work'),
    
    # Notifications
    path('notify-unassigned/', views.notify_unassigned_faults, name='notify_unassigned_faults'),
    
    # Device Management
    path('devices/', views.device_list, name='device_list'),
    path('devices/create/', views.create_device, name='create_device'),
    path('devices/<int:device_id>/', views.device_detail, name='device_detail'),
    path('devices/<int:device_id>/edit/', views.edit_device, name='edit_device'),
    path('devices/<int:device_id>/unassign/', views.unassign_device, name='unassign_device'),
    path('assign-device-to-team/', views.assign_device_to_team, name='assign_device_to_team'),
    
    # Team Management
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    
    # Team Deployment
    path('teams/deploy/', views.deploy_team, name='deploy_team'),
    path('teams/<int:team_id>/deploy/', views.deploy_team, name='deploy_team_specific'),
    path('teams/<int:team_id>/recall/', views.recall_team, name='recall_team'),
    
    # Advanced Fault Assignment
    path('advanced-assign/', views.advanced_fault_assignment, name='advanced_fault_assignment'),
    
    # Fallback for fault list
    path('faults/', views.simple_fault_list, name='fault_list'),  # Use simple_fault_list instead
]