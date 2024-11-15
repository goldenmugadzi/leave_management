from typing import Dict, Any
from it.users.models import UserProfile


class UserProfileRepository:
    
    def get_user_profile_by_id(self, user_id: int)->UserProfile:
        try:
            return UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            raise ValueError("User not found")
    
    
    def update_user_profile(self, user: UserProfile, data: Dict[str, Any]) -> UserProfile:
        for field, value in data.items():
            setattr(user, field, value)
        user.save()  # persist changes
        return user