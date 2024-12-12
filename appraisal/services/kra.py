from dataclasses import dataclass
from ..repository.kra import KRARepository
from it.users.models import UserProfile
from ..models import YearQuarter, KeyResultArea
from ..helpers.types.kra import KRAType

class KRAServiceErr(Exception):
    ...

@dataclass
class KRAService:
    kra_repo: KRARepository

    def create_use_case(self, quarter_obj: YearQuarter, creator_obj: UserProfile, data: KRAType)->KeyResultArea:
        try:
            obj = self.kra_repo.create(quarter_obj=quarter_obj, creator_obj=creator_obj, data=data)
            return obj
        except Exception as e:
            raise KRAServiceErr(f"Failed to create kra with error: {e}")
