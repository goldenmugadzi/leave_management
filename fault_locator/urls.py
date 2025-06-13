from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_fault, name='report_fault'),
    path('assign_team/<int:fault_id>/', views.assign_team, name='assign_team'),
    path('locate/<int:fault_id>/', views.locate_fault, name='locate_fault'),
    path('verify/<int:fault_id>/', views.verify_fault, name='verify_fault'),
    path('repair/<int:fault_id>/', views.repair_fault, name='repair_fault'),
    path('complete/<int:fault_id>/', views.complete_fault, name='complete_fault'),
    path('energize/<int:fault_id>/', views.energize_circuit, name='energize_circuit'),
    path('', views.fault_dashboard, name='fault_dashboard'),
]