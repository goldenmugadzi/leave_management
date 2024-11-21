from typing import Dict, Any
from dataclasses import dataclass
from django.db import transaction
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, AppraisalRepository, ExperienceRepository
from it.users.models import UserProfile
from ..models import Appraisal
from approve.views import intiate
from ..helpers.types import AppraisalPayloadType


class AppraisalCreationError(Exception):
    """Raised when creating an appraisal fails."""
    pass

@dataclass
class AppraisalService:
    qualification_repository: UserQualificationRepository
    appraisal_experience_repository: AppraisalExperienceRepository
    experience_repository: ExperienceRepository
    appraisal_repository: AppraisalRepository
    
    def create_use_case(self, user_object: UserProfile, data: AppraisalPayloadType)->Appraisal:
        
        try:
            # Atom transaction to create all entries related to appraisal
            with transaction.atomic():
                process_object = intiate(user_object, "Appraisal")
                appraisal_object  = self.appraisal_repository.create(user_object=user_object, process_object=process_object)
                
                # ========== Persist Appraisal Experience ============
                for experience_item in data.experiences:
                    experience_object = self.experience_repository.get_or_create(name=experience_item.name)

                    appraisal_object.experience.add(
                        experience_object,
                        through_defaults={
                            "years_of_experience": experience_item.years_of_experience,
                            "months_of_experience": experience_item.months_of_experience
                        }
                        
                    )
                
                # ========== Persist User Qualification ============
                for qualification_item in data.qualifications:
                    self.qualification_repository.create(name=qualification_item.name, file=qualification_item.file)
                
                return appraisal_object
        except Exception as e:
            raise AppraisalCreationError(f"Failed to create appraisal with error: {e}") 

    def get_all_use_case(self, user_object: UserProfile):
        return Appraisal.objects.filter(user=user_object)