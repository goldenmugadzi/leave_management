from django.contrib import admin
from django.utils.html import format_html
from .models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory


@admin.register(WeeklyCollections)
class WeeklyCollectionsAdmin(admin.ModelAdmin):
    list_display = [
        'week', 'year', 'week_number', 'zwl_millions', 'usd_millions', 
        'get_location_display', 'updated_at', 'updated_by'
    ]
    list_filter = [
        'year', 'week_number', 'region', 'district', 'depot', 'created_at', 'updated_at'
    ]
    search_fields = ['week', 'region__region', 'district__district', 'depot__depot']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['year', 'week_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('week', 'year', 'week_number')
        }),
        ('Financial Data', {
            'fields': ('zwl_millions', 'usd_millions')
        }),
        ('Location', {
            'fields': ('region', 'district', 'depot'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_location_display(self, obj):
        """Display location information in admin list"""
        return obj.get_location_display()
    get_location_display.short_description = 'Location'
    
    def save_model(self, request, obj, form, change):
        """Set the updated_by field when saving"""
        if not change:  # New object
            obj.updated_by = request.user
        else:  # Existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WeeklyRevenueLost)
class WeeklyRevenueLostAdmin(admin.ModelAdmin):
    list_display = [
        'week', 'year', 'week_number', 'faults_mwh', 'maintenance_mwh', 'total_mwh',
        'get_location_display', 'updated_at', 'updated_by'
    ]
    list_filter = [
        'year', 'week_number', 'region', 'district', 'depot', 'created_at', 'updated_at'
    ]
    search_fields = ['week', 'region__region', 'district__district', 'depot__depot']
    readonly_fields = ['created_at', 'updated_at', 'total_mwh']
    ordering = ['year', 'week_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('week', 'year', 'week_number')
        }),
        ('Revenue Lost Data', {
            'fields': ('faults_mwh', 'maintenance_mwh', 'total_mwh')
        }),
        ('Location', {
            'fields': ('region', 'district', 'depot'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_location_display(self, obj):
        """Display location information in admin list"""
        return obj.get_location_display()
    get_location_display.short_description = 'Location'
    
    def save_model(self, request, obj, form, change):
        """Set the updated_by field when saving"""
        if not change:  # New object
            obj.updated_by = request.user
        else:  # Existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DebtorCategory)
class DebtorCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'percentage', 'year', 'month', 'get_location_display', 
        'updated_at', 'updated_by'
    ]
    list_filter = [
        'category', 'year', 'month', 'region', 'district', 'depot', 'created_at', 'updated_at'
    ]
    search_fields = ['category', 'region__region', 'district__district', 'depot__depot']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['category', 'year', 'month']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'year', 'month')
        }),
        ('Financial Data', {
            'fields': ('percentage',)
        }),
        ('Location', {
            'fields': ('region', 'district', 'depot'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_location_display(self, obj):
        """Display location information in admin list"""
        return obj.get_location_display()
    get_location_display.short_description = 'Location'
    
    def save_model(self, request, obj, form, change):
        """Set the updated_by field when saving"""
        if not change:  # New object
            obj.updated_by = request.user
        else:  # Existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
