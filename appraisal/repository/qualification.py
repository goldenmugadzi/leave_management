from typing import Dict, Any
from it.users.models import UserQualification, UserProfile
from django.core.files.uploadedfile import UploadedFile


class UserQualificationRepository:
    def create(self, user_object: UserProfile, name: str, file: UploadedFile) -> UserQualification:
        try:
            return UserQualification.objects.create(user=user_object, name=name, file=file)
        except Exception as e:
            raise Exception(f"create user qualification repo failed with error: {e}")
    
    def get_by_user(self, user_object: UserProfile)->UserQualification:
        try:
            object = UserQualification.objects.filter(user=user_object)
            
            return object
        except Exception as e:
            raise ValueError(f"retrieving user qualification objects by user failed with error: {e}")
    
    def get_by_id(self, qualification_id: int)->UserQualification:
        try:
            object = UserQualification.objects.get(id=qualification_id)
            return object
        except Exception as e:
            raise ValueError(f"retrieving user qualification objects by pk failed with error: {e}")
    
    def update(self, qualification_object_id: int, name: str, file: UploadedFile)->UserQualification:
        try:
            changed = False
            qualification_object = self.get_by_id(qualification_object_id)
            if qualification_object.name != name:
                qualification_object.name = name
                changed = True
            if file and (not qualification_object.file or qualification_object.file.name != file.name):
                qualification_object.file = file
                changed = True
            if changed:
                qualification_object.save()
            return qualification_object
        except Exception as e:
            raise Exception(f"Update user qualification failed with error: {e}")