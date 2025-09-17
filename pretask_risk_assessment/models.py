from django.db import models
from it.users.models import Substation,UserProfile
from toolsandequipment.model import ToolOrEquipment

class Job(models.model):
    issuing_senior_authorised_person = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING,null=True, blank=True, related_name="jobs")
    competent_person = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING,null=True, blank=True,related_name="person_jobs" )
    substation = models.ForeignKey(Substation, on_delete=models.DO_NOTHING,null=True, blank=True)
    task = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Teammember(models.model):
    job = models.ForeignKey(Job, on_delete=models.DO_NOTHING,null=True, blank=True)
    person = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING,null=True, blank=True)
    agreed = models.CharField(max_length=100, blank=True, choices=[("Yes", "Yes"), ("No", "No"), ("Unknown", "Unknown")],default="Unknown")
     
    def __str__(self):
        return f"{self.person.get_fullname}"


class PretaskRiskAssessment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.DO_NOTHING,null=True, blank=True)
    equipment = models.ForeignKey(ToolOrEquipment, on_delete=models.DO_NOTHING,null=True, blank=True)
    harzard = models.TextField(blank=True)
    control_measures = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment} ({self.harzard})"