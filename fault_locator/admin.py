from django.contrib import admin
from .models import *

# admin.site.register(Depot)
admin.site.register(FaultLocatorTeam)
admin.site.register(FaultAssignment)

@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    # Priority order: voltage, clients_affected, reported_at, priority, then other details
    list_display = ['voltage', 'clients_affected', 'reported_at', 'priority', 'description', 'depot', 'backfeed', 'status']
    list_filter = ['voltage', 'priority', 'status', 'backfeed', 'depot', 'reported_at']
    search_fields = ['description', 'depot__depot']
    readonly_fields = ['reported_at', 'prioritized_at', 'verified_at']
    ordering = ['-voltage', '-clients_affected', '-reported_at', '-priority']  # Order by your priorities
    
    fieldsets = (
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
