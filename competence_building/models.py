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

class Subcategory(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='subtype')
    # section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    
    def __str__(self):
        return self.name 

class Document(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank = True, null = True)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    archive = models.BooleanField(default=False)
    file = models.FileField()
    created_by = models.ForeignKey(UserProfile, on_delete = models.DO_NOTHING, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Vacancies(models.Model):
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    department = models.ForeignKey(Sections, on_delete=models.CASCADE)
    archive = models.BooleanField(default=False)
    file = models.FileField()
    name = models.CharField(max_length=100, blank = True, null = True)
    uploaded_by = models.ForeignKey(UserProfile, on_delete = models.DO_NOTHING, blank = True, null = True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name