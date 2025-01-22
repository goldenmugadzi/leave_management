from typing import List
from dataclasses import dataclass
from ..models import AppraisalExperience, Appraisal, Experience
from ..repository import AppraisalExperienceRepository

@dataclass
class AppraisalExperienceService:
    appraisal_repo: AppraisalExperienceRepository
    
    def get_by_appraisal_id_use_case(self, appraisal_id)->List[AppraisalExperience]:
        return self.appraisal_repo.get_experiences_by_appraisal_id(appraisal_id=appraisal_id)
    
    def get_by_pk_use_case(self, appraisal_exp_id: int)->AppraisalExperience:
        try:
            return self.appraisal_repo.get_experiences_by_id(experience_id=appraisal_exp_id)
        except Exception as e:
            raise Exception(f"Failed to retrieve appraisal experience with error: {e}")

    def create_use_case(self, appraisal_object: Appraisal, experience_object: Experience, years: int,
            months:int)->AppraisalExperience:
        try:
            obj = self.appraisal_repo.create(appraisal_object=appraisal_object, experience_object=experience_object, years=years, months=months)
            return obj
        except Exception as e:
            raise Exception(f"Failed to create appraisal experience with error: {e}")

    def update_use_case(self, experience_object_id: int, years_of_experience: int, months_of_experience:int)->AppraisalExperience:
        try:
            obj = self.appraisal_repo.update(experience_object_id=experience_object_id, years_of_experience=years_of_experience, months_of_experience=months_of_experience)
            return obj
        except Exception as e:
            raise Exception(f"Failed to update appraisal experience with error: {e}")
