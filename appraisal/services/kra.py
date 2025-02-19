from typing import List
from dataclasses import dataclass
from decimal import Decimal

from ..repository.kra import KRARepository, KraActivityRepository, TargetScoreRepository, AppraisalKraRepository
from it.users.models import UserProfile
from ..models import YearQuarter, KeyResultArea, Activity, TargetScore, Appraisal
from ..helpers.types.kra import KRAType, TargetScoreType
from ..helpers.getters import get_actual_variance, get_within_condition, get_rating

class KRAErr(Exception):
    ...

@dataclass
class KRAService:
    kra_repo: KRARepository

    def create_use_case(self, quarter_obj: YearQuarter, creator_obj: UserProfile, appraisal_obj: Appraisal, data: KRAType)->KeyResultArea:
        try:
            obj = self.kra_repo.create(quarter_obj=quarter_obj, creator_obj=creator_obj, data=data, appraisal_obj=appraisal_obj)
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
class TargetScoreService:
    target_score_repository: TargetScoreRepository

    def create_use_case(self, target_obj, data: TargetScoreType)->TargetScore:
        try:

            return self.target_score_repository.create(target_obj=target_obj, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to create target-score with error: {e}")

    def update_use_case(self, target_score_obj: TargetScore, data: TargetScoreType)->TargetScore:
        try:
            return self.target_score_repository.update(target_score_obj=target_score_obj, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update target-score with error: {e}")

    def get_by_target_id_use_case(self, target_id: int)->TargetScore:
        try:
            return self.target_score_repository.get_by_target_id(target_id=target_id)
        except Exception as e:
            raise KRAErr(f"Failed to get target-score with error: {e}")

    def calculate_activity_score_use_case(self, target_id: int)->float:
        """
        Calculates the score for a specific activity based on its aggregated target scores and weight.

        Args:
            target_id (int): The unique identifier of the activity for which the score is to be calculated.

        Returns:
            float: The calculated activity score in percentage.


        Raises:
            Exception: If there is an error in retrieving the aggregated target scores.
        """
        try:
            target_score_obj = self.target_score_repository.get_by_target_id(target_id=target_id)
        except Exception as e:
            raise KRAErr(f"Activity Score calculation failed with error: {e}")

        actual_score = target_score_obj.score
        target_score = target_score_obj.target.agreed_target
        actual_variance = get_actual_variance(actual_score=actual_score, target_score=target_score)

        allowable_variance = target_score_obj.target.allowable_variance
        within_condition_value = get_within_condition(actual_variance=actual_variance, allowable_variance=allowable_variance)

        rating = get_rating(actual_variance=actual_variance, within_condition=within_condition_value)

        return rating

    def calculate_average_weighted_score_per_activity(self, activity_id: int)->float:
        """
            Calculate the weighted average score for an activity based on target scores and their respective weights.

            This method fetches all target scores for a given activity, calculates the weighted sum of the scores,
            and divides it by the total weight to return the weighted average score.

            Args:
                activity_id (int): The ID of the activity for which the weighted score is calculated.

            Returns:
                float: The weighted average score of the activity.

            Raises:
                KRAErr: If there is an error during calculation, including when the total weight is zero
                        or issues with fetching target scores.
                Exception: If the total weight of all target scores is zero.
        """
        try:
            target_scores = self.target_score_repository.fetch_by_activity_id(activity_id=activity_id)

            weighted_sum = 0
            total_weight = 0

            for target_score_obj in target_scores:
                target_score = target_score_obj.score
                target_weight = target_score_obj.target.weight
                weighted_sum += target_score * target_weight
                total_weight += target_weight

            if total_weight == 0:
                raise Exception("Total weight for activity cannot be zero.")

            return weighted_sum/total_weight
        except Exception as e:
            raise KRAErr(f"Failed to calculate activity score with error: {e}")


@dataclass
class ActivityService:
    activity_repo: KraActivityRepository

    def create_use_case(self, kra_object: KeyResultArea, data: KRAType)->Activity:
        try:
            obj = self.activity_repo.create(kra_obj=kra_object, data=data)
            return obj
        except Exception as e:
            raise KRAErr(f"Failed to create kra activity with error: {e}")

    def fetch_by_kra_id_use_case(self, kra_id: int)->List[Activity]:
        try:
            return self.activity_repo.fetch_by_kra_id(kra_id=kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def update_use_case(self, activity_object: Activity, assigned_user: UserProfile, appraiser: UserProfile, data: KRAType)->Activity:
        try:
            return self.activity_repo.update(activity_obj=activity_object, assigned_user=assigned_user, appraiser=appraiser, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update kra activities with error: {e}")

    def get_by_id_use_case(self, activity_id: int)->Activity:
        try:
            return self.activity_repo.get_activity_by_id(activity_id=activity_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def calculate_weighted_score_per_kra(self, kra_id: int, target_score_service_object: TargetScoreService)->float:
        try:
            activities_objects = self.activity_repo.fetch_by_kra_id(kra_id=kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to fetch activities by pk with error: {e}")

        try:
            # Use Decimal for precision
            weighted_sum = Decimal(0)
            total_weight = Decimal(0)

            for activity_obj in activities_objects:
                # Convert weight to Decimal for compatibility
                activity_weight = Decimal(str(activity_obj.weight))

                # Ensure activity_weighted_score is Decimal-compatible
                activity_weighted_score = Decimal(
                    target_score_service_object.calculate_average_weighted_score_per_activity(activity_id=activity_obj.id)
                )

                # Perform calculations
                weighted_sum += activity_weighted_score * activity_weight
                total_weight += activity_weight

            if total_weight == 0:
                raise Exception("Total weight cannot be zero.")

            # Return the weighted score as a float
            return float(weighted_sum / total_weight)
        except Exception as e:
            raise KRAErr(f"Failed to calculate kra weighted score with error: {e}")

@dataclass
class AppraisalKraService:
    repo: AppraisalKraRepository

    def create_use_case(self, appraisal_object: Appraisal, quarter_obj: YearQuarter, kra_obj: KeyResultArea=None, activity_object: Activity=None):
        try:
            return self.repo.create(appraisal_object=appraisal_object, quarter_obj=quarter_obj, kra_obj=kra_obj, activity_object=activity_object)
        except Expeption as e:
            raise KRAErr(f"Failed to create appraisal kra with error: {e}")

    def fetch_by_quarter_year_appraisal_pk_use_case(self, quarter_number: int, year_number: int, appraisal_id: int):
        try:
            return self.repo.retrieve_quarter_appraisal_id(quarter_number=quarter_number, year_number=year_number, appraisal_id=appraisal_id)
        except Exception as e:
            raise KRAErr(f"Retrieve all appraisal kra failed with error: {e}")
