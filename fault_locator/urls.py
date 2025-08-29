from django.urls import path
from . import views

urlpatterns = [
    # Dashboard and home
    path('', views.fault_locator_dashboard, name='fault_locator_home'),
    path('dashboard/', views.fault_locator_dashboard, name='fault_locator_dashboard'),
    
    # Simplified mobile-friendly views (these exist)
    path('simple-faults/', views.simple_fault_list, name='simple_fault_list'),
    path('quick-report/', views.quick_fault_report, name='quick_fault_report'),
    path('field-update/<int:fault_id>/', views.field_update, name='field_update'),
    path('simple-assign/<int:fault_id>/', views.simple_assign_fault, name='simple_assign_fault'),
    path('simple-assign/', views.simple_assign_fault, name='assign_fault'),
    
    # Team management (these exist)
    path('team-overview/', views.team_overview, name='team_overview'),
    path('teams/', views.team_overview, name='team_list'),  # Redirect to team_overview
    path('my-work/', views.my_work, name='my_work'),
    
    # Team management operations
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('teams/<int:team_id>/add-member/', views.add_team_member, name='add_team_member'),
    path('teams/<int:team_id>/remove-member/<int:member_id>/', views.remove_team_member, name='remove_team_member'),
    
    # Notifications
    path('notify-unassigned/', views.notify_unassigned_faults, name='notify_unassigned_faults'),
    
    # Temporary redirects for missing views - redirect to working alternatives
    path('devices/', views.fault_locator_dashboard, name='device_list'),  # Redirect to dashboard until device_list is created
    path('faults/', views.simple_fault_list, name='fault_list'),  # Use simple_fault_list instead
    
    # Note: These views need to be implemented:
    # - device_list, device_detail, create_device
    # - fault_detail, update_fault_status, create_fault
    # - assign_device_to_team, unassign_device, return_device
    # - deploy_team_to_depot, recall_team_from_depot
    # - usage_report
]