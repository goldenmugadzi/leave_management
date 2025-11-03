from django.db import models
from datetime import date
import random
import time
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from helpers.models import TimeStamp
from datetime import date
from dateutil.relativedelta import relativedelta

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(username=username, **extra_fields)
        try:
            validate_password(password, user=user)
            user.set_password(password)
            user.save(using=self._db)
            return user
            # Password is valid
        except ValidationError as e:
            # Password is not valid
            print(e.messages)
            return None

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class Regions(models.Model):
    region = models.CharField(max_length=100)
    code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.region


class Districts(models.Model):
    district = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

    def __str__(self):
        return self.district


class Sections(models.Model):
    section = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district_id = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

    def __str__(self):
        return self.section


class Depots(models.Model):
    depot = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)

    def __str__(self):
        return self.depot

class Substation(models.Model):
    name =  models.CharField(max_length=100)
    code =  models.CharField(max_length=100)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING,null=True, blank=True, related_name='substations')
    district = models.ForeignKey(Districts, on_delete=models.DO_NOTHING,null=True, blank=True)
    depot = models.ForeignKey(Depots, on_delete=models.DO_NOTHING,null=True, blank=True)

    def __str__(self):
        return self.name

class Application(models.Model):
    name = models.CharField(max_length=100, unique=True)
    fullname = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Roles(models.Model):
    role = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    application = models.CharField(max_length=100)
    app_id = models.ForeignKey(Application, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.application}"


class Designations(models.Model):
    identifier = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)
    chk = models.CharField(max_length=100, blank=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.description


class CostCenter(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    class Meta:
        ordering = ['parent__id']

    def get_all_children(self):
        children = list(self.children.all())
        return children

    def get_decendance(self):
        def _get_all_descendants(node):
            descendants = node.children.all()
            for child in descendants:
                descendants |= _get_all_descendants(child)
            return descendants

        descendants = _get_all_descendants(self)
        return descendants | self.__class__.objects.filter(pk=self.pk)

    def get_all_ancestors(self):
        ancestors = []
        current = self
        while current.parent:
            ancestors.append(current.parent)
            current = current.parent
        return ancestors[::-1]

    def get_region(self):
        cc = self
        ancestors = cc.get_all_ancestors()

        return ancestors[2]

    def get_all_ancestors_and_their_children(self):
        ancestors = CostCenter.objects.none()
        if self.parent:
            ancestors.append(self.parent)
            ancestors += self.parent.get_all_ancestors_and_their_children()
        children = self.get_all_children()
        return ancestors + children

    def get_view(self):
        """ return a list of cost centers involving children, grand children, brothers ,parent , parent brothers, grand parent"""
        cost_centers = []
        i = 0
        while self.parent and i < 2:
            cost_centers.append(self)
            cost_centers += self.get_all_children()
            self = self.parent
            i += 1
        return cost_centers
    def get_view_1(self):
        """ return a list of cost centers involving children, grand children, brothers ,parent , parent brothers, grand parent"""
        cost_centers = []
        i = 0
        while self.parent and i < 4:
            cost_centers.append(self)
            cost_centers += self.get_all_children()
            self = self.parent
            i += 1
        return cost_centers

    def __str__(self):

        return f"{self.name} ({self.code})"


GRADE_CHOICES = [
    ('',''),
    ('A and B', 'A and B'),
    ('C and Above', 'C and Above'), 
]


class UserProfile(AbstractUser):
    username = models.CharField(max_length=15, unique=True, verbose_name='EC Number', db_index=True)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.DO_NOTHING, blank=True, null=True)
    roles = models.ManyToManyField(Roles, blank=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=50, blank=True)
    last_reset = models.DateField(default=timezone.now)
    password_expiry_date = models.DateField(null=True, blank=True)
    password_expiry_days = models.IntegerField(default=90)
    change_password = models.BooleanField(default=False, null=True, blank=True)
    grade = models.CharField(choices=GRADE_CHOICES, max_length=20, null=True, blank=True)
    national_id = models.CharField(max_length=18, null=True, default=None)
    date_of_engagement = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['last_name', 'first_name', 'username']

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        else:
            return f"{self.username}"


    def add_role(self, role, app_id):
        existing_role = self.roles.filter(app_id__fullname=app_id).first()
        if existing_role:
            self.roles.remove(existing_role)
        try:
            self.roles.add(role)
        except:
            pass
        self.save()

    def get_user_roles_for_application(self, application_name):
        # Filter the user's roles for the specific application
        application = Application.objects.filter(name=application_name).first()
        print("application: ", application)
        if application:
            user_roles = self.roles.filter(app_id=application.id)
            print("user_roles: ", user_roles)
            # Return the roles if any exist
            if user_roles.exists():
                return user_roles[0].role
        else:
            return None

    def get_user_role_for_application(self, application_name):
        # Filter the user's roles for the specific application
        # Check both the app_id foreign key and the application char field
        application = Application.objects.filter(name=application_name).first()
        print("application: ", application)
        
        if application:
            # First try to find roles by app_id foreign key
            user_roles = self.roles.filter(app_id=application.id)
            print("user_roles by app_id: ", user_roles)
            if user_roles.exists():
                return user_roles[0]
        
        # If not found by app_id, try by application char field
        user_roles = self.roles.filter(application=application_name)
        print("user_roles by application field: ", user_roles)
        if user_roles.exists():
            return user_roles[0]
        
        return None

    def cost_centers_for(self, app_names):
        responsibilities = self.responsibilities.filter(role__app_id__name__in=app_names)
        if responsibilities.exists():
            cost_centers = set()
            for responsibility in responsibilities:
                cost_centers.update(responsibility.cost_centers.all())
            return cost_centers
        return None

    def cost_center_and_decendace(self):
        CostCenters = CostCenter.objects.filter(pk=self.cost_center.pk)
        CostCenters |= self.cost_center.get_decendance()
        return CostCenters
    
    def get_effective_roles(self, application_name=None):
        """Get user's effective roles including delegated roles"""
        from django.utils import timezone
        
        # Get user's own roles
        effective_roles = set(self.roles.all())
        
        # Get active delegated roles
        now = timezone.now()
        active_delegations = RoleDelegation.objects.filter(
            delegatee=self,
            status='ACTIVE',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        
        for delegation in active_delegations:
            if application_name:
                # Filter by specific application
                delegated_roles = delegation.roles.filter(
                    app_id__name=application_name
                )
            else:
                delegated_roles = delegation.roles.all()
            
            effective_roles.update(delegated_roles)
        
        return list(effective_roles)
    
    def has_delegated_role(self, role, application_name=None):
        """Check if user has a specific role through delegation"""
        effective_roles = self.get_effective_roles(application_name)
        return role in effective_roles
    
    def get_active_delegations(self):
        """Get all active delegations for this user"""
        from django.utils import timezone
        
        now = timezone.now()
        return RoleDelegation.objects.filter(
            delegatee=self,
            status='ACTIVE',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
    
    def get_pending_delegations(self):
        """Get all pending delegations for this user"""
        return RoleDelegation.objects.filter(
            delegatee=self,
            status='PENDING'
        )
    
    def can_delegate_roles(self):
        """Check if user can delegate roles (has roles to delegate)"""
        return self.roles.exists()
    
    def can_approve_delegations(self):
        """Check if user can approve delegations (admin or section head)"""
        # Check if user has admin or administrator role in users application
        admin_role = self.roles.filter(
            role__in=['admin', 'administrator'],
            application='users'
        ).exists()
        
        # Check if user has section head role in users application
        section_head_role = self.roles.filter(
            role='section_head',
            application='users'
        ).exists()
        
        return admin_role or section_head_role


class Notification(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    url = models.CharField(max_length=250)
    notification_type = models.CharField(max_length=100, blank=True, null=True)
    notification_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class Supplier(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    name = models.CharField(max_length=100, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "splr" + timestamp + random_number
        super().save(*args, **kwargs)


class Responsibilities(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,
                             related_name='responsibilities')
    role = models.ForeignKey(Roles, on_delete=models.CASCADE, blank=True, null=True)
    cost_centers = models.ManyToManyField(CostCenter, blank=True)

    def __str__(self):
        return str(self.role.name)
   

class RoleDelegation(models.Model):
    """Model for managing temporary role delegations between users"""
    
    DELEGATION_STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    delegator = models.ForeignKey(
        'UserProfile', 
        on_delete=models.CASCADE, 
        related_name='delegated_roles',
        help_text="User who is delegating their roles"
    )
    delegatee = models.ForeignKey(
        'UserProfile', 
        on_delete=models.CASCADE, 
        related_name='received_delegations',
        help_text="User who will receive the delegated roles"
    )
    roles = models.ManyToManyField(
        'Roles', 
        help_text="Roles being delegated"
    )
    applications = models.ManyToManyField(
        'Application',
        help_text="Applications for which roles are being delegated"
    )
    start_date = models.DateTimeField(
        help_text="When the delegation becomes active"
    )
    end_date = models.DateTimeField(
        help_text="When the delegation expires"
    )
    reason = models.TextField(
        help_text="Reason for delegation (e.g., leave, training, etc.)"
    )
    status = models.CharField(
        max_length=20, 
        choices=DELEGATION_STATUS_CHOICES, 
        default='PENDING',
        help_text="Current status of the delegation"
    )
    approved_by = models.ForeignKey(
        'UserProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_delegations',
        help_text="User who approved the delegation"
    )
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the delegation was approved"
    )
    rejection_reason = models.TextField(
        null=True, 
        blank=True,
        help_text="Reason for rejection if applicable"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the delegation is currently active"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_delegations',
        help_text="User who created this delegation request"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delegator']),
            models.Index(fields=['delegatee']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.delegator.username} → {self.delegatee.username} ({self.status})"
    
    def is_currently_active(self):
        """Check if delegation is currently active"""
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and 
            self.is_active and 
            self.start_date <= now <= self.end_date
        )
    
    def can_be_approved(self):
        """Check if delegation can be approved"""
        return self.status == 'PENDING'
    
    def can_be_cancelled(self):
        """Check if delegation can be cancelled"""
        return self.status in ['PENDING', 'APPROVED', 'ACTIVE']
    
    def approve(self, approver):
        """Approve the delegation"""
        if self.can_be_approved():
            self.status = 'APPROVED'
            self.approved_by = approver
            self.approved_at = timezone.now()
            self.save()
            return True
        return False
    
    def activate(self):
        """Activate the delegation"""
        if self.status == 'APPROVED' and timezone.now() >= self.start_date:
            self.status = 'ACTIVE'
            self.save()
            return True
        return False
    
    def expire(self):
        """Mark delegation as expired"""
        if self.status == 'ACTIVE':
            self.status = 'EXPIRED'
            self.is_active = False
            self.save()
            return True
        return False
    
    def cancel(self, reason=None):
        """Cancel the delegation"""
        if self.can_be_cancelled():
            self.status = 'CANCELLED'
            self.is_active = False
            if reason:
                self.rejection_reason = reason
            self.save()
            return True
        return False
    
    def reject(self, reason):
        """Reject the delegation"""
        if self.status == 'PENDING':
            self.status = 'REJECTED'
            self.rejection_reason = reason
            self.save()
            return True
        return False


class DelegationNotification(models.Model):
    """Model for tracking delegation notifications"""
    
    NOTIFICATION_TYPES = [
        ('DELEGATION_CREATED', 'Delegation Created'),
        ('DELEGATION_APPROVED', 'Delegation Approved'),
        ('DELEGATION_REJECTED', 'Delegation Rejected'),
        ('DELEGATION_ACTIVATED', 'Delegation Activated'),
        ('DELEGATION_EXPIRED', 'Delegation Expired'),
        ('DELEGATION_CANCELLED', 'Delegation Cancelled'),
        ('DELEGATION_REMINDER', 'Delegation Reminder'),
    ]
    
    delegation = models.ForeignKey(
        RoleDelegation, 
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    recipient = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='delegation_notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"

QUALIFICATION_TYPE = [
    ("Ordinary Levels", "Ordinary Levels"),
    ("Advanced Levels", "Advanced Levels"),
    ("Certificate", "Certificate"),
    ("Diploma", "Diploma"),
    ("Higher National Diploma", "Higher National Diploma"),
    ("Professional Membership", "Professional Membership"),
    ("Degree", "Degree"),
    ("Masters", "Masters"),
    ("PHD", "PHD"),
    ("Other", "Other")
]

class UserQualification(TimeStamp):
    """_summary_

    Args:
        TimeStamp (_type_): _description_
    """
    user = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    name = models.CharField(max_length=30, null=False, blank=False, choices=QUALIFICATION_TYPE)
    description = models.CharField(max_length=255, null=True, default=None)
    file = models.FileField(upload_to='uploads/appraisal/user_qualification', null=True, blank=True)
    
    def __str__(self) -> str:
        return f"{self.name}"
    
class UserExperience(TimeStamp):
    """
        Represents a work experience entry for a user, storing when the experience started and ended.
        The duration in years can be computed from these dates.
    """
    user = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name="user_experience")
    name = models.CharField(max_length=255, null=False)
    experience_from = models.DateField()
    experience_to = models.DateField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"],
                                    violation_error_message="user experience with this name already exists",
                                    name='unique_user_experience_name'
                                    )
        ]
        ordering = ['-experience_from']
    
    @property
    def years_of_experience(self):
        """
            Returns the duration between start and end date as a string in years and months.
            Example: '3 years, 2 months'
        """
        end_date = self.experience_to or date.today()
        rdelta = relativedelta(end_date, self.experience_from)
        parts = []
        if rdelta.years:
            parts.append(f"{rdelta.years} year{'s' if rdelta.years > 1 else ''}")
        if rdelta.months:
            parts.append(f"{rdelta.months} month{'s' if rdelta.months > 1 else ''}")
        return ", ".join(parts) if parts else "0 months"
    
    def __str__(self):
        return f"{self.name}"
    