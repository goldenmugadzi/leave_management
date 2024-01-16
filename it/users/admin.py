from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(UserProfile)

@admin.register(Notification)
class NonconformityAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read', )
