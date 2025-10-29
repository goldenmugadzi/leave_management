from django.contrib import admin
from .models import (
    Customer, Contractor, ApplicationAttachment, ClientApplication, 
    InspectionReport, E6Certificate, E1DefectReport, InspectionWorkflow, 
    ApplicationAssignment, InspectionPhoto
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'full_name', 'phone', 'email', 'district', 'created_at']
    list_filter = ['district', 'created_at']
    search_fields = ['customer_id', 'full_name', 'phone', 'email']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ['contractor_id', 'business_name', 'contact_person', 'phone', 'district', 'license_number']
    list_filter = ['district', 'created_at']
    search_fields = ['contractor_id', 'business_name', 'contact_person', 'license_number']
    readonly_fields = ['contractor_id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ApplicationAttachment)
class ApplicationAttachmentAdmin(admin.ModelAdmin):
    list_display = ['application', 'file_type', 'description', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['application__application_number', 'description']
    readonly_fields = ['uploaded_at']


class ApplicationAttachmentInline(admin.TabularInline):
    model = ApplicationAttachment
    extra = 1
    fields = ['file', 'file_type', 'description']


@admin.register(ClientApplication)
class ClientApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_number', 'customer', 'contractor', 'purpose', 
        'supply_type', 'status', 'submission_date'
    ]
    list_filter = [
        'application_type', 'purpose', 'supply_type', 'status', 
        'submission_date', 'created_at'
    ]
    search_fields = [
        'application_number', 'customer__full_name', 'customer__customer_id',
        'contractor__business_name', 'contractor__contractor_id'
    ]
    readonly_fields = ['application_number', 'created_at', 'updated_at']
    inlines = [ApplicationAttachmentInline]
    
    fieldsets = (
        ('Application Information', {
            'fields': ('application_number', 'application_type', 'priority', 'status')
        }),
        ('Customer Information', {
            'fields': ('customer', 'owner_name', 'owner_address')
        }),
        ('Contractor Information', {
            'fields': ('contractor',)
        }),
        ('Electrical Supply Details', {
            'fields': (
                'purpose', 'supply_type', 'roof_covering', 'single_phase_required',
                'single_phase_count', 'three_phase_required', 'three_phase_count',
                'service_feed_type', 'main_switch_size_amperes', 'main_switch_size_kva'
            )
        }),
        ('Submission Details', {
            'fields': ('submitted_by', 'submission_date', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(InspectionReport)
class InspectionReportAdmin(admin.ModelAdmin):
    list_display = [
        'service_no', 'consumer_name', 'inspection_date', 'status', 
        'inspector', 'created_at'
    ]
    list_filter = [
        'status', 'reason_for_inspection', 'inspection_date', 'created_at'
    ]
    search_fields = [
        'service_no', 'consumer_name', 'inspector__username'
    ]
    readonly_fields = ['status', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('service_no', 'inspection_date', 'reason_for_inspection', 'status')
        }),
        ('General Information (Items 1-3)', {
            'fields': (
                'consumer_name', 'property_supplied', 'property_owner_name',
                'property_owner_address', 'contractor', 'contractor_address'
            )
        }),
        ('Main Installation Details (Items 4-16)', {
            'fields': (
                'size_of_mains', 'size_of_mains_conduit', 'consumer_main_switch_type',
                'consumer_main_switch_capacity', 'consumer_main_switch_setting',
                'neutrals_fused', 'neutral_block_fitted', 'earth_electrode_installed',
                'earth_electrode_type', 'all_equipment_bonded_earthed',
                'insulation_resistance_between', 'insulation_resistance_to_earth',
                'earth_continuity_resistance', 'polarity_switches_plugs',
                'socket_outlets_earthed', 'socket_outlet_type', 'wiring_type',
                'circuit_conductors_correct_size', 'wiring_condition'
            )
        }),
        ('Specific Installation Aspects (Items 17-19)', {
            'fields': (
                'flexible_cord_prohibited_positions', 'bathroom_switch_accessible',
                'unearthed_metal_switches', 'conduits_bushed', 'conduits_bonded_earth',
                'conduits_correct_size', 'conduits_adequately_supported', 'conduits_suitable_type'
            )
        }),
        ('Circuit and Point Counts (Items 20-24)', {
            'fields': (
                'max_lighting_points_per_circuit', 'max_plug_points_per_circuit',
                'total_lighting_points', 'total_plug_points', 'appliances_wattages',
                'motors_plant_details'
            )
        }),
        ('Overhead Lines and Protection (Items 25-30)', {
            'fields': (
                'overhead_lines_height', 'overhead_lines_conductor_size',
                'overhead_lines_support', 'overhead_lines_general',
                'overhead_earthwires_fitted', 'overhead_lines_protected',
                'outbuildings_protected', 'motor_installations_protected',
                'commission_switch_details'
            )
        }),
        ('Final Status and Defects (Items 31-33)', {
            'fields': (
                'supply_connected_disconnected', 'contractor_notified_defects',
                'other_features_attention'
            )
        }),
        ('Relationships', {
            'fields': ('client_application', 'inspector')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(E6Certificate)
class E6CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'certificate_number', 'service_no', 'property_owner_occupant',
        'sent_to_client', 'sent_date', 'installation_inspector'
    ]
    list_filter = ['sent_to_client', 'sent_date', 'created_at']
    search_fields = [
        'certificate_number', 'service_no', 'property_owner_occupant'
    ]
    readonly_fields = ['certificate_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Certificate Information', {
            'fields': ('certificate_number', 'service_no')
        }),
        ('Installation Details', {
            'fields': ('installation_description', 'property_address', 'property_owner_occupant')
        }),
        ('Clearance Information', {
            'fields': ('minor_defects', 'defects_rectification_period')
        }),
        ('Electronic Delivery', {
            'fields': ('sent_to_client', 'sent_date', 'delivery_method')
        }),
        ('Relationships', {
            'fields': ('inspection_report', 'client_application', 'installation_inspector')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(E1DefectReport)
class E1DefectReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_number', 'service_no', 'property_address', 'is_reinspection',
        'sent_date', 'installation_inspector'
    ]
    list_filter = [
        'is_reinspection', 'sent_date', 'sent_to_consumer', 'sent_to_contractor',
        'created_at'
    ]
    search_fields = [
        'report_number', 'service_no', 'property_address'
    ]
    readonly_fields = ['report_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_number', 'service_no')
        }),
        ('Property Information', {
            'fields': ('property_address', 'sub_division_number')
        }),
        ('Defects Information', {
            'fields': ('defects_list', 'defects_requiring_attention')
        }),
        ('Distribution Information', {
            'fields': (
                'sent_to_consumer', 'sent_to_contractor', 'sent_to_district_manager',
                'sent_to_depot_official'
            )
        }),
        ('Electronic Delivery', {
            'fields': ('sent_date', 'delivery_method')
        }),
        ('Reinspection Information', {
            'fields': ('is_reinspection', 'original_report')
        }),
        ('Relationships', {
            'fields': ('inspection_report', 'client_application', 'installation_inspector')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(InspectionWorkflow)
class InspectionWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'workflow_number', 'client_application', 'status', 'current_step',
        'reinspection_count', 'created_at'
    ]
    list_filter = [
        'status', 'reinspection_count', 'created_at'
    ]
    search_fields = [
        'workflow_number', 'client_application__application_number'
    ]
    readonly_fields = ['workflow_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Workflow Information', {
            'fields': ('workflow_number', 'status', 'current_step', 'total_steps')
        }),
        ('Reinspection Tracking', {
            'fields': ('reinspection_count', 'max_reinspections')
        }),
        ('Relationships', {
            'fields': ('client_application', 'inspection_report', 'e6_certificate', 'e1_defect_report')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(ApplicationAssignment)
class ApplicationAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'application', 'assigned_to', 'assigned_by', 'status', 
        'assignment_date', 'due_date'
    ]
    list_filter = [
        'status', 'assignment_date', 'due_date', 'created_at'
    ]
    search_fields = [
        'application__application_number', 'assigned_to__username', 'assigned_by__username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('application', 'assigned_to', 'assigned_by')
        }),
        ('Assignment Details', {
            'fields': ('assignment_date', 'due_date', 'assignment_notes')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Acceptance/Completion', {
            'fields': ('accepted_date', 'completed_date', 'completion_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at'] 

@admin.register(InspectionPhoto)
class InspectionPhotoAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'inspection_report', 'timestamp', 'file_size', 
        'gps_latitude', 'gps_longitude', 'created_at'
    ]
    list_filter = ['timestamp', 'content_type', 'created_at']
    search_fields = [
        'filename', 'caption', 'inspection_report__service_no'
    ]
    readonly_fields = ['file_size', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('inspection_report', 'filename', 'file', 'caption', 'timestamp')
        }),
        ('Metadata', {
            'fields': ('content_type', 'file_size')
        }),
        ('GPS Coordinates', {
            'fields': ('gps_latitude', 'gps_longitude')
        }),
        ('Audit Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-timestamp']
