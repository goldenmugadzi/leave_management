from dataclasses import dataclass
from ..repository.users import UserProfileRepository

@dataclass
class UserProfileService:
    user_profile_repo: UserProfileRepository
    
    def fetch_cost_center_users_from_user_id(self, user_id: int):
        """Use case handler that uses user id to get user instance and fetch all users from the user instance cost center id.

        Args:
            user_id (int): pk of user instance

        Raises:
            Exception: Unexpected errors

        Returns:
            _type_: None if user is None and users queryset if user has cost center or user instance is not None
        """
        try:
            user_obj = self.user_profile_repo.get_by_pk(user_id=user_id)
            if user_obj is None or not user_obj.cost_center:
                return None
            
            return self.user_profile_repo.fetch_by_region_id(region_id=user_obj.region.id)
        except Exception as e:
            raise Exception(f"[UserProfileService] fetch_by_region_id with user_id: {user_id}, failed with error: {e}")
        
    