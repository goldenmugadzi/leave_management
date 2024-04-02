from django.db import models
from it.users.models import *

# Create your models here.
class Report(models.Model):
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    region = models.CharField(max_length=100, blank=True, null=True)
    report_period = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.CharField(max_length=100, blank=True, null=True)
    date_updated = models.CharField(max_length=100, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True)
    file_name = models.CharField(max_length=100, blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.file_name
