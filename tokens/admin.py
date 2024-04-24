from django.contrib import admin
from .models import  Meter, Customer, Token, Fault, Reconnection, Recover

admin.site.register(Meter)
admin.site.register(Customer)
admin.site.register(Token)
admin.site.register(Fault)
admin.site.register(Reconnection)
admin.site.register(Recover)
