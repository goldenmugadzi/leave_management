from typing import Dict, Any
from ..models import Appraisal
from it.users.models import UserProfile
from approve.models import Process


class AppraisalRepository:
    def create(self, user_object: UserProfile, process_object: Process)->Appraisal:
        try:
            return Appraisal.objects.create(user=user_object, process=process_object)
        except Exception as e:
            raise Exception(f"Appraisal Create Repo failed with error: {e}")