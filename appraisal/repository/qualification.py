from typing import Dict, Any
from it.users.models import UserQualification

class UserQualificationRepository:
    def create(self, data: Dict[str, Any])->UserQualification:
        return UserQualification.objects.create(**data)