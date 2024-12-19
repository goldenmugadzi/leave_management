from django.conf import settings
from django.db import models
from datetime import date, datetime


# Create your models here.
class Employee(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.CharField(max_length=100)
    jobcardnumber = models.CharField(max_length=300)
    eserialnumber = models.CharField(max_length=7)
    eloggedindate=  models.DateField(default=datetime.now)
    eUsername = models.CharField(max_length=300)
    ephoneextension = models.CharField(max_length=100)
    efault = models.CharField(max_length=277)
    erepairstatus = models.CharField(max_length=277)
    elocation = models.CharField(max_length=277)
    eupdatedby = models.CharField(max_length=300)
    elastupdate= models.DateField(default=datetime.now)
    def __str_(self):
        return self.ename