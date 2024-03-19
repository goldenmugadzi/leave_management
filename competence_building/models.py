from django.db import models

# Create your models here.
class OrganisationalCharts(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='charts/')
    office = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Job_description(models.Model):
    filename = models.CharField(max_length=100)
    file_type = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    filepath = models.CharField(max_length=400)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)

    def __str__(self):
        return self.filename


class Filetype (models.Model):
   name = models.CharField(max_length=100)

   def __str__(self):
        return self.name
  
class First_Category(models.Model):
   name = models.CharField(max_length=100)
   file_type = models.CharField(max_length=100)

   def __str__(self):
        return self.name