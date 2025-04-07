from django.contrib import admin
from .models import Customer, DocumentType, CustomerDocument, OnboardingProcess, ActivityLog

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_id', 'customer_type', 'account_number', 'meter_number', 'is_active')
    list_filter = ('customer_type', 'is_active', 'date_created')
    search_fields = ('name', 'customer_id', 'account_number', 'meter_number', 'email')
    date_hierarchy = 'date_created'

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'required', 'description')
    list_filter = ('required',)
    search_fields = ('name', 'description')

@admin.register(CustomerDocument)
class CustomerDocumentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'document_type', 'status', 'upload_date', 'expiry_date')
    list_filter = ('status', 'document_type', 'upload_date')
    search_fields = ('customer__name', 'customer__customer_id', 'document_type__name')
    date_hierarchy = 'upload_date'
    raw_id_fields = ('customer', 'uploaded_by', 'approved_by')

@admin.register(OnboardingProcess)
class OnboardingProcessAdmin(admin.ModelAdmin):
    list_display = ('customer', 'status', 'initiated_date', 'completed_date')
    list_filter = ('status', 'initiated_date')
    search_fields = ('customer__name', 'customer__customer_id', 'notes')
    date_hierarchy = 'initiated_date'
    raw_id_fields = ('customer', 'initiated_by')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('customer', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('customer__name', 'customer__customer_id', 'action', 'details')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('customer', 'user')
