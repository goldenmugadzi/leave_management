from django.db import models
from django.utils import timezone

from it.users.models import CostCenter, Depots, Designations, Districts, Regions, Responsibilities, Roles, Sections, UserProfile

# Create your models here.
class NewProfile(models.Model):
    username = models.CharField(max_length=15, blank=True, null=True)
    ec_number = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    company = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.DO_NOTHING, blank=True, null=True)
    depot_office = models.CharField(max_length=150, blank=True, null=True)
    sub_module = models.CharField(max_length=150, blank=True, null=True)
    roles_to_action = models.CharField(max_length=300, null=True, blank=True, default=None)
    roles_actions = models.CharField(max_length=300, null=True, blank=True, default=None)
    roles = models.ManyToManyField(Roles, blank=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    training_date = models.DateField(blank=True, null=True)
    training_confirmation_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username

class ProfileChange(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('IMPLEMENTED', 'Implemented'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    current_user_id = models.CharField(max_length=30, blank=True, null=True)
    ec_number = models.CharField(max_length=20, blank=True, null=True)
    application = models.CharField(max_length=100, null=True, blank=True, default=None)
    roles_to_action = models.CharField(max_length=300, null=True, blank=True, default=None)
    roles_actions = models.CharField(max_length=300, null=True, blank=True, default=None)
    role_to_assign = models.ManyToManyField(Roles, related_name='role_to_assign', blank=True, default=None)
    role_to_remove = models.ManyToManyField(Roles, related_name='role_to_remove', blank=True, default=None)
    reason_assign = models.TextField(blank=True, null=True)
    reason_remove = models.TextField(blank=True, null=True)
    correspondence_link = models.URLField(max_length=500, blank=True, null=True)
    change_date = models.DateTimeField()
    changed_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='changed_by')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return self.user

    class Meta:
        app_label = 'change_requests'
        
class ProfileDeactivation(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    application = models.CharField(max_length=100, null=True, blank=True, default=None)
    deactivation_date = models.DateTimeField()
    effective_start_date = models.DateTimeField(blank=True, null=True)
    reactivation_date = models.DateTimeField(blank=True, null=True)
    deactivation_reason = models.TextField(blank=True, null=True)
    correspondence_link = models.URLField(max_length=500, blank=True, null=True)
    deactivated_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='deactivated_by')

    def __str__(self):
        return self.user

    class Meta:
        app_label = 'change_requests'

class ChangeRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('IMPLEMENTED', 'Implemented'),
    ]
    
    cr_id = models.CharField(max_length=100, primary_key=True)
    application = models.CharField(max_length=100, null=True, blank=True, default=None)
    change_type = models.CharField(max_length=100)
    new_profile = models.ForeignKey(NewProfile, on_delete=models.CASCADE, null=True, blank=True)
    profile_change = models.ForeignKey(ProfileChange, on_delete=models.CASCADE, null=True, blank=True)
    profile_deactivation = models.ForeignKey(ProfileDeactivation, on_delete=models.CASCADE, null=True, blank=True)
    change_description = models.TextField(null=True, blank=True)
    change_reason = models.TextField(null=True, blank=True)
    originator_company = models.CharField(max_length=150, null=True, blank=True)
    originator_site = models.CharField(max_length=150, null=True, blank=True)
    date_resolution_required = models.DateField(null=True, blank=True)
    creator_designation = models.ForeignKey(Designations, on_delete=models.CASCADE, related_name='cr_creator_designation')
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cr_created_by')
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_change_requests')
    
    def __str__(self):
        return self.cr_id
    
    def soft_delete(self, user):
        """Soft delete the change request"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
    
    def restore(self):
        """Restore the change request"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    @property
    def overall_status(self):
        """
        Get overall approval status based on section head and IT approvals.
        Returns standardized status string for consistent handling.
        """
        sh_approval = self.crapproval_set.filter(approver_role__role="section_head").first()
        it_approval = self.crapproval_set.filter(approver_role__role="it_section_head").first()
        
        if not sh_approval:
            return "pending_sh"
        elif sh_approval.approval_status == False:
            return "rejected_sh"
        elif not it_approval:
            return "pending_it"
        elif it_approval.approval_status == False:
            return "rejected_it"
        else:
            return "approved_complete"
    
    @property
    def status_display(self):
        """
        Get human-readable status for display purposes.
        """
        status_map = {
            "pending_sh": "Pending Section Head",
            "rejected_sh": "Rejected by Section Head", 
            "pending_it": "Pending IT",
            "rejected_it": "Rejected by IT",
            "approved_complete": "Complete"
        }
        return status_map.get(self.overall_status, "Unknown")
    
    @property
    def status_color_class(self):
        """
        Get CSS class for status badge styling.
        """
        color_map = {
            "pending_sh": "bg-yellow-100 text-yellow-800",
            "rejected_sh": "bg-red-100 text-red-800",
            "pending_it": "bg-blue-100 text-blue-800",
            "rejected_it": "bg-red-100 text-red-800",
            "approved_complete": "bg-green-100 text-green-800"
        }
        return color_map.get(self.overall_status, "bg-gray-100 text-gray-800")
    
    @property
    def change_type_config(self):
        """
        Get configuration for change type display.
        """
        type_config = {
            'New Profile': {
                'icon': 'fa-user-plus',
                'color': 'text-green-600',
                'bg_color': 'bg-green-50'
            },
            'Profile Modification': {
                'icon': 'fa-user-edit',
                'color': 'text-blue-600',
                'bg_color': 'bg-blue-50'
            },
            'Profile Deactivation': {
                'icon': 'fa-user-times',
                'color': 'text-red-600',
                'bg_color': 'bg-red-50'
            },
            'Temporary Role Delegation': {
                'icon': 'fa-user-shield',
                'color': 'text-purple-600',
                'bg_color': 'bg-purple-50'
            }
        }
        return type_config.get(self.change_type, {
            'icon': 'fa-question',
            'color': 'text-gray-600',
            'bg_color': 'bg-gray-50'
        })

    class Meta:
        app_label = 'change_requests'
        indexes = [
            # Single field indexes
            models.Index(fields=['cr_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['change_type']),
            models.Index(fields=['created_by']),
            models.Index(fields=['application']),
            models.Index(fields=['is_deleted']),
            
            # Composite indexes for common query patterns
            models.Index(fields=['region', 'is_deleted', 'created_at']),  # Main listing query
            models.Index(fields=['region', 'cost_center', 'is_deleted']),  # Cost center filtering
            models.Index(fields=['change_type', 'region', 'is_deleted']),  # Type filtering
            models.Index(fields=['created_by', 'region', 'is_deleted']),  # User's requests
            models.Index(fields=['application', 'region', 'is_deleted']),  # Application filtering
            models.Index(fields=['created_at', 'region', 'is_deleted']),   # Date range queries
            
            # Performance indexes for computed properties
            models.Index(fields=['region', 'is_deleted', 'change_type', 'created_at']),  # Complex filtering
        ]
        ordering = ['-created_at']
        
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
        indexes = [
            # Single field indexes
            models.Index(fields=['cr_id']),
            models.Index(fields=['approver']),
            models.Index(fields=['approver_role']),
            models.Index(fields=['approval_status']),
            models.Index(fields=['approval_date']),
            
            # Composite indexes for approval queries
            models.Index(fields=['cr_id', 'approver_role']),  # Most common query pattern
            models.Index(fields=['approver_role', 'approval_status']),  # Status filtering by role
            models.Index(fields=['cr_id', 'approver_role', 'approval_status']),  # Complex approval queries
            models.Index(fields=['approver_role', 'approval_date']),  # Date-based approval queries
            models.Index(fields=['approver', 'approver_role', 'approval_status']),  # User's approval history
        ]