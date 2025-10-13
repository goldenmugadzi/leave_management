from django.contrib import admin
from .models import *

# admin.site.register(Depot)
admin.site.register(FaultLocatorTeam)
admin.site.register(FaultAssignment)
admin.site.register(CraneTruck)
admin.site.register(CraneRequest)
admin.site.register(CraneJobReport)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['fleet_number', 'reg_number', 'odometer_km', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['fleet_number', 'reg_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['fleet_number']
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('fleet_number', 'reg_number', 'odometer_km', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FaultLocatorDevice)
class FaultLocatorDeviceAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'description', 'vehicle', 'status', 'created_at']
    list_filter = ['status', 'vehicle__status', 'created_at']
    search_fields = ['serial_number', 'description', 'vehicle__fleet_number', 'vehicle__reg_number']
    readonly_fields = ['created_at']
    ordering = ['serial_number']
    
    fieldsets = (
        ('Device Information', {
            'fields': ('serial_number', 'description', 'status')
        }),
        ('Vehicle Assignment', {
            'fields': ('vehicle',),
            'description': 'Vehicle this device is mounted on'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    # Priority order: VVIP, voltage, clients_affected, reported_at, priority, then other details
    list_display = ['vvip', 'voltage', 'clients_affected', 'reported_at', 'priority', 'description', 'depot', 'backfeed', 'status']
    list_filter = ['vvip', 'voltage', 'priority', 'status', 'backfeed', 'depot', 'reported_at']
    search_fields = ['description', 'depot__depot']
    readonly_fields = ['reported_at', 'prioritized_at', 'verified_at']
    ordering = ['-vvip', '-voltage', '-clients_affected', '-reported_at', '-priority']  # VVIP first, then other priorities
    
    fieldsets = (
        ('VVIP Status', {
            'fields': ('vvip',),
            'description': 'VVIP status trumps all other priority criteria'
        }),
        ('Priority Information', {
            'fields': ('voltage', 'clients_affected', 'priority'),
            'description': 'Key priority fields for fault assessment'
        }),
        ('Basic Information', {
            'fields': ('description', 'depot', 'reported_by', 'status')
        }),
        ('Technical Details', {
            'fields': ('backfeed',)
        }),
        ('Workflow', {
            'fields': ('prioritized_by', 'prioritized_at', 'verified_by', 'verified_at')
        }),
        ('Notes', {
            'fields': ('foreperson_notes', 'team_leader_notes', 'location_details'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('reported_at',),
            'classes': ('collapse',)
        }),
    )
