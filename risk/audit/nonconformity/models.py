from django.db import models
import random
import time
from django.urls import reverse
from it.users.models import UserProfile

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
    violation_standard_reference = models.ForeignKey(Question,on_delete=models.SET_NULL ,  blank=True, null=True, verbose_name='Violation Standard Reference')
    description = models.TextField(max_length=400, blank=True, null=True)
    root_cause = models.TextField(max_length=400, blank=True, null=True)
    findings = models.TextField(max_length=400, blank=True, null=True)
    plan_of_action = models.TextField(max_length=400, blank=True, null=True, verbose_name='Plan of Action')
    recommended_corrective_action = models.CharField(max_length=300, blank=False, null=False, verbose_name='Recommended Corrective Action')
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='nonconformity_attachments/', blank=True, null=True, verbose_name='Attachment')
    expected_completion_date = models.DateField( verbose_name='Expected Completion Date', blank=True, null=True)
    status = models.BooleanField( choices=((True, 'Created'),(False, 'Resolved')), default= True)
    
    def __str__(self):
        return self.description
    
    def get_absolute_url(self):
        return reverse('nonconformity:nonconformity', args=[str(self.id)])
    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "NC" + timestamp + random_number
        super().save(*args, **kwargs)

class Response(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    nonconformity = models.ForeignKey(Nonconformity, on_delete=models.CASCADE)
    comment = models.TextField(max_length=400, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField( choices=((True, 'Accepted'),(False, 'Rejected')))
    
    def __str__(self):
        return 'Accepted' if self.status else 'Rejected'