from django.contrib import admin
from .models import *

class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display =('id', 'scope_of_work', 'pr_no', 'requested_by', 'created_at', 'ace', 'process', 'attachments', )

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('purchase_request', 'file')

class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_required', 'unit_of_measurement', 'quantity', 'purchase_request', 'ordered', )
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ('pr_item', 'unit_price', 'quantity')
admin.site.register(QuoteItem, QuoteItemAdmin)
admin.site.register(PurchaseRequest, PurchaseRequestAdmin)
admin.site.register(Quotation, QuotationAdmin)
admin.site.register(PrItem, ItemAdmin)