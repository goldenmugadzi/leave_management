from django.db.models.query import QuerySet
from it.users.models import UserProfile


class UserProfileRepository:
    def fetch_by_cost_center_pk(self, cost_center_id: int)->QuerySet[UserProfile]:
        try:
            return UserProfile.objects.filter(cost_center__id=cost_center_id).select_related('cost_center')
        except Exception as e:
            raise Exception(f"[UserProfileRepository] fetch_by_cost_center_pk with cost_center_id: {cost_center_id}, failed with error: {e}")
        
    def get_by_pk(self, user_id: int)->UserProfile|None:
        try:
            qr = UserProfile.objects.filter(id=user_id)
            return qr.first()
        except Exception as e:
            raise Exception(f"[UserProfileRepository] get_by_pk with user_id: {user_id}, failed with error: {e}")
        
    