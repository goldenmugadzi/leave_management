from django.db import models
import random
from django.utils import timezone

import time
from django.urls import reverse
from it.users.models import UserProfile, CostCenter

class Clause(models.Model):
    id = models.CharField(max_length=4, blank=False, null=False,primary_key=True, verbose_name='Clause number')
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Name')
    def __str__(self):
        return self.id
class Topic(models.Model):
    clause= models.ForeignKey(Clause, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Name')
    def __str__(self):
        return self.name

class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, blank=True, null=True)
    id = models.CharField(max_length=200, blank=False, null=False, primary_key=True, verbose_name='ISO Requirement number')
    description = models.TextField(max_length=400, blank=True, null=True, verbose_name='ISO: Requirements')
    maintained_info = models.CharField(max_length=200, blank=True, null=True, verbose_name='Maintained Info', help_text='“Maintained” Documented information')
    retained_info = models.CharField(max_length=200, blank=True, null=True, verbose_name='Retained Info', help_text='“Retained” Documented information')
    
    def __str__(self):
        return self.id
        
class Nonconformity(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='nonconformities_assigned_to', null=True, blank=True)
    violation_standard_reference = models.ForeignKey(Question,on_delete=models.SET_NULL ,  blank=True, null=True)
    description = models.TextField(max_length=400, blank=True, null=True)
    # findings = models.TextField(max_length=400, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    root_cause = models.TextField(max_length=400, blank=True, null=True)
    recommended_corrective_action = models.CharField(max_length=300, blank=True, null=True, help_text='Recommend a corrective action')
    accepted = models.BooleanField( blank=True, null=True)
    resolved = models.BooleanField(blank=True, null=True)
    closed = models.BooleanField(blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return self.id
    
    def get_absolute_url(self):
        return reverse('nonconformity:nonconformity', args=[str(self.id)])
    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "NC" + timestamp + random_number
        super().save(*args, **kwargs)
class Attachment(models.Model):
    nonconformity = models.ForeignKey(Nonconformity, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='nonconformity/attachments/', blank=True, null=True, verbose_name='Attachment')
    def __str__(self):
        return self.attachment.name
class Acceptance(models.Model):
    nonconformity = models.ForeignKey(Nonconformity , on_delete=models.CASCADE)
    cause = models.TextField(max_length=400, blank=True, null=True)
    corrective_action = models.CharField(max_length=300, blank=True, null=True)
    dated = models.DateTimeField(default=timezone.now)
    expected_completion_date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return self.corrective_action
class Resolution(models.Model):
    nonconformity = models.ForeignKey(Nonconformity , on_delete=models.CASCADE)
    corrective_action_taken = models.CharField(max_length=300, blank=True, null=True)
    dated = models.DateTimeField(default=timezone.now)
    resolved_on = models.DateField(blank=True, null=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return self.corrective_action_taken
    
class Rejection(models.Model):
    nonconformity = models.ForeignKey(Nonconformity , on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    rejection_reason = models.TextField(max_length=400, blank=True, null=True)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE, blank=True, null=True)
    dated = models.DateTimeField(default=timezone.now) 
    def __str__(self):
        return self.rejection_reason
    

class RejectionAttachment(models.Model):
    rejection = models.ForeignKey(Rejection, on_delete=models.CASCADE)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return self.attachment.name
class AcceptanceAttachment(models.Model):
    acceptance = models.ForeignKey(Acceptance, on_delete=models.CASCADE)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return self.attachment.name