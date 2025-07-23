from django.urls import path
from .views import ToolsAndEquipmentFormCreateView,ToolsAndEquipmentFormListView

urlpatterns = [
    path('new-TE-form/', ToolsAndEquipmentFormCreateView.as_view(), name='new-te-form'),
    path('tools-and-equipment-list/', ToolsAndEquipmentFormListView.as_view(), name='tools-and-equipment-list'),
]