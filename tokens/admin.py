from django.contrib import admin
from .models import *

admin.site.register(Meter)
admin.site.register(Customer)
admin.site.register(Token)
admin.site.register(FaultMeter)
admin.site.register(RecoveredMeter)
admin.site.register(Reconnection)
admin.site.register(REIMBURSEMENT)
admin.site.register(CLEARCREDIT)
admin.site.register(TAMPERTOKEN)
admin.site.register(FaultMaintanance)
admin.site.register(OldToken)
