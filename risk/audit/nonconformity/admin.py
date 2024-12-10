
# Register your models here.
from django.contrib import admin
from .models import *

@admin.register(Nonconformity)
class NonconformityAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'recipient', 'description', 'violation_standard_reference', 'created_at',  )

@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'description', 'maintained_info', 'retained_info', )
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
@admin.register(Acceptance)
class AcceptanceAdmin(admin.ModelAdmin):
    list_display = ('nonconformity', 'cause', 'corrective_action', 'dated', 'expected_completion_date', )
@admin.register(Rejection)
class RejectionAdmin(admin.ModelAdmin):
    list_display = ('nonconformity', 'rejection_reason', 'dated', )    
@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', )
@admin.register(RejectionAttachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', )
@admin.register(AcceptanceAttachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', )
@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('id', )