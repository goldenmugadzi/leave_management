from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Ace)
admin.site.register(Budget)
admin.site.register(Transactions)
