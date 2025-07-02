from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('RESIDENTIAL', 'Residential'),
        ('COMMERCIAL', 'Commercial'),
        ('INDUSTRIAL', 'Industrial'),
        ('GOVERNMENT', 'Government'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('PENDING', 'Pending'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    customer_id = models.CharField(max_length=20, unique=True, help_text="Unique identifier for customer")
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    stand_number = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='RESIDENTIAL')
    account_number = models.CharField(max_length=20, blank=True, null=True)
    meter_number = models.CharField(max_length=20, blank=True, null=True)
    # New fields for Excel import
    region = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    depot = models.CharField(max_length=100, blank=True, null=True)
    suburb = models.CharField(max_length=100, blank=True, null=True)
    tariff_description = models.CharField(max_length=200, blank=True, null=True)
    supply_point_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    pjob = models.CharField(max_length=100, blank=True, null=True, help_text="Project job reference")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.customer_id}"
    
    class Meta:
        ordering = ['-date_created']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    required = models.BooleanField(default=False, help_text="Whether this document type is required for customer onboarding")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class CustomerDocument(models.Model):
    APPROVAL_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    file = models.FileField(upload_to='uploads/comm_files/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_documents')
    upload_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True, help_text="Date when document expires, if applicable")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='PENDING')
    approval_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.customer.name} - {self.document_type.name}"
    
    def approve(self, user):
        self.status = 'APPROVED'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()
    
    def reject(self, user, reason):
        self.status = 'REJECTED'
        self.approved_by = user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Customer Document"
        verbose_name_plural = "Customer Documents"
        unique_together = ['customer', 'document_type'] # A customer can only have one document of each type


class OnboardingProcess(models.Model):
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('DOCS_SUBMITTED', 'Documents Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='onboarding_processes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    initiated_date = models.DateTimeField(auto_now_add=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='initiated_processes')
    last_updated = models.DateTimeField(auto_now=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.customer.name} - {self.status}"
    
    def update_status(self, status, notes=None):
        self.status = status
        if notes:
            self.notes = notes
        if status == 'COMPLETED':
            self.completed_date = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-initiated_date']
        verbose_name = "Onboarding Process"
        verbose_name_plural = "Onboarding Processes"


class ActivityLog(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.customer.name} - {self.action} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

