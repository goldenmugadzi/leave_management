from django.db import models

from it.users.models import CostCenter, Depots, Designations, Districts, Regions, Roles, Sections, UserProfile

# Create your models here.
class NewProfile(models.Model):
    username = models.CharField(max_length=15, unique=True, verbose_name='EC Number',db_index=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.DO_NOTHING, blank=True, null=True)
    roles = models.ManyToManyField(Roles, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username

class ProfileChange(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    application = models.CharField(max_length=100, null=True, blank=True, default=None)
    role_to_assign = models.ManyToManyField(Roles, related_name='role_to_assign', null=True, blank=True, default=None)
    role_to_remove = models.ManyToManyField(Roles, related_name='role_to_remove', null=True, blank=True, default=None)
    change_date = models.DateTimeField()
    changed_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='changed_by')

    def __str__(self):
        return self.user

    class Meta:
        app_label = 'change_requests'
        
class ProfileDeactivation(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    application = models.CharField(max_length=100, null=True, blank=True, default=None)
    deactivation_date = models.DateTimeField()
    deactivated_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='deactivated_by')

    def __str__(self):
        return self.user

    class Meta:
        app_label = 'change_requests'

class ChangeRequest(models.Model):
    cr_id = models.CharField(max_length=100, primary_key=True)
    change_type = models.CharField(max_length=100)
    new_profile = models.ForeignKey(NewProfile, on_delete=models.CASCADE, null=True, blank=True)
    profile_change = models.ForeignKey(ProfileChange, on_delete=models.CASCADE, null=True, blank=True)
    profile_deactivation = models.ForeignKey(ProfileDeactivation, on_delete=models.CASCADE, null=True, blank=True)
    change_description = models.TextField(null=True, blank=True)
    change_reason = models.TextField(null=True, blank=True)
    creator_designation = models.ForeignKey(Designations, on_delete=models.CASCADE, related_name='cr_creator_designation')
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cr_created_by')
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.cr_id

    class Meta:
        app_label = 'change_requests'
        
class CRApproval(models.Model):
    cr_id = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE)
    approver = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    approver_role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    approval_status = models.BooleanField()
    comment = models.TextField(null=True, blank=True)
    approval_date = models.DateTimeField()
    
    def __str__(self):
        return self.cr_id

    class Meta:
        app_label = 'change_requests'