from rest_framework import serializers
from .models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory


class WeeklyCollectionsSerializer(serializers.ModelSerializer):
    """Serializer for WeeklyCollections model"""
    
    region_name = serializers.CharField(source='region.region', read_only=True)
    district_name = serializers.CharField(source='district.district', read_only=True)
    depot_name = serializers.CharField(source='depot.depot', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = WeeklyCollections
        fields = [
            'id', 'week', 'year', 'week_number', 'zwl_millions', 'usd_millions',
            'region', 'district', 'depot', 'region_name', 'district_name', 'depot_name',
            'created_at', 'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def validate(self, data):
        """Custom validation for weekly collections data"""
        # Ensure at least one location field is set
        if not any([data.get('region'), data.get('district'), data.get('depot')]):
            raise serializers.ValidationError(
                "At least one location field (region, district, or depot) must be set."
            )
        
        # Validate week format
        week = data.get('week', '')
        if not week.startswith('Week '):
            raise serializers.ValidationError(
                "Week must start with 'Week ' followed by a number."
            )
        
        return data


class WeeklyRevenueLostSerializer(serializers.ModelSerializer):
    """Serializer for WeeklyRevenueLost model"""
    
    region_name = serializers.CharField(source='region.region', read_only=True)
    district_name = serializers.CharField(source='district.district', read_only=True)
    depot_name = serializers.CharField(source='depot.depot', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = WeeklyRevenueLost
        fields = [
            'id', 'week', 'year', 'week_number', 'faults_mwh', 'maintenance_mwh', 'total_mwh',
            'region', 'district', 'depot', 'region_name', 'district_name', 'depot_name',
            'created_at', 'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by', 'total_mwh']
    
    def validate(self, data):
        """Custom validation for weekly revenue lost data"""
        # Ensure at least one location field is set
        if not any([data.get('region'), data.get('district'), data.get('depot')]):
            raise serializers.ValidationError(
                "At least one location field (region, district, or depot) must be set."
            )
        
        # Validate week format
        week = data.get('week', '')
        if not week.startswith('Week '):
            raise serializers.ValidationError(
                "Week must start with 'Week ' followed by a number."
            )
        
        # Validate that MWh values are non-negative
        faults_mwh = data.get('faults_mwh', 0)
        maintenance_mwh = data.get('maintenance_mwh', 0)
        
        if faults_mwh < 0:
            raise serializers.ValidationError("Faults MWh cannot be negative.")
        
        if maintenance_mwh < 0:
            raise serializers.ValidationError("Maintenance MWh cannot be negative.")
        
        return data


class DebtorCategorySerializer(serializers.ModelSerializer):
    """Serializer for DebtorCategory model"""
    
    region_name = serializers.CharField(source='region.region', read_only=True)
    district_name = serializers.CharField(source='district.district', read_only=True)
    depot_name = serializers.CharField(source='depot.depot', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = DebtorCategory
        fields = [
            'id', 'category', 'category_display', 'percentage', 'year', 'month',
            'region', 'district', 'depot', 'region_name', 'district_name', 'depot_name',
            'created_at', 'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def validate(self, data):
        """Custom validation for debtor category data"""
        # Ensure at least one location field is set
        if not any([data.get('region'), data.get('district'), data.get('depot')]):
            raise serializers.ValidationError(
                "At least one location field (region, district, or depot) must be set."
            )
        
        # Validate percentage range
        percentage = data.get('percentage', 0)
        if percentage < 0 or percentage > 100:
            raise serializers.ValidationError(
                "Percentage must be between 0 and 100."
            )
        
        # Validate month range
        month = data.get('month', 1)
        if month < 1 or month > 12:
            raise serializers.ValidationError(
                "Month must be between 1 and 12."
            )
        
        return data


class DashboardDataSerializer(serializers.Serializer):
    """Serializer for complete dashboard data response"""
    
    weekly_collections = WeeklyCollectionsSerializer(many=True, read_only=True)
    weekly_revenue_lost = WeeklyRevenueLostSerializer(many=True, read_only=True)
    debtors = DebtorCategorySerializer(many=True, read_only=True)
    
    # Include other existing dashboard data fields
    pbncs = serializers.ListField(read_only=True)
    weekly_sales = serializers.ListField(read_only=True)
    upos = serializers.ListField(read_only=True)
    weekly_outages = serializers.ListField(read_only=True)
    tds = serializers.ListField(read_only=True)
    weekly_faults_maintenance = serializers.ListField(read_only=True)
    
    # Metrics data
    metrics = serializers.DictField(read_only=True)
    
    # Chart data
    inspection_locations = serializers.CharField(read_only=True)
    inspections_count = serializers.CharField(read_only=True)
    maintenance_locations = serializers.CharField(read_only=True)
    maintenance_count = serializers.CharField(read_only=True)
    mnt = serializers.DictField(read_only=True)
