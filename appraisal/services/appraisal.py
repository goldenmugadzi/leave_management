from typing import Dict, Annotated, List, Union
from dataclasses import dataclass
from django.db import transaction
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, AppraisalRepository, ExperienceRepository
from it.users.models import UserProfile, UserQualification
from ..models import Appraisal, Experience
from approve.models import Process
from ..helpers.types import AppraisalPayloadType, ExperienceType


class AppraisalCreationError(Exception):
    """Raised when creating an appraisal fails."""
    pass

@dataclass
class AppraisalService:
    qualification_repository: UserQualificationRepository
    appraisal_experience_repository: AppraisalExperienceRepository
    experience_repository: ExperienceRepository
    appraisal_repository: AppraisalRepository

    def create_use_case(self, user_object: UserProfile, process_object: Process, appraiser: UserProfile, data: AppraisalPayloadType)->Appraisal:

        try:
            # Atom transaction to create all entries related to appraisal
            with transaction.atomic():
                appraisal_object = self.appraisal_repository.create(user_object=user_object, process_object=process_object, appraiser_object=appraiser)

                # ========== Persist Appraisal Experience ============
                for experience_item in data.experiences:
                    experience_object = self.experience_repository.get_or_create(name=experience_item.name)
                    self.appraisal_repository.add_experience(appraisal_object=appraisal_object, experience_object=experience_object, data=experience_item)

                # ========== Persist User Qualification ============
                for qualification_item in data.qualifications:
                    self.qualification_repository.create(user_object=user_object, name=qualification_item.name, file=qualification_item.file)

                return appraisal_object
        except Exception as e:
            raise AppraisalCreationError(f"Failed to create appraisal with error: {e}")

    def update_use_case(self, appraisal_object: Appraisal, experience_objects: List[Experience], qualifications: List[UserQualification])->Dict[str, Union[Appraisal, List[Experience], List[UserQualification]]]:
        try:
            # ======== Appraisal ========
            appraisal_object = self.appraisal_repository.update(appraisal_object_id=appraisal_object.id, appraiser_object=appraisal_object.appraiser)
            
            
            # ======== Update Experiences ========
            existing_experiences = self.appraisal_experience_repository.get_experiences_by_appraisal_id(
                appraisal_object.id
            )
            
            existing_experience_names = {exp.experience.name for exp in existing_experiences}
            payload_experience_names = {exp.name for exp in experience_objects}

            # Remove experiences not in the payload
            for existing_exp in existing_experiences:
                if existing_exp.experience.name not in payload_experience_names:
                    self.appraisal_repository.remove_experience(
                        appraisal_object=appraisal_object,
                        experience_object=existing_exp.experience,
                    )
            
            # Add or update experiences in the payload
            for exp in experience_objects:
                experience_object = self.experience_repository.get_or_create(name=exp.name)
                self.appraisal_repository.add_experience(
                    appraisal_object=appraisal_object,
                    experience_object=experience_object,
                    data=exp,
                )
            
            # ======== Update Qualifications ========
            existing_qualifications = self.qualification_repository.get_by_user(
                user_object=appraisal_object.user
            )
            existing_qualification_names = {qual.name for qual in existing_qualifications}
            payload_qualification_names = {qual.name for qual in qualifications}

            # Remove qualifications not in the payload
            for existing_qual in existing_qualifications:
                if existing_qual.name not in payload_qualification_names:
                    existing_qual.delete()

            # Add or update qualifications in the payload
            for qual in qualifications:
                self.qualification_repository.create(
                    user_object=appraisal_object.user,
                    name=qual.name,
                    file=qual.file,
                )

            return {
                "appraisal_object": appraisal_object,
                "experience_objects": experience_objects,
                "qualification_objects": qualifications,
            }

        except Exception as e:
            raise AppraisalCreationError(f"Failed to update appraisal with error: {e}")
            
            # # ============= Experience ==========
            # # Update
            # for experience in experience_objects:
            #     experience_object = self.appraisal_experience_repository.update(
            #         experience_object_id=experience.id,
            #         years_of_experience=experience.years_of_experience,
            #         months_of_experience=experience.months_of_experience
            #     )
            #     experience_list.append(experience_object)

            # existing_experience_objects = appraisal_object.experiences.all()
            # existing_experience_objects_set = set(existing_experience_objects)
            # payload_experience_objects_set = set(experience_objects)
            
            # # Removal
            # removed_experience_objects = list(existing_experience_objects_set - payload_experience_objects_set)
            # for removed_experience_object in removed_experience_objects:
            #     self.appraisal_repository.remove_experience(appraisal_object=appraisal_object, experience_object=removed_experience_object)
        
            # # Add
            # added_experience_objects = list(payload_experience_objects_set - existing_experience_objects_set)
            # for added_experience_object in added_experience_objects:
            #     experience_object = appraisal_object.experience.
            #     data = ExperienceType(name=added_experience_object.name, years_of_experience=added_experience_object.)
            #     self.appraisal_repository.remove_experience(appraisal_object=appraisal_object, experience_object=removed_experience_object)

    
    def get_appraisal_by_user_use_case(self, user_object: UserProfile):
        return self.appraisal_repository.get_user_appraisal_objects(user_object=user_object)
    
    def get_appraisal_by_pk_use_case(self, appraisal_id: int)->Appraisal:
        return self.appraisal_repository.get_appraisal_by_pk(appraisal_id=appraisal_id)
    
    def get_all_use_case(self):
        return self.appraisal_repository.get_all_appraisal_objects()
