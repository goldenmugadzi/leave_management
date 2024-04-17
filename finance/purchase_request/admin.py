from django.contrib import admin
from .models import *

class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'allocation_code_of_expenditure', 'scope_of_work', 'proc_ref', 'payment_mode', 
    'requested_by', 'ace')

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('purchase_request', 'file')

class ItemAdmin(admin.ModelAdmin):
    list_display =('name', 'description', 'unit_of_measurement','quantity', )
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ('pr_item', 'unit_price', 'quantity')
admin.site.register(QuoteItem, QuoteItemAdmin)
admin.site.register(PurchaseRequest, PurchaseRequestAdmin)
admin.site.register(Quotation, QuotationAdmin)
admin.site.register(PrItem, ItemAdmin)