from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
from it.users.models import UserProfile, Regions, Districts, Sections, Depots, CostCenter
from approve.models import Workflow, Process, Approval


class SanctionForTestForm(models.Model):
    """
    Main model representing the entire ZESA Sanction-for-Test form.
    Uses the approval workflow system for signatures and approvals.
    """
    # Status choices for workflow management
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('received', 'Received'),
        ('cleared', 'Cleared'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    # Auto-generate unique form number
    form_no = models.CharField(max_length=50, unique=True, verbose_name="Form No.",
                             help_text="Unique form identifier")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft',
                            help_text="Current status of the form")
    
    # User tracking with UserProfile
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='created_sanction_forms',
                                 help_text="User who created this form")
    
    # Regional and organizational context from UserProfile
    region = models.ForeignKey(Regions, on_delete=models.SET_NULL, null=True, blank=True,
                              help_text="Region where the work will be performed")
    district = models.ForeignKey(Districts, on_delete=models.SET_NULL, null=True, blank=True,
                                help_text="District where the work will be performed")
    section = models.ForeignKey(Sections, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="Section responsible for the work")
    depot = models.ForeignKey(Depots, on_delete=models.SET_NULL, null=True, blank=True,
                             help_text="Depot where equipment is located")
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Cost center for budget tracking")
    
    # Workflow integration - this replaces individual signature fields
    approval_process = models.ForeignKey(Process, on_delete=models.SET_NULL, null=True, blank=True,
                                       help_text="Associated approval workflow process")
    
    date_issued = models.DateField(auto_now_add=True, verbose_name="Date Issued")
    
    # Priority and risk assessment
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium',
                              help_text="Priority level for this sanction")
    
    RISK_LEVEL_CHOICES = [
        ('minimal', 'Minimal'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('extreme', 'Extreme'),
    ]
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium',
                                help_text="Assessed risk level")
    
    # Timestamp tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Section 1.0: ISSUE - Technical Details
    work_to_be_carried_out = models.TextField(blank=True, null=True, 
                                            verbose_name="Work to be Carried Out",
                                            help_text="Detailed description of work to be performed")
    plant_or_equipment_to_be_tested = models.TextField(blank=True, null=True, 
                                                      verbose_name="Plant or Equipment to be Tested",
                                                      help_text="Equipment that will be tested")
    points_of_isolation = models.TextField(blank=True, null=True, 
                                         verbose_name="Points of Isolation",
                                         help_text="Safety isolation points")
    nearest_point_live = models.CharField(max_length=255, blank=True, null=True, 
                                        verbose_name="Nearest Point Live",
                                        help_text="Nearest live electrical point")
    circuit_main_earth_connected_at = models.CharField(max_length=255, blank=True, null=True, 
                                                     verbose_name="Circuit Main Earth Connected At",
                                                     help_text="Main earth connection point")
    danger_notices = models.CharField(max_length=255, blank=True, null=True, 
                                    verbose_name="Danger Notices",
                                    help_text="Posted danger notices")
    caution_notices = models.CharField(max_length=255, blank=True, null=True, 
                                     verbose_name="Caution Notices",
                                     help_text="Posted caution notices")
    special_keys = models.CharField(max_length=255, blank=True, null=True, 
                                  verbose_name="Special Keys",
                                  help_text="Special keys or access requirements")
    other_precaution = models.TextField(blank=True, null=True, 
                                      verbose_name="Other Precautions",
                                      help_text="Additional safety precautions")

    # Clearance and Cancellation specific fields
    exceptions = models.TextField(blank=True, null=True, 
                                verbose_name="Exceptions (Clearance)",
                                help_text="Any exceptions noted during clearance")
    cancellation_reason = models.TextField(blank=True, null=True,
                                         verbose_name="Cancellation Reason",
                                         help_text="Reason for cancellation")

    class Meta:
        verbose_name = "Sanction For Test Form"
        verbose_name_plural = "Sanction For Test Forms"
        ordering = ['-created_at']
        permissions = [
            ("can_issue_sanction", "Can issue sanction for test"),
            ("can_receive_sanction", "Can receive sanction for test"),
            ("can_clear_sanction", "Can clear sanction for test"),
            ("can_cancel_sanction", "Can cancel sanction for test"),
        ]

    def __str__(self):
        return f"Sanction For Test Form No: {self.form_no} ({self.get_status_display()})"

    # Section 1.0: ISSUE
    work_to_be_carried_out = models.TextField(blank=True, null=True, 
                                            verbose_name="Work to be Carried Out",
                                            help_text="Detailed description of work to be performed")
    plant_or_equipment_to_be_tested = models.TextField(blank=True, null=True, 
                                                      verbose_name="Plant or Equipment to be Tested",
                                                      help_text="Equipment that will be tested")
    points_of_isolation = models.TextField(blank=True, null=True, 
                                         verbose_name="Points of Isolation",
                                         help_text="Safety isolation points")
    nearest_point_live = models.CharField(max_length=255, blank=True, null=True, 
                                        verbose_name="Nearest Point Live",
                                        help_text="Nearest live electrical point")
    circuit_main_earth_connected_at = models.CharField(max_length=255, blank=True, null=True, 
                                                     verbose_name="Circuit Main Earth Connected At",
                                                     help_text="Main earth connection point")
    danger_notices = models.CharField(max_length=255, blank=True, null=True, 
                                    verbose_name="Danger Notices",
                                    help_text="Posted danger notices")
    caution_notices = models.CharField(max_length=255, blank=True, null=True, 
                                     verbose_name="Caution Notices",
                                     help_text="Posted caution notices")
    special_keys = models.CharField(max_length=255, blank=True, null=True, 
                                  verbose_name="Special Keys",
                                  help_text="Special keys or access requirements")
    other_precaution = models.TextField(blank=True, null=True, 
                                      verbose_name="Other Precautions",
                                      help_text="Additional safety precautions")

    # Clearance and Cancellation
    exceptions = models.TextField(blank=True, null=True, 
                                verbose_name="Exceptions (Clearance)",
                                help_text="Any exceptions noted during clearance")

    cancellation_reason = models.TextField(blank=True, null=True,
                                         verbose_name="Cancellation Reason",
                                         help_text="Reason for cancellation")

    class Meta:
        verbose_name = "Sanction For Test Form"
        verbose_name_plural = "Sanction For Test Forms"
        ordering = ['-created_at']
        permissions = [
            ("can_issue_sanction", "Can issue sanction for test"),
            ("can_receive_sanction", "Can receive sanction for test"),
            ("can_clear_sanction", "Can clear sanction for test"),
            ("can_cancel_sanction", "Can cancel sanction for test"),
        ]

    def __str__(self):
        return f"Sanction For Test Form No: {self.form_no} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Auto-generate form number if not provided and set regional data from user"""
        if not self.form_no:
            # Generate unique form number with prefix and timestamp
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.form_no = f"SFT-{timestamp}-{unique_id}"
        
        # Auto-populate regional data from creator if not set
        if self.created_by and not self.pk:  # Only on creation
            if not self.region and self.created_by.region:
                self.region = self.created_by.region
            if not self.district and self.created_by.district:
                self.district = self.created_by.district
            if not self.section and self.created_by.section:
                self.section = self.created_by.section
            if not self.depot and self.created_by.depot:
                self.depot = self.created_by.depot
            if not self.cost_center and self.created_by.cost_center:
                self.cost_center = self.created_by.cost_center
        
        super().save(*args, **kwargs)

    @property
    def is_editable(self):
        """Check if form can still be edited"""
        return self.status in ['draft', 'issued']

    @property
    def can_be_cancelled(self):
        """Check if form can be cancelled"""
        return self.status in ['issued', 'received']

    def get_next_required_action(self):
        """Get the next required action based on current status"""
        action_map = {
            'draft': 'Issue Form',
            'issued': 'Receive Form',
            'received': 'Clear Form',
            'cleared': 'Complete or Cancel',
            'cancelled': 'Post-Cancellation Declaration',
            'completed': 'Form Complete'
        }
        return action_map.get(self.status, 'Unknown Action')
    
    def get_current_approvals(self):
        """Get all approvals for this form's process"""
        if not self.approval_process:
            return Approval.objects.none()
        return Approval.objects.filter(process=self.approval_process).order_by('step__step')
    
    def get_pending_approvals(self):
        """Get pending approvals for this form"""
        if not self.approval_process:
            return []
        
        completed_steps = self.get_current_approvals().filter(approved__isnull=False).values_list('step__step', flat=True)
        max_completed_step = max(completed_steps) if completed_steps else 0
        
        from approve.models import Step
        next_step = Step.objects.filter(
            workflow=self.approval_process.workflow,
            step=max_completed_step + 1
        ).first()
        
        return [next_step] if next_step else []
    
    def can_user_approve(self, user):
        """Check if a user can approve at the current step"""
        if not self.approval_process:
            return False
        
        pending_steps = self.get_pending_approvals()
        if not pending_steps:
            return False
        
        current_step = pending_steps[0]
        
        # Check if user has the required role
        user_roles = user.roles.all()
        return current_step.approver in user_roles
    
    def get_approval_by_step_name(self, step_name):
        """Get approval by step name (e.g., 'issue', 'receive', 'clear')"""
        if not self.approval_process:
            return None
        
        step_mapping = {
            'issue': 1,      # Declaration by Responsible Official
            'receive': 2,    # Receipt
            'clear': 3,      # Clearance
            'cancel': 4,     # Cancellation (if needed)
        }
        
        step_number = step_mapping.get(step_name)
        if step_number:
            return self.get_current_approvals().filter(step__step=step_number).first()
        return None
    
    def get_notification_users(self):
        """Get users who should be notified about form updates"""
        users = []
        if self.created_by:
            users.append(self.created_by)
        
        # Add users from the same section/depot who have relevant roles
        if self.section:
            section_users = UserProfile.objects.filter(
                section=self.section,
                is_active=True
            ).exclude(pk=self.created_by.pk if self.created_by else None)
            users.extend(section_users)
        
        return users


# Intermediate models to handle specific form sections if needed
# Since we're using the approval workflow system, these are simplified

class SanctionFormAuditLog(models.Model):
    """
    Audit log for tracking all changes and actions on sanction forms
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('issued', 'Issued'),
        ('received', 'Received'),
        ('cleared', 'Cleared'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('modified', 'Modified'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('comment_added', 'Comment Added'),
    ]
    
    form = models.ForeignKey(SanctionForTestForm, on_delete=models.CASCADE, 
                           related_name='audit_logs')
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(help_text="Detailed description of the action")
    previous_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    approval_step = models.IntegerField(null=True, blank=True, help_text="Workflow step number")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sanction Form Audit Log"
        verbose_name_plural = "Sanction Form Audit Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.form.form_no} - {self.action} by {self.user} at {self.timestamp}"


class SanctionFormComment(models.Model):
    """
    Comments and notes on sanction forms for better communication
    """
    form = models.ForeignKey(SanctionForTestForm, on_delete=models.CASCADE, 
                           related_name='comments')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    comment = models.TextField(help_text="Comment or note about the form")
    is_private = models.BooleanField(default=False, 
                                   help_text="Private comments only visible to admin users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sanction Form Comment"
        verbose_name_plural = "Sanction Form Comments"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.form.form_no} by {self.user}"


class SanctionFormAttachment(models.Model):
    """
    File attachments for sanction forms (supporting documents, photos, etc.)
    """
    ATTACHMENT_TYPES = [
        ('document', 'Document'),
        ('photo', 'Photo'),
        ('diagram', 'Diagram'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    ]
    
    form = models.ForeignKey(SanctionForTestForm, on_delete=models.CASCADE, 
                           related_name='attachments')
    file = models.FileField(upload_to='sanction_forms/attachments/%Y/%m/')
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='document')
    description = models.CharField(max_length=255, blank=True, null=True,
                                 help_text="Brief description of the attachment")
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sanction Form Attachment"
        verbose_name_plural = "Sanction Form Attachments"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Attachment for {self.form.form_no}: {self.description or self.file.name}"
