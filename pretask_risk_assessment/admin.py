from django.contrib import admin
from .models import PretaskRiskAssessment

@admin.register(PretaskRiskAssessment)
class PretaskRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'risk_level', 'created_at')
    search_fields = ('task_name', 'risk_level')
