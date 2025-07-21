from django.contrib import admin
from .models import *

# admin.site.register(Depot)
admin.site.register(FaultLocatorTeam)
admin.site.register(FaultAssignment)

@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    list_display = ['description', 'depot', 'voltage', 'backfeed', 'clients_affected', 'priority', 'status', 'reported_at']
    list_filter = ['status', 'priority', 'voltage', 'backfeed', 'depot']
    search_fields = ['description', 'depot__depot']
    readonly_fields = ['reported_at', 'prioritized_at', 'verified_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('description', 'depot', 'reported_by', 'status', 'priority')
        }),
        ('Technical Details', {
            'fields': ('voltage', 'backfeed', 'clients_affected')
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
