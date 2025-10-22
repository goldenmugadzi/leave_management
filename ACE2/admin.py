from django.contrib import admin
from .models import Ace2, AssetBudget, Asset_budget_Virament, Transactions, AceReport, Quotation, AceAssetNumber


@admin.register(Ace2)
class Ace2Admin(admin.ModelAdmin):
    list_display = ['Ace_id2', 'details_of_expenditure', 'amount', 'currency', 'section', 'cost_center', 'region', 'requested_by', 'date_created']
    list_filter = ['currency', 'classification', 'ace_type', 'region', 'section', 'cost_center', 'date_created']
    search_fields = ['Ace_id2', 'details_of_expenditure', 'allocation_code_of_expenditure', 'requested_by__username', 'requested_by__first_name', 'requested_by__last_name']
    autocomplete_fields = ['requested_by', 'section', 'region', 'budget_id', 'cost_center', 'designation', 'process']
    readonly_fields = ['Ace_id2', 'date_created']
    fieldsets = (
        ('Basic Information', {
            'fields': ('Ace_id2', 'details_of_expenditure', 'classification', 'ace_type')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency', 'usd_equivalent', 'quantity', 'budget_id')
        }),
        ('Organization', {
            'fields': ('section', 'cost_center', 'region', 'requested_by', 'designation')
        }),
        ('Project Fields', {
            'fields': ('present_tariff', 'present_fmc', 'capital_contribution', 'materials', 'connection_fee', 'labour', 'transport', 'total_connection_fee'),
            'classes': ('collapse',)
        }),
        ('Capital & Asset', {
            'fields': ('capital_estimated', 'capital_sanctioned', 'asset_number'),
            'classes': ('collapse',)
        }),
        ('Workflow', {
            'fields': ('process', 'date_created')
        }),
    )


@admin.register(AssetBudget)
class AssetBudgetAdmin(admin.ModelAdmin):
    list_display = ['budget_id', 'budget_name', 'section', 'cost_center', 'region', 'allocated', 'withdrawn', 'balance', 'period']
    list_filter = ['region', 'cost_center', 'period', 'created_date']
    search_fields = ['budget_name', 'section', 'section_code']
    autocomplete_fields = ['region', 'cost_center']
    readonly_fields = ['budget_id', 'created_date']


@admin.register(Asset_budget_Virament)
class AssetBudgetViramentAdmin(admin.ModelAdmin):
    list_display = ['virament_id', 'from_budget', 'to_budget', 'amount', 'cost_center', 'section', 'region', 'requested_by', 'date_created']
    list_filter = ['region', 'section', 'cost_center', 'date_created', 'currency']
    search_fields = ['virament_id', 'reason', 'requested_by__username']
    autocomplete_fields = ['requested_by', 'from_budget', 'to_budget', 'section', 'cost_center', 'region', 'process']
    readonly_fields = ['virament_id', 'date_created']


@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'Ace_id2', 'details_of_expenditure', 'amount', 'cost_center', 'section', 'region', 'budget']
    list_filter = ['region', 'section', 'cost_center', 'approval_status']
    search_fields = ['transaction_id', 'details_of_expenditure', 'Ace_id2__Ace_id2']
    autocomplete_fields = ['Ace_id2', 'virament', 'region', 'section', 'cost_center', 'budget']


@admin.register(AceReport)
class AceReportAdmin(admin.ModelAdmin):
    list_display = ['report_id2', 'start_date', 'end_date', 'region', 'cost_center', 'section', 'budget']
    list_filter = ['region', 'cost_center', 'section', 'start_date', 'end_date']
    autocomplete_fields = ['region', 'cost_center', 'section', 'budget']


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['id', 'ace2', 'virament', 'quotation_file']
    search_fields = ['ace2__Ace_id2']
    autocomplete_fields = ['ace2', 'virament']


@admin.register(AceAssetNumber)
class AceAssetNumberAdmin(admin.ModelAdmin):
    list_display = ['ace', 'asset_number', 'is_verified', 'added_by', 'added_date']
    list_filter = ['is_verified', 'added_date']
    search_fields = ['asset_number', 'ace__Ace_id2', 'notes']
    autocomplete_fields = ['ace', 'added_by']
    readonly_fields = ['added_date']
