from django.db import models
from django.contrib.auth.models import User
# from hr.users.models import User

class Nonconformity(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nonconformities_assigned_to', null=True, blank=True)
    description = models.TextField(max_length=400,blank=True,null=True,verbose_name='Description')
    violation_standard_reference = models.CharField(max_length=400,blank=True,null=True,verbose_name='Violation Standard Reference')
    recommended_corrective_action = models.CharField(max_length=300,blank=False,null=False,verbose_name='Recommended Corrective Action')
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='static/noneconformity_files/',blank=True,null=True,verbose_name='Attachment')
    status = models.CharField(max_length=20, choices=(('created', 'Created'),('accepted', 'Accepted'),('rejected', 'Rejected'),('pending', 'Pending'),('resolved', 'Resolved'),), default='created')
    response = models.TextField(max_length=400,blank=True,null=True)

    def __str__(self):return self.description


