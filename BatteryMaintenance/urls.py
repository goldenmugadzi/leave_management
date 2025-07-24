from django.urls import path
from .views import InstallBattery, BatteryInstallationDetailView, BatteryInstallationListView

app_name = 'BatteryMaintenance'

urlpatterns = [
    path('install_battery/', InstallBattery.as_view(), name='install_battery'),
    path('installations/', BatteryInstallationListView.as_view(), name='installations'),
    path('installation/<int:pk>/', BatteryInstallationDetailView.as_view(), name='installation'),
]
