from django.db import models
from it.users.models import Roles,UserProfile

class Application(models.Model):
    name = models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name

class Workflow(models.Model):
    name = models.CharField(max_length=100,unique=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)

    def __str__(self):
        return self.name



class Step(models.Model):
    approver = models.ForeignKey(Roles, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE,null=True, blank=True)
    to = models.CharField(max_length=400,null=True, blank=True)
    step = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['workflow','step']

    def __str__(self):
        return f"{self.approver}"

class Process(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.workflow} created at {self.created_at}"

class Approval(models.Model):
    APPROVAL_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    step = models.ForeignKey(Step, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    comment = models.TextField(max_length=200, blank=True, null=True)
    approved = models.CharField(max_length=8, choices=APPROVAL_CHOICES)

    def __str__(self):
        return f"Approval for step {self.step} by {self.user}"