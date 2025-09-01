from django.urls import path
from .views import (
    InstallBattery,
    BatteryInstallationDetailView,
    BatteryInstallationListView,
    import_substations_from_csv,
    InspectBattery,
    clear_notifications
)

app_name = "BatteryMaintenance"

urlpatterns = [
    path("inspect_battery/<int:pk>/", InspectBattery.as_view(), name="inspect_battery"),
    path("install_battery/", InstallBattery.as_view(), name="install_battery"),
    path("installations/", BatteryInstallationListView.as_view(), name="installations"),
    path("installation/<int:pk>/",BatteryInstallationDetailView.as_view(),name="installation"),
    path("import-substations/", import_substations_from_csv, name="import_substations"),
    path('clear-notifications/', clear_notifications, name='clear_notifications'),
]
