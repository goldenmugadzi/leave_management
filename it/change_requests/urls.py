from django.urls import path

from . import views

urlpatterns = [
    path('change_request_index', views.change_request_index, name='change_request_index'),
    path('change_request_reports', views.change_request_reports, name='change_request_reports'),
    path('create_change_request', views.create_change_request, name='create_change_request'),
    
    # ==================== NEW UNIFIED ENDPOINTS ====================
    # These use the refactored service layer
    path('view_cr', views.view_change_request_unified, name='view_change_request_unified'),
    path('approve_cr', views.approve_change_request_unified, name='approve_change_request_unified'),
    path('create_cr', views.create_change_request_handler_unified, name='create_change_request_handler_unified'),
    # ==================== END NEW UNIFIED ENDPOINTS ====================
    
    # Legacy endpoints - kept for backward compatibility
    # TODO: These can be removed after migration is complete and all links are updated
    path('create_new_profile', views.create_new_profile, name='create_new_profile'),
    path('new_profile_request', views.new_profile_request, name='new_profile_request'),
    path('update_new_profile_request', views.update_new_profile_request, name='update_new_profile_request'),
    path('view_change_request', views.view_profile_request, name='view_profile_request'),
    path('approve_change_request', views.approve_profile_request, name='approve_profile_request'),
    path('profile_modification/create', views.profile_modification_request, name='profile_modification_request'),
    path('profile_deactivation_request', views.profile_deactivation_request, name='profile_deactivation_request'),
    
    # Common endpoints (not changed)
    path('datatables/export', views.get_csv_export, name='get_csv_export'),
    path('datatables/<str:view>', views.datatable_data, name='datatable_data'),
    path('profile_modification/get_user_data/<str:username>', views.get_user_data, name='get_user_data'),
    path('update_change_request', views.update_change_request, name='update_change_request'),
    path('delete_change_request', views.delete_change_request, name='delete_change_request'),
    path('restore_change_request', views.restore_change_request, name='restore_change_request'),
    path('bulk_delete_change_requests', views.bulk_delete_change_requests, name='bulk_delete_change_requests'),
    path('get_delegation_roles', views.get_delegation_roles, name='get_delegation_roles'),
    path('get_delegator_roles_by_app', views.get_delegator_roles_by_app, name='get_delegator_roles_by_app'),
    path('api/cost_centers/', views.api_cost_centers, name='api_cost_centers'),
    path('api/applications/', views.api_applications, name='api_applications'),
    
    # Optimized API endpoints - Phase 3 Performance Enhancement
    path('api/v2/change_requests/', views.api_change_requests_optimized, name='api_change_requests_optimized'),
    path('api/v2/stats/', views.api_change_request_stats, name='api_change_request_stats'),
    path('api/v2/change_requests/<str:cr_id>/', views.api_change_request_detail, name='api_change_request_detail'),
    path('api/v2/metrics/', views.api_performance_metrics, name='api_performance_metrics'),
    
]