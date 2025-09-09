from typing import Dict, Any
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.core.files.storage import default_storage


from it.users.models import UserQualification, UserProfile, UserExperience

class UserQualificationRepository:
    def create(self, user_object: UserProfile, name: str, file: UploadedFile=None) -> UserQualification:
        try:
            return UserQualification.objects.create(user=user_object, name=name, file=file)
        except Exception as e:
            raise Exception(f"create user qualification repo failed with error: {e}")
    
    def get_by_user(self, user_object: UserProfile)->UserQualification:
        try:
            object = UserQualification.objects.filter(user=user_object)
            
            return object
        except Exception as e:
            raise Exception(f"retrieving user qualification objects by user failed with error: {e}")
    
    def fetch_by_user(self, user_id: int)->UserQualification:
        try:
            return UserQualification.objects.filter(user__id=user_id)
        except Exception as e:
            raise Exception(f"fetch user qualification objects by user pk: {user_id}, failed with error: {e}")
    
    def get_by_id(self, qualification_id: int)->UserQualification:
        try:
            object = UserQualification.objects.get(id=qualification_id)
            return object
        except Exception as e:
            raise Exception(f"retrieving user qualification objects by pk failed with error: {e}")
    
    def update(self, qualification_object_id: int, name: str, file: UploadedFile)->UserQualification:
        try:
            changed = False
            qualification_object = self.get_by_id(qualification_object_id)
            if qualification_object.name != name:
                qualification_object.name = name
                changed = True
            if file and (not qualification_object.file or qualification_object.file.name != file.name):
                
                existing_file = qualification_object.file.path
                if not default_storage.exists(existing_file):
                    raise Exception("Qualification file does not exist")
                
                default_storage.delete(existing_file) 
                
                qualification_object.file = file
                changed = True
            if changed:
                qualification_object.save()
            return qualification_object
        except Exception as e:
            raise Exception(f"Update user qualification failed with error: {e}")
        
        
class UserExperienceRepository:
    def create(self, user_object: UserProfile, name: str, experience_from_date: str, experience_to_date: str=None) -> UserExperience:
        """
            Creates a new UserExperience entry for the given user.
            Args:
                user_object (UserProfile): The user for whom the experience is being created.
                name (str): The title or name of the experience (e.g., 'Database Administration').
                experience_from_date (str): The start date of the experience in 'YYYY-MM-DD' format.
                experience_to_date (Optional[str], optional): The end date of the experience. Defaults to None (ongoing).

            Returns:
                Optional[UserExperience]: The created UserExperience object if successful, or None if the experience
                already exists for the user.

            Raises:
                Exception: For any unexpected errors during creation.
        """
        try:
            return UserExperience.objects.create(user=user_object, name=name, experience_from=experience_from_date, experience_to=experience_to_date)
        except IntegrityError:
            return None
        except Exception as e:
            raise Exception(f"[UserExperienceRepository] create repo failed with error: {e}")
    
    def get_by_user_id(self, user_id: int)->UserExperience:
        try:
            qr = UserExperience.objects.filter(user__id=user_id)
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"[UserExperienceRepository] get_by_user_id with user pk: {user_id}, failed with error: {e}")
    
    def get_by_id(self, user_exp_id: int)->UserExperience:
        try:
            qr = UserExperience.objects.filter(id=user_exp_id)
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"[UserExperienceRepository] get_by_id with user experience pk: {user_exp_id}, failed with error: {e}")
        
    def update(self, user_experience_obj: UserExperience, name: str, experience_from_date: str, experience_to_date: str=None)->UserExperience:
        try:
            changed = False
            
            if user_experience_obj.name != name:
                user_experience_obj.name = name
                changed = True
            
            if user_experience_obj.experience_from != experience_from_date:
                user_experience_obj.experience_from = experience_from_date
                changed = True
            
            if user_experience_obj.experience_to != experience_to_date:
                user_experience_obj.experience_to = experience_to_date
                changed = True

            if changed:
                user_experience_obj.save()
            return user_experience_obj
        except Exception as e:
            raise Exception(f"[UserExperienceRepository] update for user expirence pk: {user_experience_obj.id}, failed with error: {e}")
        
    def fetch_by_user_id(self, user_id)->QuerySet[UserExperience]:
        try:
            return UserExperience.objects.filter(user__id=user_id)
        except Exception as e:
            raise Exception(f"[UserExperienceRepository] fetch_by_user_id with user pk: {user_id}, failed with error: {e}")
