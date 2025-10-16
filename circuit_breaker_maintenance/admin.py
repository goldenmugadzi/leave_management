from django.contrib import admin
from .models import (
    CircuitBreaker, MaintenanceRecord, MaintenanceAttachment, MaintenanceTemplate,
    EquipmentDetail, MaintenanceCheckItem, TestResult, MaintenanceTeamMember,
    SafetyPrecaution, InsulationResistanceTest, ContactResistanceTest, TimingTest,
    InterlockTest, ContactTravelTest, DuctorTest, ProtectionTest, RelayOperationTest,
    AutoRecloseTest, VacuumBreakerChecks, OilBreakerChecks, TransformerMaintenanceRecord,
    TransformerCheckItem
)

@admin.register(CircuitBreaker)
class CircuitBreakerAdmin(admin.ModelAdmin):
    list_display = ['breaker_number', 'breaker_type', 'sub_station', 'voltage_capacity', 'make_type', 'is_active']
    list_filter = ['breaker_type', 'voltage_capacity', 'is_active', 'region']
    search_fields = ['breaker_number', 'sub_station', 'make_type', 'serial_number']
    ordering = ['sub_station', 'breaker_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('breaker_number', 'breaker_type', 'make_type', 'voltage_capacity', 
                      'current_rating', 'breaking_capacity', 'serial_number')
        }),
        ('Location', {
            'fields': ('sub_station', 'bay_position', 'region')
        }),
        ('V/T Information', {
            'fields': ('vt_make_type', 'vt_volt_ratio_rating', 'vt_serial_no'),
            'classes': ('collapse',)
        }),
        ('C/T Information', {
            'fields': ('ct_make_type', 'ct_ratio', 'ct_serial_no'),
            'classes': ('collapse',)
        }),
        ('Administrative', {
            'fields': ('installation_date', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

class MaintenanceAttachmentInline(admin.TabularInline):
    model = MaintenanceAttachment
    extra = 1
    readonly_fields = ['uploaded_at']

class MaintenanceCheckItemInline(admin.TabularInline):
    model = MaintenanceCheckItem
    extra = 0
    ordering = ['category', 'order']

class TestResultInline(admin.TabularInline):
    model = TestResult
    extra = 0
    ordering = ['test_type', 'order']

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ['report_no', 'circuit_breaker', 'date', 'status', 'priority']
    list_filter = ['status', 'priority', 'date', 'circuit_breaker__breaker_type']
    search_fields = ['report_no', 'circuit_breaker__breaker_number', 'circuit_breaker__sub_station']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at', 'report_no']
    
    inlines = [MaintenanceCheckItemInline, TestResultInline, MaintenanceAttachmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('circuit_breaker', 'date', 'status', 'priority', 'report_no')
        }),
        ('Work Authorization', {
            'fields': ('permit_to_work_number', 'permit_issued_date', 'permit_expires_date',
                      'sanction_for_test_number', 'limitation_of_access_number'),
            'classes': ('collapse',)
        }),
        ('Operations Tracking', {
            'fields': ('operations_since_last_oh', 'operations_counter_last_oh', 
                      'operations_counter_to_date', 'previous_report_no', 'previous_report_date'),
            'classes': ('collapse',)
        }),
        ('Environmental Conditions', {
            'fields': ('weather_conditions', 'ambient_temperature', 'humidity', 
                      'environmental_considerations'),
            'classes': ('collapse',)
        }),
        ('Personnel', {
            'fields': ('maintenance_carried_out_by', 'protection_test_carried_out_by'),
        }),
        ('Approval Workflow', {
            'fields': ('checked_by', 'checked_by_role', 'checked_date',
                      'approved_by', 'approved_by_role', 'approved_date'),
            'classes': ('collapse',)
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_date', 'next_maintenance_due',
                      'maintenance_interval_months'),
            'classes': ('collapse',)
        }),
        ('Documentation', {
            'fields': ('remarks', 'recommendations')
        })
    )

@admin.register(InsulationResistanceTest)
class InsulationResistanceTestAdmin(admin.ModelAdmin):
    list_display = ['maintenance_record', 'phase', 'test_type', 'resistance_value', 'result_status']
    list_filter = ['phase', 'test_type', 'result_status']
    search_fields = ['maintenance_record__report_no']

@admin.register(ContactResistanceTest)
class ContactResistanceTestAdmin(admin.ModelAdmin):
    list_display = ['maintenance_record', 'phase', 'test_condition', 'resistance_microohms', 'result_status']
    list_filter = ['phase', 'test_condition', 'result_status']
    search_fields = ['maintenance_record__report_no']

@admin.register(TimingTest)
class TimingTestAdmin(admin.ModelAdmin):
    list_display = ['maintenance_record', 'phase', 'operation_type', 'result_status']
    list_filter = ['phase', 'operation_type', 'result_status']
    search_fields = ['maintenance_record__report_no']

@admin.register(VacuumBreakerChecks)
class VacuumBreakerChecksAdmin(admin.ModelAdmin):
    list_display = ['maintenance_record', 'vacuum_check_performed', 'contacts_condition']
    list_filter = ['vacuum_check_performed', 'contacts_condition']
    search_fields = ['maintenance_record__report_no']
    
    fieldsets = (
        ('Basic Checks', {
            'fields': ('gearing_checked', 'lubrication_checked', 'auxiliary_contacts_checked',
                      'motor_checked', 'springs_close_open_checked', 'cb_insulators_checked',
                      'cts_checked', 'porcelain_checked', 'local_remote_operation_checked')
        }),
        ('Vacuum System', {
            'fields': ('vacuum_check_performed', 'vacuum_level_satisfactory', 'contacts_condition')
        }),
        ('Ductor Tests', {
            'fields': ('red_phase_ductor', 'yellow_phase_ductor', 'blue_phase_ductor')
        }),
        ('Additional Tests', {
            'fields': ('timing_tests_attached', 'comments')
        })
    )

@admin.register(OilBreakerChecks)
class OilBreakerChecksAdmin(admin.ModelAdmin):
    list_display = ['maintenance_record', 'oil_condition', 'oil_analysis_required']
    list_filter = ['oil_condition', 'oil_analysis_required']
    search_fields = ['maintenance_record__report_no']
    
    fieldsets = (
        ('Oil System Checks', {
            'fields': ('oil_level_checked', 'oil_quality_checked', 'oil_leakage_checked',
                      'oil_condition')
        }),
        ('Oil Analysis', {
            'fields': ('oil_dielectric_strength', 'oil_moisture_content', 'oil_acidity',
                      'oil_analysis_required', 'oil_analysis_date', 'oil_analysis_results')
        }),
        ('Mechanical Checks', {
            'fields': ('contacts_inspection', 'arcing_contacts_condition',
                      'tank_condition', 'gasket_seals_condition')
        }),
        ('Comments', {
            'fields': ('comments',)
        })
    )

@admin.register(TransformerMaintenanceRecord)
class TransformerMaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ['report_no', 'transformer_number', 'substation', 'date', 'status']
    list_filter = ['status', 'date', 'substation']
    search_fields = ['report_no', 'transformer_number', 'substation', 'serial_no']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('substation', 'transformer_number', 'make_manufacturer',
                      'serial_no', 'rating_mva', 'voltage_ratio', 'year_of_manufacture')
        }),
        ('Administrative', {
            'fields': ('date', 'status', 'report_no')
        }),
        ('Personnel', {
            'fields': ('maintenance_carried_out_by', 'protection_test_carried_out_by',
                      'checked_by', 'engineer', 'ops_and_maint_engineer')
        }),
        ('Dates', {
            'fields': ('maintenance_date', 'protection_test_date', 'checked_date',
                      'engineer_date', 'ops_maint_date'),
            'classes': ('collapse',)
        }),
        ('Documentation', {
            'fields': ('remarks',)
        })
    )

# Register remaining models with simple admin
admin.site.register(MaintenanceAttachment)
admin.site.register(MaintenanceTemplate)
admin.site.register(EquipmentDetail)
admin.site.register(MaintenanceCheckItem)
admin.site.register(TestResult)
admin.site.register(MaintenanceTeamMember)
admin.site.register(SafetyPrecaution)
admin.site.register(InterlockTest)
admin.site.register(ContactTravelTest)
admin.site.register(DuctorTest)
admin.site.register(ProtectionTest)
admin.site.register(RelayOperationTest)
# admin.site.register(AutoRecloseTest)  # Temporarily commented out - model doesn't exist
admin.site.register(TransformerCheckItem)
