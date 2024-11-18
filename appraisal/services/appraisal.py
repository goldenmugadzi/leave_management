from typing import Dict, Any
from dataclasses import dataclass
from django.db import transaction
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, AppraisalRepository, ExperienceRepository
from it.users.models import UserProfile
from ..models import Appraisal
from approve.views import intiate
from ..helpers.types import AppraisalPayloadType

@dataclass
class AppraisalService:
    qualification_repository: UserQualificationRepository
    appraisal_experience_repository: AppraisalExperienceRepository
    experience_repository: ExperienceRepository
    appraisal_repository: AppraisalRepository
    
    def create_use_case(self, user_object: UserProfile, data: AppraisalPayloadType)->Appraisal:
        
        with transaction.atomic():
            process_object = intiate(user_object, "Appraisal")
            appraisal_object  = self.appraisal_repository.create(user_object=user_object, process_object=process_object)
            
            for experience_item in data.experiences:
                experience_object = self.experience_repository.get_or_create(name=experience_item["name"])
                
                for appraisal_experience in data.appraisal_experiences:
                    appraisal_object.experience.aadd(
                        appraisal_object,
                        experience_object,
                        through_defaults={
                            "years_of_experience": appraisal_experience["years_of_experience"],
                            "months_of_experience": appraisal_experience["months_of_experience"]
                        }
                        
                    )