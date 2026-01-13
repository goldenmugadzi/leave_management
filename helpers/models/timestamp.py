from django.db import models
from django.utils import timezone

class TimeStamp(models.Model):
    created_date = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True