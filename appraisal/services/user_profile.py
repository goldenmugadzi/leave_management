from typing import Dict, Any
from dataclasses import dataclass
from ..repository import UserProfileRepository
from it.users.models import UserProfile
from ..helpers import get_changed_fields


@dataclass
class UserProfileService:
    user_profile_repository: UserProfileRepository
    
    def update_user(self, user_object, data: Dict[str, Any])->UserProfile:
        current_user = self.user_profile_repository.get_user_profile_by_id(user_id=user_object.id)
        try:
            changed_data = get_changed_fields(model_object=current_user, data=data)
            return self.user_profile_repository.update_user_profile(user=current_user,  data=changed_data)
        except Exception as e:
            error_str = f"Update Service failed with error: {e}"
            raise ValueError(error_str)