from django.conf import settings
from django.db import models
from datetime import date, datetime
from it.users.models import *


# Create your models here.
class Employee(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,)
    jobcardnumber = models.CharField(max_length=300)
    serialnumber = models.CharField(max_length=100)
    loggedindate=  models.DateField(auto_now_add=True)
    phoneextension = models.CharField(max_length=100)
    fault = models.CharField(max_length=277)
    repairstatus = models.CharField(max_length=100,help_text="Status",  choices=[('loggedin', 'loggedin') , ('fixed', 'fixed'),('Awaiting New Spares', 'Awaiting New Spares'), ('Repaired', 'Repaired'),('Obsolute State', 'Obsolute State')])
    #updatedby = models.ForeignKey(UserProfile, on_delete=models.CASCADE,related_name="updatedby",null=True, blank=True)
    lastupdate= models.DateField(auto_now=True)
    comment = models.CharField(max_length=600,default="No comment")
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)

  
    

    def save(self, *args, **kwargs):
        if not self.jobcardnumber:
            self.jobcardnumber = "JC" + str(int(datetime.now().timestamp()))
        super(Employee, self).save(*args, **kwargs)

    def __str__(self):
        return self.jobcardnumber