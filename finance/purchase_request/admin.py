from django.contrib import admin
from .models import *

class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display =('id', 'scope_of_work', 'pr_no', 'requested_by', 'created_at', 'ace', 'process',  )

class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_required', 'unit_of_measurement', 'quantity', 'purchase_request', 'ordered', )
admin.site.register(PurchaseRequest, PurchaseRequestAdmin)
admin.site.register(PrItem, ItemAdmin)