from typing import Dict, Any, List
from django.core.exceptions import MultipleObjectsReturned
from ..models import AppraisalExperience, Appraisal, Experience


class ExperienceRepository:
    def get_or_create(self, name: str) -> Experience:
        experience_object, _ = Experience.objects.get_or_create(name=name)
        return experience_object


class AppraisalExperienceRepository:
    def create(self, appraisal_object: Appraisal, experience_object: Experience, years: int = 0, months: int = 0) -> AppraisalExperience|None:
        try:
            obj, created = AppraisalExperience.objects.get_or_create(
                appraisal=appraisal_object,
                experience=experience_object,
                defaults={
                    "years_of_experience": years,
                    "months_of_experience": months
                }
            )
            return obj
        except MultipleObjectsReturned:
            return None
        except Exception as e:
            raise Exception(f"AppraisalExperienceRepository.create failed with error: {e}")

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
    
    def get_experiences_by_id(self, experience_id: int)->AppraisalExperience:
        try:
            obj = AppraisalExperience.objects.filter(id=experience_id).select_related('experience', 'appraisal')
            return obj.first()
        except Exception as e:
            raise Exception(f"retriving AppraisalExperience failed: {e}")

    def update(self, experience_object_id: int, years_of_experience: int, months_of_experience:int)->Experience:
        try:
            changed = False
            experience_object = self.get_experiences_by_id(experience_object_id)
            print("===========>>>> ", experience_object)
            if experience_object.years_of_experience != years_of_experience:
                experience_object.years_of_experience = years_of_experience
                changed = True
            if experience_object.months_of_experience != months_of_experience:
                experience_object.months_of_experience = months_of_experience
                changed = True
            if changed:
                experience_object.save()
            return experience_object
        except Exception as e:
            raise Exception(f"Update AppraisalExperience failed: {e}")
