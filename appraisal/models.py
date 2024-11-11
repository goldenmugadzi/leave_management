from helpers.models import TimeStamp
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Appraisal(TimeStamp):
    """Model that defines all information required for appraisal process.
    The model use an abstract model(TimeStamp) with created_date and updated_date fields.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self) -> str:
        return f"{self.user}"
    

    
