# admin.py

from django.contrib import admin
from .models import (BatteryInstallation,Cell,BatteryMaintenance,CellReading)
@admin.register(BatteryInstallation)
class BatteryInstallationAdmin(admin.ModelAdmin):
    list_display = ("id", "battery_name",  "date")
    list_filter = ("substation", "date", "cell_type")
    search_fields = ("battery_name", "substation__name")
@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ("id",  "installation", "voltage", "specific_gravity")
    list_filter = ("installation__battery_name",)
    search_fields = ( "installation__battery_name",)
@admin.register(BatteryMaintenance)
class BatteryMaintenanceAdmin(admin.ModelAdmin):
    list_display = ("battery", "reading_type", "water_used", "date")
    list_filter = ("reading_type", "date")
    search_fields = ("battery__battery_name",)
@admin.register(CellReading)
class CellReadingAdmin(admin.ModelAdmin):
    list_display = ("battery_maintenance", "cell", "voltage", "specific_gravity")
    list_filter = ("battery_maintenance__reading_type",)
    search_fields = ("battery_maintenance__battery__battery_name",)