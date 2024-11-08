from django.db import models

class TimeStamp(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True