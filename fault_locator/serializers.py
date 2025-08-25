from rest_framework import serializers
from .models import (
    FaultLocatorDevice, FaultLocatorTeam, Fault, FaultAssignment,
    FaultLocatorDeviceAssignment, TeamDeployment, FaultLocatorRole
)
from it.users.models import UserProfile, Depots

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'email']

class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depots
        fields = ['id', 'code', 'depot', 'region']

class FaultLocatorDeviceSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = FaultLocatorDevice
        fields = ['id', 'serial_number', 'description', 'status', 'created_at', 'created_by']
        read_only_fields = ['id', 'status', 'created_at', 'created_by']

class FaultLocatorTeamSerializer(serializers.ModelSerializer):
    team_leader = UserMiniSerializer(read_only=True)
    members = UserMiniSerializer(many=True, read_only=True)
    current_depot = DepotSerializer(read_only=True)

    class Meta:
        model = FaultLocatorTeam
        fields = ['id', 'name', 'team_leader', 'members', 'current_depot', 'assigned_at', 'assigned_by', 'created_at', 'created_by']
        read_only_fields = ['assigned_at', 'assigned_by', 'created_at', 'created_by']

class FaultSerializer(serializers.ModelSerializer):
    depot = DepotSerializer(read_only=True)
    depot_id = serializers.PrimaryKeyRelatedField(queryset=Depots.objects.all(), source='depot', write_only=True)
    reported_by = UserMiniSerializer(read_only=True)
    prioritized_by = UserMiniSerializer(read_only=True)
    verified_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Fault
        fields = [
            'id','description','depot','depot_id','reported_at','reported_by','status','priority',
            'prioritized_by','prioritized_at','voltage','backfeed','clients_affected','vvip',
            'foreperson_notes','team_leader_notes','location_details','verified_by','verified_at'
        ]
        read_only_fields = ['reported_at','reported_by','prioritized_by','prioritized_at','verified_by','verified_at']

class FaultAssignmentSerializer(serializers.ModelSerializer):
    fault = FaultSerializer(read_only=True)
    fault_id = serializers.PrimaryKeyRelatedField(queryset=Fault.objects.all(), source='fault', write_only=True)
    team = FaultLocatorTeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(queryset=FaultLocatorTeam.objects.all(), source='team', write_only=True)
    device = FaultLocatorDeviceSerializer(read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(queryset=FaultLocatorDevice.objects.all(), source='device', write_only=True)
    assigned_by = UserMiniSerializer(read_only=True)
    located_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = FaultAssignment
        fields = ['id','fault','fault_id','team','team_id','device','device_id','assigned_at','assigned_by','located_at','located_by','work_started_at','estimated_completion','actual_completion','work_notes']
        read_only_fields = ['assigned_at','assigned_by','located_at','located_by']

class FaultLocatorDeviceAssignmentSerializer(serializers.ModelSerializer):
    device = FaultLocatorDeviceSerializer(read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(queryset=FaultLocatorDevice.objects.all(), source='device', write_only=True)
    team = FaultLocatorTeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(queryset=FaultLocatorTeam.objects.all(), source='team', write_only=True)
    assigned_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = FaultLocatorDeviceAssignment
        fields = ['id','device','device_id','team','team_id','assigned_at','assigned_by','notes']
        read_only_fields = ['assigned_at','assigned_by']

class TeamDeploymentSerializer(serializers.ModelSerializer):
    team = FaultLocatorTeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(queryset=FaultLocatorTeam.objects.all(), source='team', write_only=True)
    depot = DepotSerializer(read_only=True)
    depot_id = serializers.PrimaryKeyRelatedField(queryset=Depots.objects.all(), source='depot', write_only=True)
    deployed_by = UserMiniSerializer(read_only=True)
    recalled_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = TeamDeployment
        fields = ['id','team','team_id','depot','depot_id','deployed_by','deployed_at','recalled_at','recalled_by','deployment_notes','recall_notes']
        read_only_fields = ['deployed_at','deployed_by','recalled_at','recalled_by']

class FaultLocatorRoleSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), source='user', write_only=True)
    depot = DepotSerializer(read_only=True)
    depot_id = serializers.PrimaryKeyRelatedField(queryset=Depots.objects.all(), source='depot', write_only=True, allow_null=True, required=False)

    class Meta:
        model = FaultLocatorRole
        fields = ['id','user','user_id','role','depot','depot_id','assigned_at','assigned_by','is_active']
        read_only_fields = ['assigned_at','assigned_by']
