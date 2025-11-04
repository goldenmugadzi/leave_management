from django.contrib import admin
from .models import *

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Workflow._meta.fields]

@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Step._meta.fields]

@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Process._meta.fields]
    search_fields = ('name', 'description')

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('step', 'user', 'comment', 'approved', )

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['name']

# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display =('name', 'description', )





