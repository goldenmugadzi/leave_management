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
    
<<<<<<< HEAD
    # Gear Management
    path('devices/', views.device_list, name='device_list'),
    path('devices/create/', views.create_device, name='create_device'),
    path('devices/<int:device_id>/', views.device_detail, name='device_detail'),
    path('devices/<int:device_id>/edit/', views.edit_device, name='edit_device'),
    path('devices/<int:device_id>/unassign/', views.unassign_device, name='unassign_device'),
    path('assign-device-to-team/', views.assign_device_to_team, name='assign_device_to_team'),
=======
    # Team management operations
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('teams/<int:team_id>/add-member/', views.add_team_member, name='add_team_member'),
    path('teams/<int:team_id>/remove-member/<int:member_id>/', views.remove_team_member, name='remove_team_member'),
    
    # Notifications
    path('notify-unassigned/', views.notify_unassigned_faults, name='notify_unassigned_faults'),
>>>>>>> 8ac5c72c2f3ee3fb177a21305176b062e3001c87
    
    # Temporary redirects for missing views - redirect to working alternatives
    path('devices/', views.fault_locator_dashboard, name='device_list'),  # Redirect to dashboard until device_list is created
    path('faults/', views.simple_fault_list, name='fault_list'),  # Use simple_fault_list instead
    
<<<<<<< HEAD
    # Individual fault detail/update view
    path('faults/<int:fault_id>/', views.field_update, name='fault_detail'),
    
    # Fault priority change
    path('faults/<int:fault_id>/change-priority/', views.change_fault_priority, name='change_fault_priority'),
    
    # Additional convenience URLs for dashboard access
    path('field-update/', views.simple_fault_list, name='field_update_list'),  # For field updates selection
    path('my-assignments/', views.my_work, name='my_assignments'),  # Team leader assignments
    path('team-work/', views.my_work, name='team_work'),  # Team member work view
    path('contact-leader/', views.team_overview, name='contact_leader'),  # Contact team leader
    path('request-help/', views.team_overview, name='request_help'),  # Request assistance
    
    # Debug view
    path('debug-user/', views.debug_user, name='debug_user'),
    path('debug-roles/', role_views.debug_role_status, name='debug_role_status'),

    # Role troubleshooting
    path('troubleshoot/', views.role_troubleshooting, name='role_troubleshooting'),
]

# Crane management URLs
urlpatterns += [
    path('cranes/trucks/', views.crane_truck_list, name='crane_truck_list'),
    path('cranes/trucks/create/', views.crane_truck_create, name='crane_truck_create'),
    path('cranes/trucks/<int:truck_id>/edit/', views.crane_truck_edit, name='crane_truck_edit'),
    path('cranes/requests/', views.crane_request_list, name='crane_request_list'),
    path('cranes/requests/create/', views.crane_request_create, name='crane_request_create'),
    path('cranes/requests/<int:request_id>/assign/', views.crane_request_assign, name='crane_request_assign'),
    path('cranes/requests/<int:request_id>/report/', views.crane_job_report, name='crane_job_report'),
    path('cranes/availability/', views.crane_availability, name='crane_availability'),
    
    # Vehicle management URLs
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:vehicle_id>/edit/', views.vehicle_edit, name='vehicle_edit'),
=======
    # Note: These views need to be implemented:
    # - device_list, device_detail, create_device
    # - fault_detail, update_fault_status, create_fault
    # - assign_device_to_team, unassign_device, return_device
    # - deploy_team_to_depot, recall_team_from_depot
    # - usage_report
>>>>>>> 8ac5c72c2f3ee3fb177a21305176b062e3001c87
]