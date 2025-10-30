"""
Serializers for Inspection Sync API endpoints
Formats data according to BACKEND_API_REQUIREMENTS.md specification
"""

from rest_framework import serializers
from .models import InspectionReport, E1DefectReport, E6Certificate, InspectionPhoto


class InspectionPhotoSerializer(serializers.ModelSerializer):
    """
    Serializer for inspection photos
    """
    url = serializers.SerializerMethodField()
    gps_coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = InspectionPhoto
        fields = [
            'id', 'filename', 'url', 'caption', 'timestamp', 
            'gps_coordinates', 'content_type', 'file_size'
        ]
    
    def get_url(self, obj):
        """Get full URL for photo file"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_gps_coordinates(self, obj):
        """Format GPS coordinates as object"""
        if obj.gps_latitude is not None and obj.gps_longitude is not None:
            return {
                'latitude': float(obj.gps_latitude),
                'longitude': float(obj.gps_longitude)
            }
        return None


class InspectionReportSyncSerializer(serializers.ModelSerializer):
    """
    Serializer for E117 Inspection Reports
    Formats according to sync API specification
    """
    consumer_main_switch = serializers.SerializerMethodField()
    server_updated_at = serializers.DateTimeField(source='updated_at', required=False, allow_null=True)
    
    class Meta:
        model = InspectionReport
        fields = [
            # Basic Information
            'id',
            'service_no',
            'inspection_date',
            'reason_for_inspection',
            'status',
            'server_updated_at',
            
            # Items 1-3: General Information
            'consumer_name',
            'property_supplied',
            'property_owner_name',
            'property_owner_address',
            'contractor',
            'contractor_address',
            
            # Items 4-5: Main Installation Details
            'size_of_mains',
            'size_of_mains_conduit',
            'consumer_main_switch',
            
            # Items 6-8: Neutral, Earthing, Bonding
            'neutrals_fused',
            'neutral_block_fitted',
            'earth_electrode_installed',
            'earth_electrode_type',
            'all_equipment_bonded_earthed',
            
            # Items 9-10: Resistance Tests
            'insulation_resistance_between',
            'insulation_resistance_to_earth',
            'earth_continuity_resistance',
            
            # Items 11-13: Polarity & Socket Outlets
            'polarity_switches_plugs',
            'socket_outlets_earthed',
            'socket_outlet_type',
            
            # Items 14-16: Wiring Details (PREVIOUSLY MISSING)
            'wiring_type',
            'circuit_conductors_correct_size',
            'wiring_condition',
            
            # Items 17-18: Specific Installation Aspects (PREVIOUSLY MISSING)
            'flexible_cord_prohibited_positions',
            'bathroom_switch_accessible',
            'unearthed_metal_switches',
            
            # Item 19: Conduits (PREVIOUSLY MISSING)
            'conduits_bushed',
            'conduits_bonded_earth',
            'conduits_correct_size',
            'conduits_adequately_supported',
            'conduits_suitable_type',
            
            # Items 20-24: Circuit Counts (PREVIOUSLY MISSING)
            'max_lighting_points_per_circuit',
            'max_plug_points_per_circuit',
            'total_lighting_points',
            'total_plug_points',
            'appliances_wattages',
            'motors_plant_details',
            
            # Items 25-27: Overhead Lines (PREVIOUSLY MISSING)
            'overhead_lines_height',
            'overhead_lines_conductor_size',
            'overhead_lines_support',
            'overhead_lines_general',
            'overhead_earthwires_fitted',
            'overhead_lines_protected',
            
            # Items 28-30: Protection & Commission (PREVIOUSLY MISSING)
            'outbuildings_protected',
            'motor_installations_protected',
            'commission_switch_details',
            
            # Items 31-33: Final Status (PREVIOUSLY MISSING)
            'supply_connected_disconnected',
            'contractor_notified_defects',
            'other_features_attention',
            
            # Defects tracking
            'defects_count',
        ]
    
    def get_consumer_main_switch(self, obj):
        """Format consumer main switch as object"""
        return {
            'type': obj.consumer_main_switch_type or '',
            'capacity': obj.consumer_main_switch_capacity or '',
            'setting': obj.consumer_main_switch_setting or ''
        }
    
    def to_representation(self, instance):
        """Convert field names to match mobile app format"""
        data = super().to_representation(instance)
        
        # Rename fields to match API spec
        field_mapping = {
            'size_of_mains': 'mains_size',
            'size_of_mains_conduit': 'mains_conduit_size',
            'contractor': 'contractor_name',
            'contractor_address': 'contractor_address',
            'all_equipment_bonded_earthed': 'switches_bonded_earthed',
            'insulation_resistance_between': 'installation_resistance_between_phases',
            'insulation_resistance_to_earth': 'installation_resistance_to_earth',
            'polarity_switches_plugs': 'polarity_test_result',
            'status': 'inspection_result',
            'service_no': 'service_number',
        }
        
        # Apply mappings
        mapped_data = {}
        for old_key, new_key in field_mapping.items():
            if old_key in data:
                mapped_data[new_key] = data[old_key]
        
        # Keep unmapped fields
        for key, value in data.items():
            if key not in field_mapping:
                mapped_data[key] = value
        
        # Add inspector information (placeholder - would need to get from relationship)
        mapped_data['inspector_name'] = ''
        mapped_data['inspector_designation'] = ''
        mapped_data['inspector_signature'] = ''
        
        return mapped_data


class E1DefectReportSyncSerializer(serializers.ModelSerializer):
    """
    Serializer for E1 Defect Reports
    Formats according to sync API specification
    """
    inspection_id = serializers.UUIDField(source='inspection_report.id', read_only=True)
    inspection_result = serializers.SerializerMethodField()
    defects_requiring_attention = serializers.SerializerMethodField()
    official_signature = serializers.SerializerMethodField()
    inspector_designation = serializers.SerializerMethodField()
    reference_number = serializers.CharField(source='report_number')
    stand_plot_location = serializers.SerializerMethodField()
    sub_div_number = serializers.CharField(source='sub_division_number')
    farm_mine_location = serializers.SerializerMethodField()
    district_township = serializers.SerializerMethodField()
    inspection_date = serializers.DateTimeField(source='inspection_report.inspection_date', read_only=True)
    reinspection_required = serializers.SerializerMethodField()
    reinspection_fee = serializers.SerializerMethodField()
    rectification_period_days = serializers.SerializerMethodField()
    
    class Meta:
        model = E1DefectReport
        fields = [
            'id',
            'inspection_id',
            'stand_plot_location',
            'sub_div_number',
            'farm_mine_location',
            'district_township',
            'inspection_date',
            'inspection_result',
            'defects_requiring_attention',
            'reinspection_required',
            'reinspection_fee',
            'rectification_period_days',
            'official_signature',
            'inspector_designation',
            'reference_number',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_inspection_result(self, obj):
        """Get inspection result - E1 means failed"""
        return 'failed'
    
    def get_defects_requiring_attention(self, obj):
        """Parse defects list as array of objects"""
        if obj.defects_requiring_attention:
            # Simple parsing - in real scenario might be JSON
            defects = []
            for line in obj.defects_requiring_attention.split('\n'):
                if line.strip():
                    defects.append({
                        'description': line.strip(),
                        'location': '',
                        'severity': 'medium'
                    })
            return defects
        return []
    
    def get_official_signature(self, obj):
        """Get inspector signature (placeholder)"""
        return ''
    
    def get_inspector_designation(self, obj):
        """Get inspector designation"""
        if obj.installation_inspector:
            return getattr(obj.installation_inspector, 'job_title', 'Inspector')
        return 'Inspector'
    
    def get_stand_plot_location(self, obj):
        """Get property address"""
        return obj.property_address or ''
    
    def get_farm_mine_location(self, obj):
        """Get farm/mine location (placeholder)"""
        return ''
    
    def get_district_township(self, obj):
        """Get district (placeholder)"""
        return ''
    
    def get_reinspection_required(self, obj):
        """Determine if reinspection is required"""
        return not obj.is_reinspection
    
    def get_reinspection_fee(self, obj):
        """Get reinspection fee (placeholder)"""
        return 50.00
    
    def get_rectification_period_days(self, obj):
        """Get rectification period (default 14 days)"""
        return 14


class E6CertificateSyncSerializer(serializers.ModelSerializer):
    """
    Serializer for E6 Certificates
    Formats according to sync API specification
    """
    inspection_id = serializers.UUIDField(source='inspection_report.id', read_only=True)
    service_number = serializers.CharField(source='service_no')
    property_details = serializers.CharField(source='property_address')
    owner_occupier = serializers.CharField(source='property_owner_occupant')
    inspection_completed = serializers.SerializerMethodField()
    connection_approved = serializers.SerializerMethodField()
    minor_defects = serializers.SerializerMethodField()
    rectification_period_days = serializers.IntegerField(source='defects_rectification_period')
    inspector_name = serializers.SerializerMethodField()
    inspection_date = serializers.DateTimeField(source='inspection_report.inspection_date', read_only=True)
    certificate_issued_date = serializers.DateTimeField(source='created_at')
    inspector_signature = serializers.SerializerMethodField()
    
    class Meta:
        model = E6Certificate
        fields = [
            'id',
            'inspection_id',
            'service_number',
            'installation_description',
            'property_details',
            'owner_occupier',
            'inspection_completed',
            'connection_approved',
            'minor_defects',
            'rectification_period_days',
            'inspector_name',
            'inspection_date',
            'certificate_issued_date',
            'inspector_signature',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_inspection_completed(self, obj):
        """Check if inspection is completed"""
        return True
    
    def get_connection_approved(self, obj):
        """Check if connection is approved - E6 means passed"""
        return True
    
    def get_minor_defects(self, obj):
        """Parse minor defects as array"""
        if obj.minor_defects:
            return [defect.strip() for defect in obj.minor_defects.split('\n') if defect.strip()]
        return []
    
    def get_inspector_name(self, obj):
        """Get inspector name"""
        if obj.installation_inspector:
            return obj.installation_inspector.get_full_name() or obj.installation_inspector.username
        return ''
    
    def get_inspector_signature(self, obj):
        """Get inspector signature (placeholder for base64 encoded signature)"""
        return ''


class DefectSerializer(serializers.Serializer):
    """
    Serializer for general defects extracted from E1 reports
    """
    id = serializers.UUIDField()
    inspection_id = serializers.UUIDField()
    inspection_type = serializers.CharField(default='e117')
    defect_description = serializers.CharField()
    defect_category = serializers.CharField()
    severity = serializers.CharField()
    rectification_required = serializers.CharField()
    compliance_standard = serializers.CharField()
    status = serializers.CharField()
    rectification_date = serializers.DateTimeField(allow_null=True)
    verification_date = serializers.DateTimeField(allow_null=True)
    photos = serializers.ListField(child=serializers.CharField())
    notes = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

