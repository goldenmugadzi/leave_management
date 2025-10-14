from rest_framework import permissions
from .models import FaultLocatorRole

class HasFaultLocatorRole(permissions.BasePermission):
    message = "You do not have an active fault locator role"

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.fault_locator_roles.filter(is_active=True).exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsSeniorForeman(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.fault_locator_roles.filter(role='senior_foreman', is_active=True).exists()

class IsDepotForeperson(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.fault_locator_roles.filter(role='depot_foreperson', is_active=True).exists()

class IsTeamLeader(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.fault_locator_roles.filter(role='team_leader', is_active=True).exists()

class IsTeamMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.fault_locator_roles.filter(role='team_member', is_active=True).exists()
