from django.contrib import admin
from .models import RFQ, Quotation

class RFQAdmin(admin.ModelAdmin):
    list_display = ('id', 'allocation_code_of_expenditure', 'scope_of_work', 'quantity', 'proc_ref', 'amount', 'payment_mode', 
    'requested_by', 'ace')

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('rfq', 'quotation_file')

admin.site.register(RFQ, RFQAdmin)
admin.site.register(Quotation, QuotationAdmin)