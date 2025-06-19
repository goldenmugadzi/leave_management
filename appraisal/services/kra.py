from typing import List, Dict, Annotated
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.db.models.query import QuerySet

from ..repository.kra import KRARepository, KraActivityRepository, TargetScoreRepository, AppraisalKraRepository, PerformanceDimensionRepository
from it.users.models import Designations
from ..models import YearQuarter, KeyResultArea, Activity, TargetScore, Appraisal, AppraisalKra, PerformanceDimension
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

@dataclass
class TargetScoreService:
    target_score_repository: TargetScoreRepository

    def create_use_case(self, performance_dimension_obj: PerformanceDimension, data: TargetScoreType)->TargetScore:
        try:
            return self.target_score_repository.create(performance_dimension=performance_dimension_obj, data=data)
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
        target_score = score_object.performance_dimension.agreed_target
        rating_calc_handler = RatingCalculation()
        
        actual_variance = rating_calc_handler.get_actual_variance(actual_score=actual_score, target_score=target_score)
        return actual_variance
    
    def calculate_performance_dimension_rating_score_use_case(self, score_object: TargetScore)->float:
        """Calculate the rating score for an performance dimension based on actual variance and allowable variance."""
        performance_dimension_obj = score_object.performance_dimension
        rating_calc_handler = RatingCalculation()
        
        is_target_met = rating_calc_handler.is_target_met(agreed_target=performance_dimension_obj.agreed_target, actual_target=score_object.score)
        variance_range_classifier = rating_calc_handler.classify_variance_range(agreed_target=performance_dimension_obj.agreed_target, allowable_variance=performance_dimension_obj.allowable_variance, actual_score=score_object.score)
        rating = rating_calc_handler.calculate_rating(is_target_met=is_target_met, variance_range_classify=variance_range_classifier)

        return rating

    def calculate_performance_dimension_weighted_score(self, performance_dimension_id: int)->float:
        """Calculate the weighted score for an performance dimension by multiplying the performance dimension score by its weight."""
        try:
            score_obj = self.target_score_repository.get_by_performance_dimension_id(performance_dimension_id=performance_dimension_id)
            performance_dimension_rate = self.calculate_performance_dimension_rating_score_use_case(score_object=score_obj)
            performance_dimension_weight = score_obj.performance_dimension.weight/100
            weighted_score = performance_dimension_rate * performance_dimension_weight

            return weighted_score
        except Exception as e:
            raise KRAErr(f"Failed to calculate performance dimension weighted score with error: {e}")


@dataclass
class ActivityService:
    activity_repo: KraActivityRepository

    def create_use_case(self, appraisal_kra_object: AppraisalKra, data: ActivityType)->Activity:
        try:
            obj = self.activity_repo.create(appraisal_kra_object=appraisal_kra_object,  data=data)
            return obj
        except Exception as e:
            raise KRAErr(f"Failed to create kra activity with error: {e}")

    def fetch_by_appraisal_kra_id_use_case(self, appraisal_kra_id: int)->List[Activity]:
        try:
            return self.activity_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def update_use_case(self, activity_object: Activity, data: ActivityType)->Activity:
        try:
            return self.activity_repo.update(activity_obj=activity_object, data=data)
        except Exception as e:
            raise KRAErr(f"Failed to update kra activities with error: {e}")

    def get_by_id_use_case(self, activity_id: int)->Activity:
        try:
            return self.activity_repo.get_activity_by_id(activity_id=activity_id)
        except Exception as e:
            raise KRAErr(f"Failed to retrieve kra activities with error: {e}")

    def calculate_total_activities_weighted_scores_per_appraisal_kra(self, appraisal_kra_id: int, target_score_service_object: TargetScoreService, performance_dimension_repo: PerformanceDimensionRepository)->float:
        try:
            performance_dimension_qr = performance_dimension_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
        except Exception as e:
            raise KRAErr(f"Failed to calculate_total_activities_weighted_scores_per_appraisal_kra with error: {e}")

        try:
            total_weight = Decimal(0)

            for performance_dimension_obj in performance_dimension_qr:
                weighted_score = target_score_service_object.calculate_performance_dimension_weighted_score(performance_dimension_id=performance_dimension_obj.id)
                total_weight += weighted_score

            return total_weight
        except Exception as e:
            raise KRAErr(f"Failed to calculate kra weighted score with error: {e}")
        
    def get_activities_kra_weight_progress(self, appraisal_kra_object: AppraisalKra)->WeightProgressType:
        try:
            activities_qr = self.activity_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_object.id)
            if activities_qr.exists():
                appraisal_kra_weight = appraisal_kra_object.get_weight
                covered_appraisal_kra_weight = activities_qr.aggregate(Sum("weight"))["weight__sum"]
                if appraisal_kra_weight < covered_appraisal_kra_weight:
                    raise Exception(f"Appraisal Kra pk[{appraisal_kra_object.id}]: Total Activities weight cannot be greater than Appraisal Kra weight")
                
                remain_appraisal_kra_weight = appraisal_kra_weight - covered_appraisal_kra_weight
                return WeightProgressType(covered_weight=covered_appraisal_kra_weight, remaining_weight=remain_appraisal_kra_weight)
            
            return WeightProgressType(covered_weight=0, remaining_weight=appraisal_kra_object.get_weight)
        except Exception as e:
            raise KRAErr(f"Failed to get kra activities weight progress with error: {e}")

    def get_activities_related_data_by_appraisal_kra_id(self, appraisal_kra_id: int, performance_dimension_repo: PerformanceDimensionRepository)->List[Dict[str, Annotated[str, int, QuerySet[PerformanceDimension]]]]:
        try:
            result = []
            activity_qr = self.activity_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
            
            for activity_obj in activity_qr:
                performance_dimension_qr = performance_dimension_repo.fetch_by_activity_id(activity_id=activity_obj.id)
                data = {
                    "activity_id": activity_obj.id,
                    "activity_name": activity_obj.name,
                    "activity_weight": activity_obj.weight,
                    "activity_performance_dimension_qr": performance_dimension_qr,
                    "performance_dimension_length": len(performance_dimension_qr)+1
                }
                result.append(data)
            
            return result
        except Exception as e:
            raise KRAErr(f"[ActivityService] Failed get_activities_related_data_by_appraisal_kra_id with error: {e}")
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

@dataclass
class PerformanceDimensionService:
    repo: PerformanceDimensionRepository
    
    def create_use_case(self, activity_obj: Activity, data: PerformanceDimensionType):
        return self.repo.create(activity_obj=activity_obj, data=data)
    
    def fetch_all_by_activity_id(self, activity_id):
        return self.repo.fetch_by_activity_id(activity_id=activity_id)
    
    def get_activities_performance_dimension_weight_progress(self, activity_object: Activity)->WeightProgressType:
        try:
            perf_dimension_qr = self.fetch_all_by_activity_id(activity_id=activity_object.id)
            activity_weight = activity_object.weight
            
            if perf_dimension_qr.exists():
                covered_activity_weight = perf_dimension_qr.aggregate(Sum("weight"))["weight__sum"]
                if activity_weight < covered_activity_weight:
                    raise Exception(f"Activity pk[{activity_object.id}]: Total Performance Dimensions weight cannot be greater than Activity weight")
                
                remain_activity_weight = activity_weight - covered_activity_weight
                return WeightProgressType(covered_weight=covered_activity_weight, remaining_weight=remain_activity_weight)
            
            return WeightProgressType(covered_weight=0, remaining_weight=activity_weight)
        except Exception as e:
            raise KRAErr(f"[PerformanceDimensionService] get_activities_performance_dimension_weight_progress with activity pk {activity_weight.id}, failed with error {e}")

    def calculate_total_performance_dimensions_weighted_score_per_activity(self, activity_id, target_score_object: TargetScoreService)->float:
        try:
            performance_dimension_qr = self.repo.fetch_by_activity_id(activity_id=activity_id)
        except Exception as e:
            raise KRAErr(f"Failed to fetch performance dimension by activity pk with error: {e}")

        try:
            total_weight = Decimal(0)

            for performance_dimension_obj in performance_dimension_qr:
                weighted_score = target_score_object.calculate_performance_dimension_weighted_score(performance_dimension_id=performance_dimension_obj.id)
                total_weight += weighted_score

            return total_weight
        except Exception as e:
            raise KRAErr(f"Failed calculate_total_performance_dimensions_weighted_score_per_activity() with error: {e}")
        
    
    def performance_indicator_exists(self, activity_id, performance_indicator: str)->bool:
        qr = self.repo.fetch_by_activity_id_performance_indicator(activity_id=activity_id, performance_indicator=performance_indicator)
        
        if qr.exists():
            return True
        return False
        
        
    def get_by_pk_use_case(self, performance_dimension_id: int)->PerformanceDimension:
        return self.repo.get_by_pk(performance_dimension_id=performance_dimension_id)
    
    def update_use_case(self, performance_dimension_object: PerformanceDimension, data: PerformanceDimensionType, is_applicable: bool)->PerformanceDimension:
        return self.repo.update(performance_dimension_obj=performance_dimension_object, data=data, is_applicable=is_applicable)