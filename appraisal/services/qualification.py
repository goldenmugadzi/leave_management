from typing import List
from dataclasses import dataclass
from django.core.files.uploadedfile import UploadedFile
from ..repository import UserQualificationRepository
from it.users.models import UserQualification, UserProfile

class UserQualificationServiceError(Exception):
    pass

@dataclass
class UserQualificationService:
    user_qualification_repo: UserQualificationRepository
    
    def create_use_case(self, user_object: UserProfile, name: str, file: UploadedFile)->UserQualification:
        try:
            return self.user_qualification_repo.create(user_object=user_object, name=name, file=file)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to create user qualification with error: {e}")
    
    def update_use_case(self, qualification_object_id: int, name: str, file: UploadedFile)->UserQualification:
        try:
            return self.user_qualification_repo.update(qualification_object_id=qualification_object_id, name=name, file=file)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to update user qualification with error: {e}")
    
    
    def get_by_user_object_use_case(self, user_object: UserQualification)->List[UserQualification]:
        try:
           return self.user_qualification_repo.get_by_user(user_object=user_object)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to retrieve user qualification by user with error: {e}")
    
    def get_by_pk_use_case(self, qualification_id: int)->UserQualification:
        try:
           return self.user_qualification_repo.get_by_id(qualification_id=qualification_id)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to retrieve user qualification by pk with error: {e}")
    
