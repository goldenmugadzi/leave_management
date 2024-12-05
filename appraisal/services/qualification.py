from typing import List
from dataclasses import dataclass
from ..repository import UserQualificationRepository
from it.users.models import UserQualification

class UserQualificationServiceError(Exception):
    pass

@dataclass
class UserQualificationService:
    user_qualification_repo: UserQualificationRepository
    
    def get_by_user_object_use_case(self, user_object: UserQualification)->List[UserQualification]:
        try:
           return self.user_qualification_repo.get_by_user(user_object=user_object)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to retrieve user qualification by user with error: {e}")
    
