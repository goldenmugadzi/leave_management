from typing import List
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum

from ..repository.kra import KRARepository, KraActivityRepository, TargetScoreRepository, AppraisalKraRepository
from it.users.models import UserProfile
from ..models import YearQuarter, KeyResultArea, Activity, TargetScore, Appraisal, AppraisalKra
from ..helpers.types.kra import KRAType, TargetScoreType, ActivityType, ActivityKraProgressType
from ..helpers.getters import RatingCalculation

class KRAErr(Exception):
    ...

@dataclass
class KRAService:
    kra_repo: KRARepository

    def create_use_case(self, appraisal: Appraisal, data: KRAType)->KeyResultArea:
        try:
            obj = self.kra_repo.create(appraisal=appraisal, data=data)
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

    def create_use_case(self, activity_obj: Activity, data: TargetScoreType)->TargetScore:
        try:
            return self.target_score_repository.create(activity_obj=activity_obj, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to create target-score with error: {e}")

    def update_use_case(self, target_score_obj: TargetScore, data: TargetScoreType)->TargetScore:
        try:
            return self.target_score_repository.update(target_score_obj=target_score_obj, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update target-score with error: {e}")

    def get_by_id_use_case(self, score_id: int)->TargetScore:
        try:
            return self.target_score_repository.get_by_id(score_id=score_id)
        except Exception as e:
            raise KRAErr(f"Failed to get target-score with error: {e}")
        

    def calculate_actual_variance_use_case(self, score_object: TargetScore)->float:
        """Calculate the actual variance between the actual score and the target score."""
        actual_score = score_object.score
        target_score = score_object.activity.agreed_target
        rating_calc_handler = RatingCalculation()
        
        actual_variance = rating_calc_handler.get_actual_variance(actual_score=actual_score, target_score=target_score)
        return actual_variance
    
    def calculate_activity_rating_score_use_case(self, score_object: TargetScore)->float:
        """Calculate the rating score for an activity based on actual variance and allowable variance."""
        activity_obj = score_object.activity
        rating_calc_handler = RatingCalculation()
        
        is_target_met = rating_calc_handler.is_target_met(agreed_target=activity_obj.agreed_target, actual_target=score_object.score)
        variance_range_classifier = rating_calc_handler.classify_variance_range(agreed_target=activity_obj.agreed_target, allowable_variance=activity_obj.allowable_variance, actual_score=score_object.score)
        rating = rating_calc_handler.calculate_rating(is_target_met=is_target_met, variance_range_classify=variance_range_classifier)

        return rating

    def calculate_activity_weighted_score(self, activity_id: int)->float:
        """Calculate the weighted score for an activity by multiplying the activity score by its weight."""
        try:
            score_obj = self.target_score_repository.get_by_activity_id(activity_id=activity_id)
            activity_rate = self.calculate_activity_rating_score_use_case(score_object=score_obj)
            activity_weight = score_obj.activity.weight/100
            weighted_score = activity_rate * activity_weight

            return weighted_score
        except Exception as e:
            raise KRAErr(f"Failed to calculate activity weighted score with error: {e}")


@dataclass
class ActivityService:
    activity_repo: KraActivityRepository

    def create_use_case(self, appraisal_kra_object: AppraisalKra, assigned_user_object: UserProfile|None, data: ActivityType)->Activity:
        try:
            obj = self.activity_repo.create(appraisal_kra_object=appraisal_kra_object, assigned_user_object=assigned_user_object, data=data)
            return obj
        except Exception as e:
            raise KRAErr(f"Failed to create kra activity with error: {e}")

    def fetch_by_appraisal_kra_id_use_case(self, appraisal_kra_id: int)->List[Activity]:
        try:
            return self.activity_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def update_use_case(self, activity_object: Activity, assigned_user: UserProfile, data: ActivityType)->Activity:
        try:
            return self.activity_repo.update(activity_obj=activity_object, assigned_user=assigned_user, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update kra activities with error: {e}")

    def get_by_id_use_case(self, activity_id: int)->Activity:
        try:
            return self.activity_repo.get_activity_by_id(activity_id=activity_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def calculate_total_activities_weighted_scores_per_kra(self, appraisal_kra_id: int, target_score_service_object: TargetScoreService)->float:
        try:
            activities_objects = self.activity_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to fetch activities by appraisal kra pk with error: {e}")

        try:
            total_weight = Decimal(0)

            for activity_obj in activities_objects:
                activity_weighted_score = target_score_service_object.calculate_activity_weighted_score(activity_id=activity_obj.id)
                total_weight += activity_weighted_score

            return total_weight
        except Exception as e:
            raise KRAErr(f"Failed to calculate kra weighted score with error: {e}")
        
    def get_activities_kra_weight_progress(self, appraisal_kra_object: AppraisalKra)->ActivityKraProgressType:
        try:
            activities_qr = self.activity_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_object.id)
            if activities_qr.exists():
                appraisal_kra_weight = appraisal_kra_object.get_weight
                covered_appraisal_kra_weight = activities_qr.aggregate(Sum("weight"))["weight__sum"]
                if appraisal_kra_weight < covered_appraisal_kra_weight:
                    raise Exception(f"Appraisal Kra pk[{appraisal_kra_object.id}]: Total Activities weight cannot be greater than Appraisal Kra weight")
                
                remain_appraisal_kra_weight = appraisal_kra_weight - covered_appraisal_kra_weight
                return ActivityKraProgressType(covered_kra_weight=covered_appraisal_kra_weight, remaining_kra_weight=remain_appraisal_kra_weight)
            
            return ActivityKraProgressType(covered_kra_weight=0, remaining_kra_weight=appraisal_kra_object.get_weight)
        except Exception as e:
            raise KRAErr(f"Failed to get kra activities weight progress with error: {e}")

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
