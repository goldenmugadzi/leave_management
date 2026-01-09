from django.urls import path

from . import views

urlpatterns = [
    path('register_vehicle', views.register_vehicle, name='register_vehicle'),
    path('table_vehicle/', views.table_vehicle, name="table_vehicle"),
    path('vehicle_datatable/', views.vehicle_datatable),
    path('upload_vehicle/', views.upload_vehicle, name='upload_vehicle'),
    path('vehicle_dashboard/', views.vehicle_dashboard, name='vehicle_dashboard'),
    path('add_trip/', views.add_trip, name=' add_trip'),
    path('trip_list/', views.trip_list, name='  trip_list'),
    path('trips/datatable/', views.trip_datatable, name='trip_datatable'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/datatable/', views.vehicle_datatables, name='vehicle_datatable'),
    path("tyres/", views.tyres_list, name="tyres_list"),
    path("batteries/", views.battery_list, name="battery_list"),
    path("allocations/", views.allocation_list, name="allocation_list"),
    path("add_tyres/", views.add_tyres, name="add_tyres"), 
    path("add_batteries/", views.add_battery, name="add_battery"),
    path("add_allocation/", views.add_allocation, name="add_allocation"),
    path('get_last_reading/<int:vehicle_id>/', views.get_last_reading, name='get_last_reading'),
    path('create_vehicle/', views.create_vehicle, name='create_vehicle'),
]