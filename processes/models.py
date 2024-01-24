from django.db import models

# Create your models here.

class FormsUploads(models.Model):
    filename = models.CharField(max_length=100)
    filetype = models.CharField(max_length=100)
    file_path = models.CharField(max_length=400)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()

class Filetype(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
