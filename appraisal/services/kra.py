from typing import List
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

    def get_all_by_quarter_year_use_case(self, quarter_number: int, year_number: int)->List[KeyResultArea]:
        try:
            return self.kra_repo.retrieve(quarter_number=quarter_number, year_number=year_number)
        except Exception as e:
            raise KRAServiceErr(f"Retrieve all kra failed with error: {e}")

    def update_use_case(self, kra_object: KeyResultArea, quarter_obj: YearQuarter, data: KRAType)->KeyResultArea:
        try:
            return self.kra_repo.update(kra_object=kra_object, quarter_obj=quarter_obj, data=data)
        except Exception as e:
            raise KRAServiceErr(f"Failed to update kra with error: {e}")
