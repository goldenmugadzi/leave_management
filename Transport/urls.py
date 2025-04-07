from django.urls import path

from . import views

urlpatterns = [
    path('register_vehicle', views.register_vehicle, name='register_vehicle'),
    path('table_vehicle/', views.table_vehicle, name="table_vehicle"),
    path('vehicle_datatable/', views.vehicle_datatable),
    path('update_vehicle/<str:id>/', views.update_vehicle, name="update_vehicle"),
    path('upload_vehicle/', views.upload_vehicle, name='upload_vehicle')
    
]