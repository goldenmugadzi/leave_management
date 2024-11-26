from typing import Dict, Any
from it.users.models import UserQualification, UserProfile
from django.core.files.uploadedfile import UploadedFile


class UserQualificationRepository:
    def create(self, user_object: UserProfile, name: str, file: UploadedFile) -> UserQualification:
        return UserQualification.objects.acreate(user=user_object, name=name, file=file)
