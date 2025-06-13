from django.urls import path
from . import views

urlpatterns = [
    path('devices/', views.device_list, name='device_list'),
    path('devices/create/', views.create_device, name='create_device'),
    path('devices/<int:device_id>/', views.device_detail, name='device_detail'),  # Add this line
    path('assign/', views.assign_device, name='assign_device'),
    path('return/<int:assignment_id>/', views.return_device, name='return_device'),
    path('usage_report/', views.usage_report, name='usage_report'),
    path('faults/create/', views.create_fault, name='create_fault'),
]