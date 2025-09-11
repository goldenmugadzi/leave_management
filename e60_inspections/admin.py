from django.contrib import admin
from .models import (
    E60InspectionReport,
    E60TransformerInspection,
    E60CircuitBreakerInspection,
    E60MeteringInspection,
    E60HousingInspection,
    E60FuseInspection,
    E60SurgeArrestorInspection,
    E60GeneralStateInspection,
    E60SafetyInspection,
    E60ConsumerInstallationInspection,
)


class E60TransformerInspectionInline(admin.StackedInline):
    model = E60TransformerInspection
    extra = 0


class E60CircuitBreakerInspectionInline(admin.StackedInline):
    model = E60CircuitBreakerInspection
    extra = 0


class E60MeteringInspectionInline(admin.StackedInline):
    model = E60MeteringInspection
    extra = 0


class E60HousingInspectionInline(admin.StackedInline):
    model = E60HousingInspection
    extra = 0


class E60FuseInspectionInline(admin.StackedInline):
    model = E60FuseInspection
    extra = 0


class E60SurgeArrestorInspectionInline(admin.TabularInline):
    model = E60SurgeArrestorInspection
    extra = 1


class E60GeneralStateInspectionInline(admin.StackedInline):
    model = E60GeneralStateInspection
    extra = 0


class E60SafetyInspectionInline(admin.StackedInline):
    model = E60SafetyInspection
    extra = 0


class E60ConsumerInstallationInspectionInline(admin.StackedInline):
    model = E60ConsumerInstallationInspection
    extra = 0


@admin.register(E60InspectionReport)
class E60InspectionReportAdmin(admin.ModelAdmin):
    list_display = ['report_number', 'substation_name', 'inspection_date', 'inspector', 'status']
    list_filter = ['status', 'inspection_type', 'construction_type', 'inspection_date']
    search_fields = ['report_number', 'substation_name', 'service_number', 'section']
    readonly_fields = ['report_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Header Information', {
            'fields': (
                'report_number',
                'substation_name', 
                'service_number', 
                'section', 
                'construction_type',
                'inspection_date', 
                'inspection_type'
            )
        }),
        ('Inspector Information', {
            'fields': (
                'inspector',
                'inspector_signature',
            )
        }),
        ('Overall Assessment', {
            'fields': (
                'general_condition',
                'remarks',
                'status',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        E60TransformerInspectionInline,
        E60CircuitBreakerInspectionInline,
        E60MeteringInspectionInline,
        E60HousingInspectionInline,
        E60FuseInspectionInline,
        E60SurgeArrestorInspectionInline,
        E60GeneralStateInspectionInline,
        E60SafetyInspectionInline,
        E60ConsumerInstallationInspectionInline,
    ]


@admin.register(E60SurgeArrestorInspection)
class E60SurgeArrestorInspectionAdmin(admin.ModelAdmin):
    list_display = ['inspection_report', 'arrestor_type', 'make_and_type', 'voltage_rating']
    list_filter = ['arrestor_type']
    search_fields = ['inspection_report__report_number', 'make_and_type']