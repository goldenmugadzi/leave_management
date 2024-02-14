from django.db import models

class Departments(models.Model):

    name = models.CharField(max_length =60)

    def __str__(self):
        return self.name
    
class RiskFiles(models.Model):

    file_name  = models.CharField(max_length =30)
    cat        = models.ForeignKey(Departments, on_delete = models.CASCADE)
    file       = models.FileField(null=True)
    filepath   = models.CharField(max_length=400)
    section    = models.CharField(max_length=100)
    created_by = models.CharField(max_length=50)
    created_at = models.DateField(null = True)
    updated_at = models.DateField()
    region = models.CharField(max_length=100)

    def __str__(self):
        return self.file_name
