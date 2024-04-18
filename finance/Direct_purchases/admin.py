from django.contrib import admin


from finance.Direct_purchases.models import *

# Register your models here.
admin.site.register(Direct_purchase)
admin.site.register(Supplier)
admin.site.register(Item)

