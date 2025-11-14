from django.db import models
from it.users.models import UserProfile 

# Document
class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='docusign/documents/')
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='docs')
    uploaded_at = models.DateTimeField(auto_now_add=True)

# Signature Template
class Signature(models.Model):
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sigs')
    image = models.ImageField(upload_to='docusign/signature_templates/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# Signing Request
class Request(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reqs')
    requester = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='made_reqs') 
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')

# Possible Signer
class PossibleSigner(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='poss_signers')
    signer = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='poss_reqs')
    added_at = models.DateTimeField(auto_now_add=True)

# Sign Record
class Sign(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='signs')
    signer = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed')
    signature = models.ForeignKey(Signature, on_delete=models.SET_NULL, null=True, blank=True, related_name='sig_used')
    signed_at = models.DateTimeField(auto_now_add=True)