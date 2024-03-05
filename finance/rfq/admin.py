from django.contrib import admin
from .models import RFQ, Quotation

class RFQAdmin(admin.ModelAdmin):
    list_display = ('id','allocation_code_of_expenditure', 'scope_of_work', 'quantity', 'proc_ref', 'amount', 'payment_mode', 'requested_by', 'created_at', 'section', 'ace')

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('rfq', 'quotation_file')

# class ApprovalStageAdmin(admin.ModelAdmin):
#     list_display = ('stage',)

# class ApprovalStatusAdmin(admin.ModelAdmin):
#     list_display = ('stage', 'status')

# class RFQApprovalAdmin(admin.ModelAdmin):
#     list_display = ('rfq', 'approval_status', 'approval_date', 'rejection_reason')

admin.site.register(RFQ, RFQAdmin)
admin.site.register(Quotation, QuotationAdmin)
# admin.site.register(ApprovalStage, ApprovalStageAdmin)
# admin.site.register(ApprovalStatus, ApprovalStatusAdmin)
# admin.site.register(RFQApproval, RFQApprovalAdmin)