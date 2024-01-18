from django.contrib import admin
from .models import KnowledgeCenter, Secondary_Category,First_Category,Filetype,Categories
# Register your models here.
admin.site.register(KnowledgeCenter)
admin.site.register(Filetype)
admin.site.register(Secondary_Category)
admin.site.register(First_Category)
admin.site.register(Categories)