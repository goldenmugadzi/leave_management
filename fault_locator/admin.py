from django.contrib import admin
from .models import Depot,FaultLocatorDevice,DeviceAssignment

admin.site.register(Depot)
admin.site.register(FaultLocatorDevice)
admin.site.register(DeviceAssignment)
