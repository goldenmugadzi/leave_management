
# Register your models here.
from django.contrib import admin
from .models import *

@admin.register(Nonconformity)
class NonconformityAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'recipient', 'description', 'violation_standard_reference', 'recommended_corrective_action', 'created_at', 'attachment', )
@admin.register(Response)
class Response(admin.ModelAdmin):
    list_display =('user', 'nonconformity', 'comment', 'created_at', 'status', )
@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('clause', 'id', 'description', 'maintained_info', 'retained_info', )
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    
