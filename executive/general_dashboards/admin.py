from django.contrib import admin
from .models import DashboardPreference, ActionItemMetrics, DashboardWidget, UserWidgetPreference


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
