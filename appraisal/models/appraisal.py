from helpers.models import TimeStamp
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Appraisal(TimeStamp):
    """Model that defines all information required for appraisal process.
    The model use an abstract model(TimeStamp) with created_date and updated_date fields.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    experience = models.ManyToManyField("Experience", through="AppraisalExperience")
    process = models.ForeignKey("approve.Process", on_delete=models.CASCADE, null=True,
                                related_name="appraisal_process")


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


