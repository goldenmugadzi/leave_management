from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import (
    FaultLocatorDevice, FaultLocatorTeam, Fault, FaultAssignment,
    FaultLocatorDeviceAssignment, TeamDeployment, FaultLocatorRole
)
from .serializers import (
    FaultLocatorDeviceSerializer, FaultLocatorTeamSerializer, FaultSerializer,
    FaultAssignmentSerializer, FaultLocatorDeviceAssignmentSerializer,
    TeamDeploymentSerializer, FaultLocatorRoleSerializer
)
from .api_permissions import (
    HasFaultLocatorRole, IsSeniorForeman, IsDepotForeperson,
    IsTeamLeader, IsTeamMember
)
from it.users.models import UserProfile, Depots

# Utility helpers

def get_user_role(user):
    role = user.fault_locator_roles.filter(is_active=True).order_by('-assigned_at').first()
    return role.role if role else None

class FaultLocatorDeviceViewSet(viewsets.ModelViewSet):
    queryset = FaultLocatorDevice.objects.all().order_by('-created_at')
    serializer_class = FaultLocatorDeviceSerializer
    permission_classes = [permissions.IsAuthenticated, HasFaultLocatorRole]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        if role == 'senior_foreman':
            return self.queryset
        if role == 'depot_foreperson':
            # Devices assigned to teams at user's depot or unassigned
            depot_code = getattr(user, 'depot', None).code if getattr(user, 'depot', None) else None
            if depot_code:
                team_ids = FaultLocatorTeam.objects.filter(current_depot__code=depot_code).values_list('id', flat=True)
                assigned_device_ids = FaultLocatorDeviceAssignment.objects.filter(team_id__in=team_ids).values_list('device_id', flat=True)
                return FaultLocatorDevice.objects.filter(Q(id__in=assigned_device_ids) | Q(status='available'))
            return FaultLocatorDevice.objects.none()
        # Team leader/member see only devices assigned to their active team
        assignments = FaultLocatorDeviceAssignment.objects.filter(team__members=user)
        return FaultLocatorDevice.objects.filter(id__in=assignments.values_list('device_id', flat=True))

class FaultLocatorTeamViewSet(viewsets.ModelViewSet):
    queryset = FaultLocatorTeam.objects.all().order_by('-created_at')
    serializer_class = FaultLocatorTeamSerializer
    permission_classes = [permissions.IsAuthenticated, HasFaultLocatorRole]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        if role == 'senior_foreman':
            return self.queryset
        if role == 'depot_foreperson':
            depot_code = getattr(user, 'depot', None).code if getattr(user, 'depot', None) else None
            return self.queryset.filter(current_depot__code=depot_code)
        if role == 'team_leader' or role == 'team_member':
            return self.queryset.filter(Q(team_leader=user) | Q(members=user)).distinct()
        return self.queryset.none()

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        try:
            member = UserProfile.objects.get(id=user_id)
            team.members.add(member)
            return Response({'status': 'member added'})
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        try:
            member = UserProfile.objects.get(id=user_id)
            team.members.remove(member)
            return Response({'status': 'member removed'})
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class FaultViewSet(viewsets.ModelViewSet):
    queryset = Fault.objects.all().order_by('-reported_at')
    serializer_class = FaultSerializer
    permission_classes = [permissions.IsAuthenticated, HasFaultLocatorRole]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        if role == 'senior_foreman':
            return self.queryset
        if role == 'depot_foreperson':
            depot_code = getattr(user, 'depot', None).code if getattr(user, 'depot', None) else None
            return self.queryset.filter(depot__code=depot_code)
        if role == 'team_leader' or role == 'team_member':
            # Faults assigned to their team or reported by them
            team_ids = FaultLocatorTeam.objects.filter(Q(team_leader=user) | Q(members=user)).values_list('id', flat=True)
            assignment_fault_ids = FaultAssignment.objects.filter(team_id__in=team_ids, located_at__isnull=True).values_list('fault_id', flat=True)
            return self.queryset.filter(Q(id__in=assignment_fault_ids) | Q(reported_by=user)).distinct()
        return self.queryset.none()

    @action(detail=True, methods=['post'])
    def prioritize(self, request, pk=None):
        fault = self.get_object()
        new_priority = request.data.get('priority')
        try:
            new_priority = int(new_priority)
            if new_priority < 1 or new_priority > 4:
                raise ValueError
        except (TypeError, ValueError):
            return Response({'error': 'Invalid priority'}, status=status.HTTP_400_BAD_REQUEST)
        fault.priority = new_priority
        fault.prioritized_by = request.user
        fault.prioritized_at = timezone.now()
        fault.save()
        return Response({'status': 'priority updated'})

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        fault = self.get_object()
        new_status = request.data.get('status')
        valid = dict(Fault._meta.get_field('status').choices).keys()
        if new_status not in valid:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        old_status = fault.status
        fault.status = new_status
        if new_status == 'located':
            # Mark assignment located
            assignment = FaultAssignment.objects.filter(fault=fault, located_at__isnull=True).first()
            if assignment:
                assignment.located_at = timezone.now()
                assignment.located_by = request.user
                assignment.save()
        fault.save()
        return Response({'status': 'status updated', 'old': old_status, 'new': new_status})

class FaultAssignmentViewSet(viewsets.ModelViewSet):
    queryset = FaultAssignment.objects.all().order_by('-assigned_at')
    serializer_class = FaultAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, HasFaultLocatorRole]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        if role == 'senior_foreman':
            return self.queryset
        if role == 'depot_foreperson':
            depot_code = getattr(user, 'depot', None).code if getattr(user, 'depot', None) else None
            return self.queryset.filter(fault__depot__code=depot_code)
        if role == 'team_leader' or role == 'team_member':
            team_ids = FaultLocatorTeam.objects.filter(Q(team_leader=user) | Q(members=user)).values_list('id', flat=True)
            return self.queryset.filter(team_id__in=team_ids)
        return self.queryset.none()

class DeviceAssignmentViewSet(viewsets.ModelViewSet):
    queryset = FaultLocatorDeviceAssignment.objects.all().order_by('-assigned_at')
    serializer_class = FaultLocatorDeviceAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, HasFaultLocatorRole]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        if role == 'senior_foreman':
            return self.queryset
        if role == 'depot_foreperson':
            depot_code = getattr(user, 'depot', None).code if getattr(user, 'depot', None) else None
            team_ids = FaultLocatorTeam.objects.filter(current_depot__code=depot_code).values_list('id', flat=True)
            return self.queryset.filter(team_id__in=team_ids)
        if role in ['team_leader', 'team_member']:
            team_ids = FaultLocatorTeam.objects.filter(Q(team_leader=user) | Q(members=user)).values_list('id', flat=True)
            return self.queryset.filter(team_id__in=team_ids)
        return self.queryset.none()

class TeamDeploymentViewSet(viewsets.ModelViewSet):
    queryset = TeamDeployment.objects.all().order_by('-deployed_at')
    serializer_class = TeamDeploymentSerializer
    permission_classes = [permissions.IsAuthenticated, HasFaultLocatorRole]

    def perform_create(self, serializer):
        serializer.save(deployed_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        if role == 'senior_foreman':
            return self.queryset
        if role == 'depot_foreperson':
            depot_code = getattr(user, 'depot', None).code if getattr(user, 'depot', None) else None
            return self.queryset.filter(depot__code=depot_code)
        if role in ['team_leader', 'team_member']:
            team_ids = FaultLocatorTeam.objects.filter(Q(team_leader=user) | Q(members=user)).values_list('id', flat=True)
            return self.queryset.filter(team_id__in=team_ids)
        return self.queryset.none()

    @action(detail=True, methods=['post'])
    def recall(self, request, pk=None):
        deployment = self.get_object()
        if deployment.recalled_at:
            return Response({'error': 'Already recalled'}, status=status.HTTP_400_BAD_REQUEST)
        deployment.recalled_at = timezone.now()
        deployment.recalled_by = request.user
        deployment.save()
        return Response({'status': 'team recalled'})

class FaultLocatorRoleViewSet(viewsets.ModelViewSet):
    queryset = FaultLocatorRole.objects.all().order_by('-assigned_at')
    serializer_class = FaultLocatorRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeniorForeman]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)