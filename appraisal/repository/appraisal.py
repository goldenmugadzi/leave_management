from typing import Dict, Any, List
from django.db.models import Q
from ..models import Appraisal, Experience
from it.users.models import UserProfile
from approve.models import Process
from ..helpers.types import ExperienceType


class AppraisalRepository:
    def create(self, user_object: UserProfile, appraiser_object: UserProfile, reviewert_object: UserProfile) -> Appraisal:
        try:
            return Appraisal.objects.create(user=user_object, appraiser=appraiser_object, reviewer=reviewert_object)
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
    
    def remove_experience(self, appraisal_object :Appraisal, experience_object: Experience):
        try:
            appraisal_object.experience.remove(
              experience_object  
            )
        except Exception as e:
            raise Exception(f"Appraisal Experience Repo failed with error: {e}")

    def fetch_by_user(self, user_object: UserProfile) -> List[Appraisal]:
        return Appraisal.objects.filter(user=user_object)
    
    def fetch_by_appraiser(self, appraiser_object: UserProfile) -> List[Appraisal]:
        return Appraisal.objects.filter(appraiser=appraiser_object)
    
    def fetch_by_reviewer(self, reviewer_object: UserProfile) -> List[Appraisal]:
        return Appraisal.objects.filter(reviewer=reviewer_object)
        
    def get_appraisal_by_pk(self, appraisal_id: int)->Appraisal:
        return Appraisal.objects.filter(id=appraisal_id)
    
    def get_all_appraisal_objects(self)->list:
        
        return Appraisal.objects.all()

    def update(self, appraisal_object_id: int, appraiser_object: UserProfile)->Appraisal:
        try:
            appraisal_object = self.get_appraisal_by_pk(appraisal_object_id)
            if appraisal_object.appraiser != appraiser_object:
                appraisal_object.appraiser = appraiser_object
                appraisal_object.save()
            return appraisal_object
        except Exception as e:
            raise Exception(f"Appraisal Create Repo failed with error: {e}")
