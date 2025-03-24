from django.conf import settings
from django.db import models
from datetime import date, datetime
from it.users.models import *

# Create your models here.
class Employee(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    user = models.CharField(max_length=100)
    userprofile = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    jobcardnumber = models.CharField(max_length=300)
    eserialnumber = models.CharField(max_length=100)
    eloggedindate=  models.DateField(auto_now_add=True)
    eUsername = models.CharField(max_length=300)
    ephoneextension = models.CharField(max_length=100)
    efault = models.CharField(max_length=277)
    erepairstatus = models.CharField(max_length=277)
    elocation = models.CharField(max_length=277)
    eupdatedby = models.CharField(max_length=300)
    elastupdate= models.DateField(default=datetime.now)
    comment = models.CharField(max_length=600)
    department = models.CharField(max_length=500)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    sections = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    def __str_(self):
        return self.ename