from django.db import models

# Create your models here.
class Process_maps(models.Model):
    filename = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100, null=True)
    filepath = models.CharField(max_length=400)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)
   
    def __str__(self):
        return self.filename




    