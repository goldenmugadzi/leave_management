from django.contrib import admin

from finance import PettyCash
from finance.PettyCash.models import Quotation

# Register your models here.
admin.site.register(PettyCash)
admin.site.register(Quotation)

