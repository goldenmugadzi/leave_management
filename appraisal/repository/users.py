from django.db.models.query import QuerySet
from it.users.models import UserProfile


class UserProfileRepository:
    def fetch_by_cost_center_pk(self, cost_center_id: int)->QuerySet[UserProfile]:
        try:
            return UserProfile.objects.filter(cost_center__id=cost_center_id)
        except Exception as e:
            raise Exception(f"[UserProfileRepository] fetch_by_cost_center_pk with cost_center_id: {cost_center_id}, failed with error: {e}")