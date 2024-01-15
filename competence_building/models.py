from django.db import models

# Create your models here.
class OrganisationalCharts(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='charts/')
    office = models.CharField(max_length=100)

    def __str__(self):
        return self.name
