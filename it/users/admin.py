from django.contrib import admin
from .models import *
@admin.register(Districts)
class DistrictsAdmin(admin.ModelAdmin):
    list_display = ('district', 'region_id')

@admin.register(Sections)
class SectionsAdmin(admin.ModelAdmin):
    list_display = ('section', 'code', 'district_id')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display =('username', 'designation', 'section', 'depot', 'region', 'district', 'status', ) 
    
@admin.register(Depots)
class DepotsAdmin(admin.ModelAdmin):
    list_display = ('depot', 'code', 'district_id', 'region_id', )

@admin.register(Regions)
class RegionsAdmin(admin.ModelAdmin):
    list_display = ('region', 'code', )

@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ('role', 'name', 'description', 'application', )

@admin.register(Designations)
class DesignationsAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'description', )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read')

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent')

@admin.register(Responsibilities)
class ResponsibilitiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'get_app_name','user')

    def get_app_name(self, obj):
        return obj.role.app_id.name if obj.role and obj.role.app_id else 'No App'
    get_app_name.short_description = 'App Name'
    
admin.site.register(UserQualification)
admin.site.register(UserExperience)