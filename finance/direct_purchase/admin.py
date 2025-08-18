from django.contrib import admin
from .models import (
    DPProcPlan, DirectPurchase, DPRequiredItems, DPItems, 
    DPBids, DPCompliance, DPComplianceRemarks, DPRanking, 
    DPOrder, DPCommittee, DPApproval
)

@admin.register(DPProcPlan)
class DPProcPlanAdmin(admin.ModelAdmin):
    list_display = ['proc_ref', 'period', 'description', 'annual_cost', 'annual_qty', 'uom', 'proc_method', 'sprc', 'region']
    list_filter = ['proc_method', 'sprc', 'region']
    search_fields = ['proc_ref', 'description']
    ordering = ['proc_ref']

@admin.register(DirectPurchase)
class DirectPurchaseAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'pr_number', 'scope_of_work', 'created_by', 'created_at', 'cancelled', 'closing_date']
    list_filter = ['cancelled', 'created_at', 'closing_date', 'show_site_visit', 'show_sample_required']
    search_fields = ['cs_id', 'pr_number', 'scope_of_work', 'created_by__username']
    readonly_fields = ['created_at', 'cs_id']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('cs_id', 'pr_id', 'pr_number', 'pr_date', 'scope_of_work')
        }),
        ('Procurement Details', {
            'fields': ('proc_plan', 'ref_date', 'closing_date', 'closing_time', 'currency')
        }),
        ('Additional Information', {
            'fields': ('cs_opened', 'tac_date', 'show_site_visit', 'show_sample_required')
        }),
        ('Notes', {
            'fields': ('additional_notes', 'buyers_notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'cost_center', 'section', 'region', 'cancelled', 'created_at')
        }),
    )

@admin.register(DPRequiredItems)
class DPRequiredItemsAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'item_name', 'quantity', 'unit_of_measurement', 'created_at']
    list_filter = ['created_at']
    search_fields = ['item_name', 'cs_id__cs_id']
    ordering = ['cs_id', 'item_name']

@admin.register(DPItems)
class DPItemsAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'item_name', 'quantity', 'unit_of_measurement', 'created_at']
    list_filter = ['created_at']
    search_fields = ['item_name', 'cs_id__cs_id']
    ordering = ['cs_id', 'item_name']

@admin.register(DPBids)
class DPBidsAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'bid_no', 'sup_id', 'item_id', 'unit_price', 'total', 'quote_date']
    list_filter = ['quote_date', 'created_at']
    search_fields = ['bid_no', 'sup_id__name', 'cs_id__cs_id']
    ordering = ['cs_id', 'bid_no']
    date_hierarchy = 'quote_date'

@admin.register(DPCompliance)
class DPComplianceAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'supplier_id', 'decision', 'payment_terms', 'bid_validity', 'delivery_period', 'technical_specifications']
    list_filter = ['decision', 'payment_terms', 'bid_validity', 'delivery_period', 'technical_specifications', 'created_at']
    search_fields = ['supplier_id__name', 'cs_id__cs_id']
    ordering = ['cs_id', 'supplier_id']

@admin.register(DPComplianceRemarks)
class DPComplianceRemarksAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'supplier_id', 'remarks', 'created_at']
    list_filter = ['created_at']
    search_fields = ['supplier_id__name', 'cs_id__cs_id', 'remarks']
    ordering = ['cs_id', 'supplier_id']

@admin.register(DPRanking)
class DPRankingAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'supplier_id', 'rank', 'total', 'created_at']
    list_filter = ['rank', 'created_at']
    search_fields = ['supplier_id__name', 'cs_id__cs_id', 'rank']
    ordering = ['cs_id', 'rank']

@admin.register(DPOrder)
class DPOrderAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'order_no', 'order_status', 'order_date', 'delivery_date', 'payment_status']
    list_filter = ['order_status', 'payment_status', 'order_date', 'delivery_date']
    search_fields = ['order_no', 'cs_id__cs_id']
    ordering = ['cs_id', 'order_no']
    date_hierarchy = 'order_date'

@admin.register(DPCommittee)
class DPCommitteeAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'user', 'committee_name', 'committee_position', 'committee_status', 'committee_approval']
    list_filter = ['committee_status', 'committee_approval', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'cs_id__cs_id']
    ordering = ['cs_id', 'user']

@admin.register(DPApproval)
class DPApprovalAdmin(admin.ModelAdmin):
    list_display = ['cs_id', 'user', 'approver_role', 'approval', 'approval_date']
    list_filter = ['approver_role', 'approval', 'approval_date', 'created_at']
    search_fields = ['user__username', 'approver_role', 'cs_id__cs_id']
    ordering = ['cs_id', 'approver_role']
    date_hierarchy = 'approval_date'
