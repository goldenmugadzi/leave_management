from django.urls import path
from .views import *

app_name = "EquipTracker"

urlpatterns = [
    
    path('equipment-tracker/<int:pk>/', EquipmentDetailView.as_view(), name='equipment_tracker'),
    path('equipment-change/', EquipmentChangeView.as_view(), name='equipment_change'),
    path('equipment-list/', EquipmentListView.as_view(), name='equipment_list'),
]
 