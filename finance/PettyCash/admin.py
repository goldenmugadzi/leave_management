from django.contrib import admin
from .models import Pettycash, Quotation, PettycashReport


@admin.register(Pettycash)
class PettycashAdmin(admin.ModelAdmin):
    list_display = ['petty_id', 'details_of_expenditure', 'amount', 'currency', 'payment_mode', 'section', 'cost_center', 'region', 'requested_by', 'date_created']
    list_filter = ['currency', 'payment_mode', 'region', 'section', 'cost_center', 'date_created', 'old_version']
    search_fields = ['petty_id', 'details_of_expenditure', 'requested_by__username', 'requested_by__first_name', 'requested_by__last_name']
    autocomplete_fields = ['section', 'cost_center', 'region', 'requested_by', 'process']
    readonly_fields = ['petty_id', 'date_created']
    fieldsets = (
        ('Basic Information', {
            'fields': ('petty_id', 'details_of_expenditure', 'old_version')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency', 'payment_mode', 'amount_disbursed', 'amount_used')
        }),
        ('Organization', {
            'fields': ('section', 'cost_center', 'region', 'requested_by')
        }),
        ('Documents & Workflow', {
            'fields': ('receipt_file', 'process', 'date_created')
        }),
    )


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['id', 'pettycash', 'quotation_file']
    search_fields = ['pettycash__petty_id']
    autocomplete_fields = ['pettycash']


@admin.register(PettycashReport)
class PettycashReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'start_date', 'end_date', 'region', 'section', 'payment_mode']
    list_filter = ['region', 'section', 'payment_mode', 'start_date']
    autocomplete_fields = ['region', 'section']

