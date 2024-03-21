from django.db import models
from it.users.models import Regions, Sections, UserProfile

# Create your models here.
class OrganisationalCharts(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='charts/')
    office = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

class Document(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank = True, null = True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    file = models.FileField()
    created_by = models.ForeignKey(UserProfile, on_delete = models.DO_NOTHING, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name





# class Job_description(models.Model):
#     filename = models.CharField(max_length=100)
#     file_type = models.CharField(max_length=100)
#     sub_category = models.CharField(max_length=100)
#     filepath = models.CharField(max_length=400)
#     section = models.CharField(max_length=100)
#     region = models.CharField(max_length=100)
#     created_at = models.DateField()
#     updated_at = models.DateField()
#     created_by = models.CharField(max_length=50)

#     def __str__(self):
#         return self.filename


# class Filetype (models.Model):
#    name = models.CharField(max_length=100)

#    def __str__(self):
#         return self.name
  
# class First_Category(models.Model):
#    name = models.CharField(max_length=100)
#    file_type = models.CharField(max_length=100)

#    def __str__(self):
#         return self.name
    