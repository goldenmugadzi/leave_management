from rest_framework import routers
from django.urls import path, include
from .api import (
    FaultLocatorDeviceViewSet, FaultLocatorTeamViewSet, FaultViewSet,
    FaultAssignmentViewSet, DeviceAssignmentViewSet, TeamDeploymentViewSet,
    FaultLocatorRoleViewSet
)

router = routers.DefaultRouter()
router.register(r'devices', FaultLocatorDeviceViewSet, basename='fl-device')
router.register(r'teams', FaultLocatorTeamViewSet, basename='fl-team')
router.register(r'faults', FaultViewSet, basename='fl-fault')
router.register(r'assignments', FaultAssignmentViewSet, basename='fl-assignment')
router.register(r'device-assignments', DeviceAssignmentViewSet, basename='fl-device-assignment')
router.register(r'deployments', TeamDeploymentViewSet, basename='fl-deployment')
router.register(r'roles', FaultLocatorRoleViewSet, basename='fl-role')

urlpatterns = [
    path('', include(router.urls)),
]
