from typing import Dict, Any
from ..models import Appraisal, Experience
from it.users.models import UserProfile
from approve.models import Process
from ..helpers.types import ExperienceType


class AppraisalRepository:
    def create(self, user_object: UserProfile, process_object: Process, appraiser_object: UserProfile) -> Appraisal:
        try:
            return Appraisal.objects.create(user=user_object, process=process_object, appraiser=appraiser_object)
        except Exception as e:
            raise Exception(f"Appraisal Create Repo failed with error: {e}")

    def add_experience(self, appraisal_object :Appraisal, experience_object: Experience, data: ExperienceType):
        try:
            appraisal_object.experience.add(
                experience_object,
                through_defaults={
                    "years_of_experience": data.years_of_experience,
                    "months_of_experience": data.months_of_experience
                }

            )
        except Exception as e:
            raise Exception(f"Appraisal Experience Repo failed with error: {e}")

    def get_user_appraisal_objects(self, user_object: UserProfile)->list:
        return Appraisal.objects.filter(user=user_object)
    
    def get_appraisal_by_pk(self, appraisal_id: int)->Appraisal:
        return Appraisal.objects.filter(id=appraisal_id)
    
    def get_all_appraisal_objects(self)->list:
        
        return Appraisal.objects.all()
