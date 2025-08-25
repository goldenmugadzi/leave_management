from django.urls import path, includefrom django.urls import path, include

from rest_framework.routers import DefaultRouter

from fault_locator.api import (urlpatterns = [

    FaultLocatorDeviceViewSet, FaultLocatorTeamViewSet, FaultViewSet,    path('ace/', include('ACE2.urls')),

    FaultAssignmentViewSet, FaultLocatorDeviceAssignmentViewSet,    path('pettycash/', include('finance.PettyCash.urls')),

    TeamDeploymentViewSet, FaultLocatorRoleViewSet]

)

router = DefaultRouter()
router.register(r'devices', FaultLocatorDeviceViewSet, basename='fl-device')
router.register(r'teams', FaultLocatorTeamViewSet, basename='fl-team')
router.register(r'faults', FaultViewSet, basename='fl-fault')
router.register(r'assignments', FaultAssignmentViewSet, basename='fl-assignment')
router.register(r'device-assignments', FaultLocatorDeviceAssignmentViewSet, basename='fl-device-assignment')
router.register(r'deployments', TeamDeploymentViewSet, basename='fl-deployment')
router.register(r'roles', FaultLocatorRoleViewSet, basename='fl-role')

urlpatterns = [
    path('api/fault-locator/', include(router.urls)),
]
