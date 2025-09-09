from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    # Dashboard overview page
    path('', views.dashboard_index, name='dashboard_overview'),
    path('overview/', views.dashboard_index, name='dashboard_overview'),
    
    # Data retrieval endpoints
    path('regions/', views.get_regions, name='get_regions'),
    path('dashboard-data/', views.get_dashboard_data, name='get_dashboard_data'),
    path('user-permissions/', views.get_user_permissions, name='get_user_permissions'),
    
    # Data saving endpoints
    path('save-dashboard-data/', views.save_dashboard_data, name='save_dashboard_data'),
    
    # Utility endpoints
    path('create-sample-data/', views.create_sample_data, name='create_sample_data'),
    
    # CSV Import/Export endpoints
    path('download-template/', views.download_csv_template, name='download_csv_template'),
    path('bulk-upload/', views.bulk_upload_dashboard_data, name='bulk_upload_dashboard_data'),
    

]
