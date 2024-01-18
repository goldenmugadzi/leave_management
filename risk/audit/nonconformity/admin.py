
# Register your models here.
from django.contrib import admin
from .models import *

@admin.register(Nonconformity)
class NonconformityAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'recipient', 'description', 'violation_standard_reference', 'recommended_corrective_action', 'created_at', 'attachment', )
@admin.register(Response)
class NonconformityAdmin(admin.ModelAdmin):
    list_display =('user', 'nonconformity', 'comment', 'created_at', 'status', )