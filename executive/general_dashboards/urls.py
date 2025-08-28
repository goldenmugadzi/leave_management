from django.urls import path
from . import views
from . import monitoring_views

app_name = 'general_dashboards'

urlpatterns = [
    path('', views.action_dashboard, name='action_dashboard'),
    path('api/', views.dashboard_api, name='dashboard_api'),
    path('preferences/', views.update_preferences, name='update_preferences'),
    
    # New dashboard data endpoints
    path('regions/', views.get_regions, name='get_regions'),
    path('dashboard_data/', views.get_dashboard_data, name='get_dashboard_data'),
    path('dashboard_filter/', views.dashboard_filter, name='dashboard_filter'),
    path('save_dashboard_data/', views.save_dashboard_data, name='save_dashboard_data'),
    path('user_permissions/', views.user_permissions, name='user_permissions'),
    path('debug_user_roles/', views.debug_user_roles, name='debug_user_roles'),
    
    # Monitoring and logging endpoints
    path('monitoring/', monitoring_views.monitoring_dashboard, name='monitoring_dashboard'),
    path('monitoring/api/performance/', monitoring_views.api_performance_stats, name='api_performance_stats'),
    path('monitoring/api/health/', monitoring_views.system_health, name='system_health'),
    path('monitoring/api/reset/', monitoring_views.reset_performance_metrics, name='reset_performance_metrics'),
    path('monitoring/api/queries/', monitoring_views.query_performance, name='query_performance'),
    path('monitoring/api/errors/', monitoring_views.error_logs, name='error_logs'),
    path('monitoring/status/', monitoring_views.monitoring_status, name='monitoring_status'),
] 