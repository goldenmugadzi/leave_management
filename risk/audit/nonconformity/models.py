from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
class Nonconformity(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nonconformities_assigned_to', null=True, blank=True)
    description = models.TextField(max_length=400, blank=True, null=True, verbose_name='Description')
    root_cause = models.TextField(max_length=400, blank=True, null=True)
    violation_standard_reference = models.CharField(max_length=400, blank=True, null=True, verbose_name='Violation Standard Reference')
    recommended_corrective_action = models.CharField(max_length=300, blank=False, null=False, verbose_name='Recommended Corrective Action')
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='static/nonconformity_files/', blank=True, null=True, verbose_name='Attachment')
    plan_of_action = models.TextField(max_length=400, blank=True, null=True, verbose_name='Plan of Action')
    expected_completion_date = models.DateField(blank=True, null=True, verbose_name='Expected Completion Date')
    
    def __str__(self):
        return self.description
    
    def get_absolute_url(self):
        return reverse('nonconformity:nonconformity', args=[str(self.id)])

class Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nonconformity = models.ForeignKey(Nonconformity, on_delete=models.CASCADE)
    comment = models.TextField(max_length=400, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=(('created', 'Created'),('accepted', 'Accepted'),('rejected', 'Rejected'), ('resolved', 'Resolved'),), default='created')
    
 
    def __str__(self):
        return f"Response by {self.user.username} on {self.nonconformity.description}"
