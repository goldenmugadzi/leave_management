from django.contrib import admin
from django.utils.html import format_html
from .models import Equipment, EquipmentOperation, OperationDocument, EquipmentHistory


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'serial_number', 'equipment_type', 'make', 'status', 
        'substation_name', 'district', 'installation_date'
    ]
    list_filter = [
        'equipment_type', 'status', 'district', 'installation_date'
    ]
    search_fields = [
        'serial_number', 'make', 'substation_name', 'location_description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Equipment Information', {
            'fields': (
                'equipment_type', 'make', 'serial_number',
                'kva_rating', 'ampere_rating', 'voltage_rating'
            )
        }),
        ('Location', {
            'fields': (
                'substation_name', 'section', 'district', 'location_description'
            )
        }),
        ('Status', {
            'fields': (
                'status', 'installation_date'
            )
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class OperationDocumentInline(admin.TabularInline):
    model = OperationDocument
    extra = 1
    readonly_fields = ['file_size', 'uploaded_at']


@admin.register(EquipmentOperation)
class EquipmentOperationAdmin(admin.ModelAdmin):
    list_display = [
        'form_number', 'operation_type', 'consumer_name', 
        'status', 'priority', 'operation_date', 'created_by'
    ]
    list_filter = [
        'operation_type', 'status', 'priority', 'district', 
        'operation_date', 'created_at'
    ]
    search_fields = [
        'form_number', 'consumer_name', 'substation_name', 
        'operator_name', 'reason'
    ]
    readonly_fields = [
        'form_number', 'created_at', 'updated_at', 'approval_date'
    ]
    inlines = [OperationDocumentInline]
    
    fieldsets = (
        ('Operation Details', {
            'fields': (
                'form_number', 'operation_type', 'priority', 
                'operation_date', 'scheduled_date', 'completion_date'
            )
        }),
        ('Consumer Information', {
            'fields': (
                'consumer_name', 'consumer_account_number'
            )
        }),
        ('Location', {
            'fields': (
                'substation_name', 'section', 'district'
            )
        }),
        ('Equipment', {
            'fields': (
                'equipment_installed', 'equipment_removed'
            )
        }),
        ('Operation Details', {
            'fields': (
                'reason', 'operator_name', 'operator_designation',
                'estimated_duration_hours', 'actual_duration_hours',
                'cost_estimate', 'actual_cost'
            )
        }),
        ('Status & Approval', {
            'fields': (
                'status', 'created_by', 'reviewed_by', 'approved_by',
                'review_notes', 'approval_date'
            )
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and obj.status in ['approved', 'completed']:
            readonly_fields.extend([
                'operation_type', 'equipment_installed', 'equipment_removed',
                'reason', 'operator_name'
            ])
        return readonly_fields


@admin.register(OperationDocument)
class OperationDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'operation', 'document_type', 'file_name', 
        'file_size_display', 'uploaded_at', 'uploaded_by'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['operation__form_number', 'file_name', 'description']
    readonly_fields = ['file_size', 'uploaded_at', 'file_name']

    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} bytes"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size // 1024} KB"
            else:
                return f"{obj.file_size // (1024 * 1024)} MB"
        return "Unknown"
    file_size_display.short_description = "File Size"

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EquipmentHistory)
class EquipmentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'equipment', 'action_type', 'performed_by', 'performed_at'
    ]
    list_filter = ['action_type', 'performed_at']
    search_fields = [
        'equipment__serial_number', 'action_description', 
        'performed_by__username'
    ]
    readonly_fields = ['performed_at']

    def has_add_permission(self, request):
        # History records should be created automatically, not manually
        return False

    def has_change_permission(self, request, obj=None):
        # History records should not be editable
        return False
