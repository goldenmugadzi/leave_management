from django.urls import path
from . import views

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
] 