from typing import List, Dict, Annotated
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.db.models.query import QuerySet

from ..repository.kra import KRARepository
from it.users.models import Designations
from ..models import YearQuarter, KeyResultArea, Appraisal
from ..helpers.types.kra import KRAType, TargetScoreType, ActivityType, WeightProgressType, PerformanceDimensionType
from ..helpers.getters import RatingCalculation

class KRAErr(Exception):
    ...

@dataclass
class KRAService:
    kra_repo: KRARepository

    def create_use_case(self, data: KRAType, appraisee_designation: Designations)->KeyResultArea:
        try:
            obj = self.kra_repo.create(data=data, designation=appraisee_designation)
            return obj
        except Exception as e:
            raise KRAErr(f"Failed to create kra with error: {e}")

    def get_all_by_quarter_year_use_case(self, quarter_number: int, year_number: int)->List[KeyResultArea]:
        try:
            return self.kra_repo.retrieve(quarter_number=quarter_number, year_number=year_number)
        except Exception as e:
            raise KRAErr(f"Retrieve all kra failed with error: {e}")

    def fetch_by_quarter_year_appraisal_pk_use_case(self, quarter_number: int, year_number: int, appraisal_id: int)->List[KeyResultArea]:
        try:
            return self.kra_repo.retrieve_quarter_appraisal_id(quarter_number=quarter_number, year_number=year_number, appraisal_id=appraisal_id)
        except Exception as e:
            raise KRAErr(f"Retrieve all kra failed with error: {e}")

    def update_use_case(self, kra_object: KeyResultArea, appraisee_designation: Designations, data: KRAType)->KeyResultArea:
        try:
            return self.kra_repo.update(kra_object=kra_object, designation=appraisee_designation, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update kra with error: {e}")

    def get_kra_by_pk_use_case(self, kra_id: int)->KeyResultArea:
        try:
            return self.kra_repo.retrieve_by_pk(kra_id=kra_id)
        except Exception as e:
            raise KRAErr(f"Retriev kra by id failed with error: {e}")

