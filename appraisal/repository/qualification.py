from typing import Dict, Any
from it.users.models import UserQualification, UserProfile
from django.core.files.uploadedfile import UploadedFile


class UserQualificationRepository:
    def create(self, user_object: UserProfile, name: str, file: UploadedFile) -> UserQualification:
        return UserQualification.objects.acreate(user=user_object, name=name, file=file)

    def get_by_user(self, user_object: UserProfile)->UserQualification:
        try:
            object = UserQualification.objects.filter(user=user_object)
            
            return object
        except Exception as e:
            raise ValueError(f"retrieving user qualification objects by user failed with error: {e}")
    