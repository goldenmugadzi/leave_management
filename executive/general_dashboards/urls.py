from django.urls import path
from . import views

app_name = 'general_dashboards'

urlpatterns = [
    path('', views.action_dashboard, name='action_dashboard'),
    path('api/', views.dashboard_api, name='dashboard_api'),
    path('preferences/', views.update_preferences, name='update_preferences'),
] 