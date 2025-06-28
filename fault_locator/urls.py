from django.urls import path
from . import views

urlpatterns = [
    path('', views.fault_locator_home, name='fault_locator_home'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/create/', views.create_device, name='create_device'),
    path('devices/<int:device_id>/', views.device_detail, name='device_detail'),  # Add this line
    path('assign-fault/', views.assign_fault, name='assign_fault'),
    path('return/<int:assignment_id>/', views.return_device, name='return_device'),
    path('usage_report/', views.usage_report, name='usage_report'),
    path('faults/create/', views.create_fault, name='create_fault'),
    path('faults/', views.fault_list, name='fault_list'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/add_member/', views.add_team_member, name='add_team_member'),
    path('teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('teams/<int:team_id>/remove_member/<int:member_id>/', views.remove_team_member, name='remove_team_member'),
    path('teams/', views.team_list, name='team_list'),
    path('assign-device-to-team/', views.assign_device_to_team, name='assign_device_to_team'),
    path('devices/<int:device_id>/unassign/', views.unassign_device, name='unassign_device'),

    # Senior Foreperson functions
    path('deploy-team/', views.deploy_team_to_depot, name='deploy_team_to_depot'),
    path('recall-team/<int:deployment_id>/', views.recall_team_from_depot, name='recall_team_from_depot'),
    path('senior-assign-device/', views.senior_device_assignment, name='senior_device_assignment'),
    path('team-deployments/', views.team_deployments, name='team_deployments'),

    # Depot Foreperson functions  
    path('depot/<int:depot_id>/fault-priority/', views.depot_fault_priority, name='depot_fault_priority'),
]