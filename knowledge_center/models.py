from django.db import models

# Create your models here.
class KnowledgeCenter(models.Model):
    filename = models.CharField(max_length=100)
    file_type = models.CharField(max_length=100)
    sub_category_1 = models.CharField(max_length=100)
    sub_category_2 = models.CharField(max_length=100)
    filepath = models.CharField(max_length=400)
    archived = models.BooleanField(default=False)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)

class Categories(models.Model):
   file_type = models.CharField(max_length=100)
   cat_1 = models.CharField(max_length=100)
   cat_2 = models.CharField(max_length=100)

class Filetype(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class First_Category(models.Model):
    file_type  = models.ForeignKey (Filetype,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Secondary_Category(models.Model):
    file  = models.ForeignKey (Filetype,on_delete=models.CASCADE,related_name='category')
    category  = models.ForeignKey (First_Category,on_delete=models.CASCADE,related_name='file')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name