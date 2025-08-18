from django.contrib import admin
from .models import (
    SanctionForTestForm, SanctionFormAuditLog, 
    SanctionFormComment, SanctionFormAttachment
)


class SanctionFormAuditLogInline(admin.TabularInline):
    model = SanctionFormAuditLog
    extra = 0
    readonly_fields = ['user', 'action', 'description', 'previous_status', 'new_status', 
                      'approval_step', 'ip_address', 'user_agent', 'timestamp']
    can_delete = False
    max_num = 0


class SanctionFormCommentInline(admin.TabularInline):
    model = SanctionFormComment
    extra = 1
    fields = ['user', 'comment', 'is_private']
    readonly_fields = ['user']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)


class SanctionFormAttachmentInline(admin.TabularInline):
    model = SanctionFormAttachment
    extra = 1
    fields = ['file', 'attachment_type', 'description', 'uploaded_by']
    readonly_fields = ['uploaded_by', 'uploaded_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SanctionForTestForm)
class SanctionForTestFormAdmin(admin.ModelAdmin):
    list_display = ['form_no', 'status', 'priority', 'risk_level', 'created_by', 'region', 'date_issued', 'created_at']
    list_filter = ['status', 'priority', 'risk_level', 'region', 'district', 'date_issued', 'created_at']
    search_fields = ['form_no', 'created_by__username', 'created_by__first_name', 'created_by__last_name', 'work_to_be_carried_out']
    readonly_fields = ('form_no', 'date_issued', 'created_at', 'updated_at')
    
    inlines = [
        SanctionFormCommentInline,
        SanctionFormAttachmentInline,
        SanctionFormAuditLogInline,
    ]
    
    fieldsets = (
        ('Form Information', {
            'fields': ('form_no', 'status', 'priority', 'risk_level', 'created_by', 'date_issued', 'created_at', 'updated_at')
        }),
        ('Regional and Organizational Context', {
            'fields': ('region', 'district', 'section', 'depot', 'cost_center'),
            'classes': ('collapse',)
        }),
        ('Workflow Integration', {
            'fields': ('approval_process',),
            'classes': ('collapse',)
        }),
        ('Section 1.0: ISSUE - Technical Details', {
            'fields': (
                'work_to_be_carried_out', 'plant_or_equipment_to_be_tested',
                'points_of_isolation', 'nearest_point_live', 'circuit_main_earth_connected_at',
                'danger_notices', 'caution_notices', 'special_keys', 'other_precaution'
            )
        }),
        ('Clearance and Cancellation', {
            'fields': ('exceptions', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SanctionFormAuditLog)
class SanctionFormAuditLogAdmin(admin.ModelAdmin):
    list_display = ['form', 'user', 'action', 'approval_step', 'previous_status', 'new_status', 'timestamp']
    list_filter = ['action', 'previous_status', 'new_status', 'approval_step', 'timestamp']
    search_fields = ['form__form_no', 'user__username', 'description']
    readonly_fields = ['form', 'user', 'action', 'description', 'previous_status', 'new_status', 
                      'approval_step', 'ip_address', 'user_agent', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SanctionFormComment)
class SanctionFormCommentAdmin(admin.ModelAdmin):
    list_display = ['form', 'user', 'comment_preview', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['form__form_no', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'


@admin.register(SanctionFormAttachment)
class SanctionFormAttachmentAdmin(admin.ModelAdmin):
    list_display = ['form', 'attachment_type', 'description', 'uploaded_by', 'uploaded_at']
    list_filter = ['attachment_type', 'uploaded_at']
    search_fields = ['form__form_no', 'description', 'uploaded_by__username']
    readonly_fields = ['uploaded_by', 'uploaded_at']
