from django.db import models
from it.users.models import *

# Create your models here.
class Report(models.Model):
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING)
    report_period = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    file_name = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.CharField(max_length=300, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, related_name='created_by')

    def __str__(self):
        return self.file_name