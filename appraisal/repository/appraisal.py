from typing import Dict, Any, List
from django.db.models import Q
from ..models import Appraisal, Experience
from it.users.models import UserProfile
from approve.models import Process
from ..helpers.types import ExperienceType


class AppraisalRepository:
    def create(self, appraisee_object: UserProfile, appraiser_object: UserProfile) -> Appraisal:
        try:
            return Appraisal.objects.create(user=appraisee_object, appraiser=appraiser_object, reviewer=None)
        except Exception as e:
            raise Exception(f"Appraisal Create Repo failed with error: {e}")

    def fetch_by_user_id(self, user_id: UserProfile) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(user__id=user_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_user_id Repo with appraisee or user pk: {user_id}, failed with error: {e}")

    def fetch_by_appraiser_id(self, appraiser_id: int) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(appraiser__id=appraiser_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_appraiser_id Repo with appraiser pk: {appraiser_id}, failed with error: {e}")

    def fetch_by_reviewer_id(self, reviewer_id: int) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(reviewer__id=reviewer_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_reviewer_id Repo with reviewer pk: {reviewer__id}, failed with error: {e}")

    def get_appraisal_by_pk(self, appraisal_id: int)->Appraisal:
        return Appraisal.objects.filter(id=appraisal_id)
    
    def get_all_appraisal_objects(self)->list:
        return Appraisal.objects.all()

    def update(self, appraisal_object: Appraisal, appraiser_object: UserProfile, reviewer_obj: UserProfile, is_accepted_by_appraiser_reviewer: bool)->Appraisal:
        try:
            is_changed = False
            
            if appraisal_object.appraiser != appraiser_object:
                appraisal_object.appraiser = appraiser_object
                is_changed = True
            
            if appraisal_object.reviewer != reviewer_obj:
                appraisal_object.reviewer != reviewer_obj
                is_changed = True
                
            if appraisal_object.is_accepted != is_accepted_by_appraiser_reviewer:
                appraisal_object.is_accepted != is_accepted_by_appraiser_reviewer
                is_changed = True
                
            if is_changed:
                appraisal_object.save()
                
            return appraisal_object
        except Exception as e:
            raise Exception(f"Appraisal update Repo with appraisal pk: {appraisal_object.id}, failed with error: {e}")
