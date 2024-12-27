from typing import List
from dataclasses import dataclass

from ..repository.kra import KRARepository, KraActivityRepository, ActivityTargetRepository, TargetScoreRepository
from it.users.models import UserProfile
from ..models import YearQuarter, KeyResultArea, Activity,Target, TargetScore
from ..helpers.types.kra import KRAType, TargetType, TargetScoreType

class KRAErr(Exception):
    ...

@dataclass
class KRAService:
    kra_repo: KRARepository

    def create_use_case(self, quarter_obj: YearQuarter, creator_obj: UserProfile, data: KRAType)->KeyResultArea:
        try:
            obj = self.kra_repo.create(quarter_obj=quarter_obj, creator_obj=creator_obj, data=data)
            return obj
        except Exception as e:
            raise KRAErr(f"Failed to create kra with error: {e}")

    def get_all_by_quarter_year_use_case(self, quarter_number: int, year_number: int)->List[KeyResultArea]:
        try:
            return self.kra_repo.retrieve(quarter_number=quarter_number, year_number=year_number)
        except Exception as e:
            raise KRAErr(f"Retrieve all kra failed with error: {e}")

    def update_use_case(self, kra_object: KeyResultArea, quarter_obj: YearQuarter, data: KRAType)->KeyResultArea:
        try:
            return self.kra_repo.update(kra_object=kra_object, quarter_obj=quarter_obj, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update kra with error: {e}")

    def get_kra_by_pk_use_case(self, kra_id: int)->KeyResultArea:
        try:
            return self.kra_repo.retrieve_by_pk(kra_id=kra_id)
        except Exception as e:
            raise KRAErr(f"Retriev kra by id failed with error: {e}")

@dataclass
class ActivityService:
    activity_repo: KraActivityRepository

    def create_use_case(self, kra_object: KeyResultArea, assigned_user: UserProfile, data: KRAType)->Activity:
        try:
            obj = self.activity_repo.create(kra_obj=kra_object, assigned_user=assigned_user, data=data)
            return obj
        except Exception as e:
            raise KRAErr(f"Failed to create kra activity with error: {e}")

    def fetch_by_kra_id_use_case(self, kra_id: int)->List[Activity]:
        try:
            return self.activity_repo.fetch_by_kra_id(kra_id=kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def update_use_case(self, activity_object: Activity, assigned_user: UserProfile, data: KRAType)->Activity:
        try:
            return self.activity_repo.update(activity_obj=activity_object, assigned_user=assigned_user, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update kra activities with error: {e}")

    def get_by_id_use_case(self, activity_id: int)->Activity:
        try:
            return self.activity_repo.get_activity_by_id(activity_id=activity_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")


@dataclass
class TargetService:
    target_repository: ActivityTargetRepository

    def fetch_by_activity_use_case(self, activity_id: int)->List[Target]:
        try:
            return self.target_repository.fetch_by_activity_id(activity_id=activity_id)
        except Exception as e:
            raise KRAErr(f"Retrieve all targets by activity id failed with error: {e}")

    def create_use_case(self, activity_obj: Activity, payload: TargetType)->Target:
        try:
            return self.target_repository.create(activity_obj=activity_obj, data=payload)
        except Exception as e:
            raise KRAErr(f"Create failed with error: {e}")

    def get_by_id_use_case(self, target_id: int)->Target:
        try:
            return self.target_repository.get_target_by_id(target_id=target_id)
        except Exception as e:
            raise KRAErr(f"Get by pk failed with error: {e}")

    def update_use_case(self, target_obj: Target, payload: TargetType)->Target:
        try:
            return self.target_repository.update(target_obj=target_obj, payload=payload)
        except Exception as e:
            raise KRAErr(f"Failed to update target with error: {e}")

@dataclass
class TargetScoreService:
    target_score_repository: TargetScoreRepository

    def create_use_case(self, target_obj: Target, data: TargetScoreType)->TargetScore:
        try:
            return self.target_score_repository.create(target_obj=target_obj, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to create target-score with error: {e}")
