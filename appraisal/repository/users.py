from typing import List
from django.db.models.query import QuerySet
from it.users.models import UserProfile
from loguru import logger
from django.db import transaction

class UserProfileRepository:
    def fetch_by_cost_center_pk(self, cost_center_id: int)->QuerySet[UserProfile]:
        try:
            return UserProfile.objects.filter(cost_center__id=cost_center_id).select_related('cost_center')
        except Exception as e:
            raise Exception(f"[UserProfileRepository] fetch_by_cost_center_pk with cost_center_id: {cost_center_id}, failed with error: {e}")
        
    def bulk_update(self, objs: List[UserProfile], fields: List[str]) -> bool:
        """
        Efficiently updates multiple UserProfile records in bulk.

        Args:
            objs (List[UserProfile]): List of user profile objects to update.
            fields (List[str]): List of model field names to update.

        Returns:
            bool: True if successful, raises exception otherwise.
        """
        if not objs:
            logger.warning("[UserProfileRepository] No user profiles provided for bulk update.")
            return False

        try:
            with transaction.atomic():
                UserProfile.objects.bulk_update(objs, fields)
            logger.info(f"[UserProfileRepository] Successfully bulk updated {len(objs)} users.")
            return True
        except Exception as e:
            logger.error(f"[UserProfileRepository] bulk_update failed: {e}", exc_info=True)
            raise Exception(f"[UserProfileRepository] bulk_update failed with error: {e}")
        
    def fetch_by_region_id_hr_section(self, region_id: int)->QuerySet[UserProfile]:
        try:
            return UserProfile.objects.filter(
                region__id=region_id,
                section__section__icontains="human resources"
                ).select_related('cost_center', 'section')        
        except Exception as e:
            raise Exception(f"[UserProfileRepository] fetch_by_region_id_hr_section with region id: {region_id}, failed with error: {e}")
        
    def fetch_by_region_id(self, region_id: int)->QuerySet[UserProfile]:
        try:
            return UserProfile.objects.filter(
                region__id=region_id
                ).select_related('cost_center', 'section')       
        except Exception as e:
            raise Exception(f"[UserProfileRepository] fetch_by_region_id with region id: {region_id}, failed with error: {e}")
        
    def get_by_pk(self, user_id: int)->UserProfile|None:
        try:
            qr = UserProfile.objects.filter(id=user_id)
            return qr.first()
        except Exception as e:
            raise Exception(f"[UserProfileRepository] get_by_pk with user_id: {user_id}, failed with error: {e}")
        
    
    def get_by_username(self, username: str)->UserProfile|None:
        try:
            qr = UserProfile.objects.filter(username=username)
            return qr.first()
        except Exception as e:
            raise Exception(f"[UserProfileRepository] get_by_username with username: {username}, failed with error: {e}")
    
    