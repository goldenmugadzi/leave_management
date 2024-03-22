from django.contrib import admin
from .models import MeterType, Meter, Customer, TemperToken, Fault, Reconnection, Recover

admin.site.register(MeterType)
admin.site.register(Meter)
admin.site.register(Customer)
admin.site.register(TemperToken)
admin.site.register(Fault)
admin.site.register(Reconnection)
admin.site.register(Recover)
