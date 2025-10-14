from django.contrib import admin
from .models import PretaskRiskAssessment

@admin.register(PretaskRiskAssessment)
class PretaskRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('job', 'equipment', 'harzard', 'control_measures', 'created_at')
    search_fields = ('harzard', 'control_measures')
