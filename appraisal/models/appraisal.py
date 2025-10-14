from helpers.models import TimeStamp
from .helpers import YearQuarter
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Appraisal(TimeStamp):
    """Model that defines all information required for appraisal process.
    The model use an abstract model(TimeStamp) with created_date and updated_date fields.
    """
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    appraiser = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appraiser", null=True)
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reviewer", null=True)
    is_accepted = models.BooleanField(default=False)
    hr = models.ForeignKey(User, on_delete=models.PROTECT, related_name="hr", null=True)
    appraiser_comment = models.TextField(null=True, blank=True)
    reviewer_comment = models.TextField(null=True, blank=True)
    
    def __str__(self) -> str:
        return f"{self.user}"

class Experience(TimeStamp):
    """Base model for experiences used in Appraisal"""
    name = models.CharField(max_length=255, unique=True, null=False)

    def __str__(self) -> str:
        return str(self.name)


class AppraisalExperience(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE, related_name="appraisal")
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name="experience")

    # additional experiences
    years_of_experience = models.PositiveIntegerField(default=0)
    months_of_experience = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.appraisal.user} - {self.experience}"
    
class PersonalAttribute(TimeStamp):
    name = models.CharField(unique=True, max_length=250)
    
    def __str__(self):
        return self.name
    
class AppraiseePersonalAttribute(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="appraisee_appraisal")
    personal_attribute = models.ForeignKey(PersonalAttribute, on_delete=models.RESTRICT, related_name="personal_attributes")
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT, null=True, blank=True, related_name="personal_attributes_quarter")

    excellent = models.BooleanField(default=False)
    very_good = models.BooleanField(default=False)
    satisfactory = models.BooleanField(default=False)
    requires_improvement = models.BooleanField(default=False)
    unsatisfactory = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.appraisal} - {self.personal_attribute} - {self.quarter}"


