from django.urls import path
from .views import ToolsAndEquipmentFormCreateView, ToolsAndEquipmentFormListView, ToolsAndEquipmentDetailView, DepotToolsAndEquipmentCreateView

app_name ='tools-and-equipment'
urlpatterns = [
    path('new-TE-form/', ToolsAndEquipmentFormCreateView.as_view(), name='new-te-form'),
    path('depot-te-register/new/', DepotToolsAndEquipmentCreateView.as_view(), name='depot-te-register-new'),
    path('tools-and-equipment-list/', ToolsAndEquipmentFormListView.as_view(), name='tools-and-equipment-list'),
    path('tools-and-equipment/<str:pk>/', ToolsAndEquipmentDetailView.as_view(), name='tools-and-equipment-detail'),
]