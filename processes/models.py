from django.db import models
    
class Processes_Procedures(models.Model):
    filename = models.CharField(max_length=100)
    file_type = models.CharField(max_length=100)
    sub_category_1 = models.CharField(max_length=100)
    sub_category_2 = models.CharField(max_length=100)
    filepath = models.CharField(max_length=400)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)

class File_Type(models.Model):
    name = models.CharField(max_length = 100)
    
    def __str__(self):
        return self.name

class First_Category(models.Model):
    name = models.CharField(max_length=100)
    file_type_id  = models.ForeignKey (File_Type,on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    

class Second_Category(models.Model):
    file_type_id  = models.ForeignKey (File_Type,on_delete=models.CASCADE,related_name='category')
    first_cat_id = models.ForeignKey (First_Category,on_delete=models.CASCADE,related_name='category')
    category  = models.ForeignKey (First_Category,on_delete=models.CASCADE,related_name='file')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
