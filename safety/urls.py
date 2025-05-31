from django.urls import path
from . import views

urlpatterns = [
    path('safety_table/', views.safety_table, name='safety_table'),
    path('reports/new/', views.safety_report_create, name='safety_report_create'),
    path('safety_report_data/', views.safety_report_data, name='safety_report_data'),
]