from typing import Dict, Any
from it.users.models import UserQualification
from django.core.files.uploadedfile import UploadedFile

class UserQualificationRepository:
    def create(self, name: str, file: UploadedFile)->UserQualification:
        return UserQualification.objects.acreate(name=name, file=file)