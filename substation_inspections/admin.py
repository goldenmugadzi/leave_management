from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Substation, 
    MonthlyInspectionSchedule, 
    MonthlyInspectionReport, 
    InspectionChecklistItem, 
    InspectionItemResponse
)


@admin.register(Substation)
class SubstationAdmin(admin.ModelAdmin):
    list_display = [
        'substation_code', 'name', 'substation_type', 'voltage_level',
        'location', 'district', 'region', 'is_active', 'last_inspection_date',
        'next_scheduled_inspection'
    ]
    list_filter = [
        'substation_type', 'voltage_level', 'district', 'region', 'is_active'
    ]
    search_fields = ['substation_code', 'name', 'location', 'district', 'region']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('substation_code', 'name', 'substation_type', 'voltage_level')
        }),
        ('Location', {
            'fields': ('location', 'district', 'region')
        }),
        ('Equipment Inventory', {
            'fields': ('transformers_count', 'circuit_breakers_count', 'switchgear_count')
        }),
        ('Status', {
            'fields': ('is_active', 'last_inspection_date', 'next_scheduled_inspection')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(MonthlyInspectionSchedule)
class MonthlyInspectionScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'substation', 'frequency', 'day_of_month', 'assigned_inspector',
        'is_active', 'reminder_days_before', 'escalation_days_after_due'
    ]
    list_filter = ['frequency', 'is_active', 'substation__substation_type']
    search_fields = ['substation__name', 'substation__substation_code', 'assigned_inspector__username']
    list_editable = ['is_active', 'reminder_days_before', 'escalation_days_after_due']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('substation', 'frequency', 'day_of_month', 'assigned_inspector')
        }),
        ('Notification Settings', {
            'fields': ('reminder_days_before', 'escalation_days_after_due')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('substation', 'assigned_inspector')


@admin.register(MonthlyInspectionReport)
class MonthlyInspectionReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_number', 'substation', 'inspection_date', 'inspector',
        'status', 'compliance_status', 'created_at'
    ]
    list_filter = [
        'status', 'compliance_status', 'inspection_date', 'substation__substation_type'
    ]
    search_fields = [
        'report_number', 'substation__name', 'substation__substation_code',
        'inspector__username', 'inspector__first_name', 'inspector__last_name'
    ]
    list_editable = ['status', 'compliance_status']
    readonly_fields = ['report_number', 'created_at', 'updated_at']
    date_hierarchy = 'inspection_date'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_number', 'substation', 'inspection_date', 'scheduled_date', 'inspector')
        }),
        ('Environmental Conditions', {
            'fields': ('weather_conditions', 'temperature', 'humidity')
        }),
        ('Inspection Status', {
            'fields': ('status', 'compliance_status')
        }),
        ('Assessment', {
            'fields': ('overall_condition', 'critical_issues', 'recommendations')
        }),
        ('Approval', {
            'fields': ('supervisor_approval', 'approval_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('substation', 'inspector', 'supervisor_approval')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'completed':
            return self.readonly_fields + ['substation', 'inspection_date', 'inspector']
        return self.readonly_fields


@admin.register(InspectionChecklistItem)
class InspectionChecklistItemAdmin(admin.ModelAdmin):
    list_display = [
        'item_code', 'title', 'category', 'severity', 'is_mandatory',
        'is_active', 'frequency'
    ]
    list_filter = ['category', 'severity', 'is_mandatory', 'is_active', 'frequency']
    search_fields = ['item_code', 'title', 'description', 'reference_standard']
    list_editable = ['is_mandatory', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('item_code', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'severity', 'is_mandatory', 'is_active')
        }),
        ('Reference Information', {
            'fields': ('reference_standard', 'frequency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InspectionItemResponse)
class InspectionItemResponseAdmin(admin.ModelAdmin):
    list_display = [
        'inspection_report', 'checklist_item', 'response', 'defect_identified',
        'corrective_action_required', 'checked_at'
    ]
    list_filter = [
        'response', 'defect_identified', 'corrective_action_required',
        'checklist_item__category', 'defect_severity'
    ]
    search_fields = [
        'inspection_report__report_number', 'checklist_item__title',
        'checklist_item__item_code', 'observations'
    ]
    readonly_fields = ['checked_at', 'updated_at']
    date_hierarchy = 'checked_at'
    
    fieldsets = (
        ('Response Information', {
            'fields': ('inspection_report', 'checklist_item', 'response', 'observations')
        }),
        ('Defect Information', {
            'fields': ('defect_identified', 'defect_description', 'defect_severity')
        }),
        ('Corrective Action', {
            'fields': ('corrective_action_required', 'corrective_action_description', 'target_completion_date')
        }),
        ('Additional Data', {
            'fields': ('photos', 'measurements')
        }),
        ('Timestamps', {
            'fields': ('checked_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'inspection_report__substation', 'checklist_item'
        )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.inspection_report.status == 'completed':
            return self.readonly_fields + ['inspection_report', 'checklist_item', 'response']
        return self.readonly_fields


# Custom admin site configuration
admin.site.site_header = "Substation Inspection Administration"
admin.site.site_title = "Substation Inspections"
admin.site.index_title = "Substation Inspection Management"