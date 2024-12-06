from typing import Dict, Any, List
from ..models import AppraisalExperience, Appraisal, Experience


class ExperienceRepository:
    def get_or_create(self, name: str) -> Experience:
        experience_object, _ = Experience.objects.get_or_create(name=name)
        return experience_object


class AppraisalExperienceRepository:
    def create(self, appraisal_object: Appraisal, experience_object: Experience, years: int = 0,
               months: int = 0) -> AppraisalExperience:
        return AppraisalExperience.objects.create(
            appraisal=appraisal_object,
            experience=experience_object,
            years_of_experience=years,
            months_of_experience=months
        )

    def bulk_create(self, instances: List[AppraisalExperience]):
        try:
            AppraisalExperience.objects.abulk_create(instances)
        except Exception as e:
            raise Exception(f"bulk creation of AppraisalExperience failed: {e}")
        
    def get_experiences_by_appraisal_id(self, appraisal_id: int)->List[AppraisalExperience]:
        try:
            return AppraisalExperience.objects.filter(appraisal__id=appraisal_id).select_related('experience', 'appraisal')
        except Exception as e:
            raise Exception(f"retriving AppraisalExperience failed: {e}")
