from django.db import models

from it.users.models import CostCenter, UserProfile

# Create your models here.
class ChangeRequest(models.Model):
    cr_id = models.CharField(max_length=100, primary_key=True)
    change_type = models.CharField(max_length=100)
    change_description = models.TextField()
    change_status = models.CharField(max_length=100)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cr_created_by')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.cr_id

    class Meta:
        app_label = 'change_requests'
        
class CRApproval(models.Model):
    cr_id = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE)
    approver = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    approval_status = models.CharField(max_length=100)
    approval_date = models.DateTimeField()
    
    def __str__(self):
        return self.cr_id

    class Meta:
        app_label = 'change_requests'