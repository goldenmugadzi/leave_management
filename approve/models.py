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


class Role(models.Model):
    name = models.CharField(max_length=100,unique=True)
    description = models.CharField(max_length=400,null=True, blank=True)
    
    def __str__(self):
        return self.name


class Step(models.Model):
    approver = models.ForeignKey(Role, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE,null=True, blank=True)
    step = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['workflow','step']

    def __str__(self):
        return f"{self.approver} for {self.workflow}"


class Approval(models.Model):
    APPROVAL_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    ]

    step = models.ForeignKey(Step, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    comment = models.TextField(max_length=200, blank=True, null=True)
    approved = models.CharField(max_length=1, choices=APPROVAL_CHOICES, default='P')

    def __str__(self):
        return f"Approval for step {self.step} by {self.user}"

# from django.db import models
# from it.users.models import Roles,UserProfile

# class Workflow(models.Model):
#     name = models.CharField(max_length=100)
#     application = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name


# class Step(models.Model):
#     from_role = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name='from_steps')
#     to_role = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name='to_steps', null=True, blank=True)
#     workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
#     order = models.PositiveIntegerField()

#     class Meta:
#         ordering = ['workflow','order']

#     def __str__(self):
#         return f"Step from {self.from_role} to {self.to_role} for {self.workflow}"


# class Approval(models.Model):
#     APPROVAL_CHOICES = [
#         ('P', 'Pending'),
#         ('A', 'Approved'),
#         ('R', 'Rejected'),
#     ]

#     step = models.ForeignKey(Step, on_delete=models.CASCADE)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     comment = models.TextField(max_length=200, blank=True, null=True)
#     approved = models.CharField(max_length=1, choices=APPROVAL_CHOICES, default='P')

#     def __str__(self):
#         return f"Approval for step {self.step} by {self.user}"