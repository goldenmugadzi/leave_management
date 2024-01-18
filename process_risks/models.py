from django.db import models

class Departments(models.Model):

    name = models.CharField(max_length =60)

    def __str__(self):
        return self.name
    
class RiskFiles(models.Model):

    file_name = models.CharField(max_length =30)
    cat       = models.ForeignKey(Departments, on_delete = models.CASCADE)
    file      = models.FileField(null=True)
    filepath = models.CharField(max_length=400)

    def __str__(self):
        return self.file_name
