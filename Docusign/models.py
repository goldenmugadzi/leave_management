"""
Document Models - For managing documents and signatures
"""
from django.db import models
from it.users.models import UserProfile 



class AuditLog(models.Model):
    """
    Audit log for tracking user activities
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('upload', 'Document Upload'),
        ('sign', 'Document Sign'),
        ('verify', 'Document Verify'),
        ('key_generate', 'Key Generation'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=255, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"


class PKIKeyPair(models.Model):
    """PKI Key Pair for user signatures - allows multiple key sets per user"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='pki_key_pairs')
    name = models.CharField(max_length=255, help_text="Name for this key pair (e.g., 'Legal Documents', 'Contracts')")
    public_key_pem = models.TextField()
    private_key_encrypted = models.TextField(help_text="Encrypted private key")
    certificate_pem = models.TextField()
    is_default = models.BooleanField(default=False, help_text="Default key pair for this user")
    is_active = models.BooleanField(default=True, help_text="Whether this key pair is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    class Meta:
        db_table = 'pki_key_pairs'
        ordering = ['-created_at']
        unique_together = [['user', 'name']]
    
    def save(self, *args, **kwargs):
        """Ensure only one default key pair per user"""
        if self.is_default:
            PKIKeyPair.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        default = " (Default)" if self.is_default else ""
        return f"{self.user.username} - {self.name}{default}"

class Document(models.Model):
    """Document model for uploaded files"""
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/%d/', max_length=500)
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='docs')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title


class Signature(models.Model):
    """Signature template for users"""
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sigs')
    image = models.ImageField(upload_to='docusign/signature_templates/', null=True, blank=True)
    requires_pki = models.BooleanField(default=False, help_text='If True, user must provide PKI password when signing with this signature')
    pki_key_pair = models.ForeignKey('PKIKeyPair', on_delete=models.SET_NULL, null=True, blank=True, related_name='signatures', help_text='PKI key pair to use when requires_pki is True')
    description = models.CharField(max_length=255, null=True, blank=True, help_text="Description for signature (e.g., 'Quick Approval', 'Legal Documents')")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signatures'
        ordering = ['-created_at']
    
    def __str__(self):
        protection = " [PKI Protected]" if self.requires_pki else ""
        return f"Signature by {self.owner.username}{protection}"


class Request(models.Model):
    """Signing request for documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reqs', null=True, blank=True)
    requester = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='made_reqs')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, null=True, blank=True, default='pending')
    require_all_signatures = models.BooleanField(default=True, help_text='If True, all signers must sign before completion')
    
    class Meta:
        db_table = 'requests'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Request #{self.id} - {self.status}"


class PossibleSigner(models.Model):
    """Users who can sign a request"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='poss_signers')
    signer = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='poss_reqs')
    role = models.CharField(choices=[('signer', 'Signer'), ('verifier', 'Verifier'), ('reviewer', 'Reviewer'), ('approver', 'Approver')], max_length=20, default='signer')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'possible_signers'
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.signer.username} for Request #{self.request.id}"


class Sign(models.Model):
    """Record of a completed signature"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='signs')
    signer = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed')
    signature = models.ForeignKey(Signature, on_delete=models.SET_NULL, null=True, blank=True, related_name='sig_used')
    signed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signs'
        ordering = ['-signed_at']
    
    def __str__(self):
        return f"Sign by {self.signer.username} at {self.signed_at}"


class Initial(models.Model):
    """Record of user initials placement on document pages"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='initials')
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='initials', null=True, blank=True)
    page_number = models.IntegerField(help_text="Page number where initial is placed")
    x_position = models.FloatField(help_text="X coordinate as percentage (0-1)")
    y_position = models.FloatField(help_text="Y coordinate as percentage (0-1)")
    width = models.FloatField(help_text="Width as percentage (0-1)")
    height = models.FloatField(help_text="Height as percentage (0-1)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'initials'
        ordering = ['page_number', '-created_at']
    
    def __str__(self):
        return f"Initial by {self.user.username} on page {self.page_number}"
