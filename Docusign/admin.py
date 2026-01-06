from django.contrib import admin
from .models import Document, Signature, Request, PossibleSigner, Sign, Initial
# Register your models here.

admin.site.register(Document)
admin.site.register(Signature)
admin.site.register(Request)
admin.site.register(PossibleSigner)
admin.site.register(Sign)
admin.site.register(Initial)
