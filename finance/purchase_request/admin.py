from django.contrib import admin
from .models import PurchaseRequest, Quotation, Item

class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'allocation_code_of_expenditure', 'scope_of_work', 'proc_ref', 'payment_mode', 
    'requested_by', 'ace')

class QuotationAdmin(admin.ModelAdmin):
    list_display = ('purchase_request', 'file')

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'unit_measure', 'price', 'quantity', 'quotation')    

admin.site.register(PurchaseRequest, PurchaseRequestAdmin)
admin.site.register(Quotation, QuotationAdmin)
admin.site.register(Item, ItemAdmin)