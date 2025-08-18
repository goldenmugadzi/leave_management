from django.contrib import admin
from .models import (
    DashboardPreference, ActionItemMetrics, DashboardWidget, UserWidgetPreference,
    DashboardMetric, WeeklySales, WeeklyOutage, WeeklyFaultMaintenance, TopDebtor
)


@admin.register(DashboardPreference)
class DashboardPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_priority_filter', 'items_per_page', 'email_notifications', 'updated_at']
    list_filter = ['default_priority_filter', 'email_notifications', 'show_completed_actions']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ActionItemMetrics)
class ActionItemMetricsAdmin(admin.ModelAdmin):
    list_display = ['user', 'application', 'item_type', 'item_id', 'action_taken', 'action_date']
    list_filter = ['application', 'item_type', 'action_taken', 'action_date']
    search_fields = ['user__username', 'item_id', 'comments']
    readonly_fields = ['action_date']
    date_hierarchy = 'action_date'


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'widget_type', 'is_active', 'created_at']
    list_filter = ['widget_type', 'is_active']
    search_fields = ['name', 'title', 'description']
    filter_horizontal = ['required_roles']
    readonly_fields = ['created_at']


@admin.register(UserWidgetPreference)
class UserWidgetPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'widget', 'position', 'is_visible']
    list_filter = ['widget', 'is_visible']
    search_fields = ['user__username', 'widget__name']
    ordering = ['user', 'position']


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'unit', 'target', 'progress', 'region', 'district', 'depot', 'updated_at']
    list_filter = ['metric_type', 'region', 'district', 'depot']
    search_fields = ['metric_type', 'value', 'target']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_type', 'value', 'unit', 'target', 'target_unit', 'progress')
        }),
        ('Location', {
            'fields': ('region', 'district', 'depot'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WeeklySales)
class WeeklySalesAdmin(admin.ModelAdmin):
    list_display = ['week', 'zwl', 'usd', 'week_number', 'year', 'region', 'district', 'depot']
    list_filter = ['year', 'region', 'district', 'depot']
    search_fields = ['week', 'zwl', 'usd']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['year', 'week_number']


@admin.register(WeeklyOutage)
class WeeklyOutageAdmin(admin.ModelAdmin):
    list_display = ['week', 'outages', 'resolved', 'pending', 'week_number', 'year', 'region', 'district', 'depot']
    list_filter = ['year', 'region', 'district', 'depot']
    search_fields = ['week']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['year', 'week_number']


@admin.register(WeeklyFaultMaintenance)
class WeeklyFaultMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['week', 'faults', 'maintenance', 'completed', 'pending', 'week_number', 'year', 'region', 'district', 'depot']
    list_filter = ['year', 'region', 'district', 'depot']
    search_fields = ['week']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['year', 'week_number']


@admin.register(TopDebtor)
class TopDebtorAdmin(admin.ModelAdmin):
    list_display = ['rank', 'name', 'amount', 'region', 'district', 'depot', 'updated_at']
    list_filter = ['region', 'district', 'depot']
    search_fields = ['name', 'amount']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['region', 'district', 'depot', 'rank']
