from dataclasses import dataclass
from typing import Protocol, List
from django.db.models.query import QuerySet
from ...repository.approval import AppraisalWorkflowRepository, AppraisalKraReviewerStatusRepository
from ...repository.performance import PerformanceReviewRepository
from ...repository.training import TrainingAndDevelopmentRepository
from ...repository.kra import TargetScoreRepository, AppraisalKraRepository
from ...models.helpers import YearQuarter
from ...models.kra import TargetScore, APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from ..types.quarters import ApprovedQuartersType
from loguru import logger


@dataclass
class AppraisalKraAndYearQuarterHandler:
    
    def get_appraisal_kra_obj(self, appraisal_kra_id: int):
        appraisal_kra_repo = AppraisalKraRepository()
        return appraisal_kra_repo.retrieve_by_pk(pk=appraisal_kra_id)

    def get_year_quarter_queryset(self, year: int)->QuerySet[YearQuarter]:
        """Handler that returns queryset of YearQuarter for the given year

        Args:
            year_name (int): Year number

        Returns:
            QuerySet[YearQuarter]: queryset for the given year
        """
        return YearQuarter.objects.filter(year=year).order_by("quarter")

        
@dataclass
class ApprovalStagesHandler:
    appraisal_id: int
    
    def get_approval_queryset(self):
        """Retrieve all approval workflow stages for the given appraisal."""
        approval_workflow_repo = AppraisalWorkflowRepository()
        return approval_workflow_repo.retrieve_by_appraisal(appraisal_id=self.appraisal_id)

    def get_completed_approval_queryset(self):
        """Retrieve completed approval stages."""
        qr = self.get_approval_queryset()
        return qr.filter(is_completed=True) if qr else None
    
    def get_uncompleted_approval_queryset(self):
        """Retrieve uncompleted approval stages."""
        qr = self.get_approval_queryset()
        return qr.filter(is_completed=False) if qr else None
    
    def __get_next_stage_obj__(self, current_stage_num: int):
        """Retrieve the next approval stage based on the current stage number."""
        qr = self.get_approval_queryset()
        next_stage_qr = qr.filter(stage_num__gt=current_stage_num) if qr.exists() else None
        return next_stage_qr.first() if next_stage_qr and next_stage_qr.exists() else None
    
    def get_current_and_next_stage(self):
        """Determine the current and next approval stages."""
        completed_qr = self.get_completed_approval_queryset()
        uncompleted_qr = self.get_uncompleted_approval_queryset()

        data = {"current_stage": None, "next_stage": None}

        if completed_qr and completed_qr.exists():
            current_stage_obj = completed_qr.last()
            data["current_stage"] = current_stage_obj
            data["next_stage"] = self.__get_next_stage_obj__(current_stage_obj.stage_num)
            return data
        if uncompleted_qr and uncompleted_qr.exists():
            current_stage_obj = uncompleted_qr.first()
            data["current_stage"] = current_stage_obj
            data["next_stage"] = self.__get_next_stage_obj__(current_stage_obj.stage_num)
            return data
        
        return data

    
    def get_stages_info(self):
        """Retrieve all stages along with current and next stage information."""
        qr = self.get_approval_queryset()
        last_stage_number = qr.last().stage_num if qr and qr.exists() else None

        return {
            "stages": qr,
            "last_stage_number": last_stage_number,
            **self.get_current_and_next_stage()
        }


# Strategy Pattern use Protocol for composition rather inheritance
class ApprovalWorkflowQuarterStagesStrategyInterface(Protocol):
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        """handler that retrieve all quarters[1,2,3,4] approval status.

        Args:
            appraisal_kra_id (int): AppraisalKra pk

        Returns:
            ApprovedQuartersType: pydantic type for with all quarters[1,2,3,4]
        """
        pass
        
class ScoringStageStrategy:
    def __get_all_score_objects_by_appraisal_kra_id(self, appraisal_kra_id: int):
        repo = TargetScoreRepository()
        return repo.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
    
    def __get_unscored_per_quarter(self, target_score_objects: QuerySet[TargetScore], quarter_obj_id: int):
        return target_score_objects.filter(performance_dimension__activity__appraisal_kra__quarter__id=quarter_obj_id, is_scored=False)
    
    def __get_scored_per_quarter(self, target_score_objects: QuerySet[TargetScore], quarter_obj_id: int):
        return target_score_objects.filter(performance_dimension__activity__appraisal_kra__quarter__id=quarter_obj_id, is_scored=True)
    
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_kra_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_kra_obj = appraisal_kra_year_quarter_handler.get_appraisal_kra_obj(appraisal_kra_id=appraisal_kra_id)
        year_quarter_qr = appraisal_kra_year_quarter_handler.get_year_quarter_queryset(year=appraisal_kra_obj.quarter.year)
        target_score_objects = self.__get_all_score_objects_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
        result = []
        
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            unscored_qr  = self.__get_unscored_per_quarter(target_score_objects=target_score_objects, quarter_obj_id=year_quarter_obj.id)
            scored_qr = self.__get_scored_per_quarter(target_score_objects=target_score_objects, quarter_obj_id=year_quarter_obj.id)
            
            approved_quarter_type_obj = None
            if unscored_qr.exists() or not scored_qr.exists():
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=True)
            result.append(approved_quarter_type_obj)
        return result
    
class PerformanceReviewStageStrategy:
    
    def __is_incomplete_performance_review_exists(self, appraisal_id: int, quarter_obj_id: int)->bool:
        """Handler that query db by appraisal and quarter pk, to Performance review object is incomplete

        Args:
            appraisal_id (int): Appraisal primary key
            quarter_obj_id (int): Year Quarter pk 

        Returns:
            bool: 'true' if PerformanceProgressReview is incomplete else false
        """
        
        perf_reviewer_repo = PerformanceReviewRepository()
        perf_reviewer_qr = perf_reviewer_repo.get_performance_by_appraisal_id(appraisal_id=appraisal_id)

        incomplete_perf_review_qr = perf_reviewer_qr.filter(quarter__id=quarter_obj_id, is_completed=False)
        if incomplete_perf_review_qr.exists():
            return True
        return False
    
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_kra_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_kra_obj = appraisal_kra_year_quarter_handler.get_appraisal_kra_obj(appraisal_kra_id=appraisal_kra_id)
        year_quarter_qr = appraisal_kra_year_quarter_handler.get_year_quarter_queryset(year=appraisal_kra_obj.quarter.year)

        result = []
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            is_not_approved = self.__is_incomplete_performance_review_exists(appraisal_id=appraisal_kra_obj.appraisal.id, quarter_obj_id=year_quarter_obj.id)
            
            approved_quarter_type_obj = None
            if is_not_approved:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=True)
            result.append(approved_quarter_type_obj)
        return result
            
class TrainingAndDevelopmentStageStrategy:
    def __is_incomplete_training_dev_exists(self, appraisal_id: int, quarter_obj_id: int)->bool:
        """Handler that query db by appraisal and quarter pk, to TrainingAndDevelopment object is incomplete

        Args:
            appraisal_id (int): Appraisal primary key
            quarter_obj_id (int): Year Quarter pk 

        Returns:
            bool: 'true' if TrainingAndDevelopment is incomplete else false
        """
        
        training_dev_repo = TrainingAndDevelopmentRepository()
        training_dev_qr = training_dev_repo.get_by_appraisal_id(appraisal_id=appraisal_id)

        incomplete_training_dev_qr = training_dev_qr.filter(quarter__id=quarter_obj_id, is_completed=False)
        if incomplete_training_dev_qr.exists():
            return True
        return False
    
    
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_kra_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_kra_obj = appraisal_kra_year_quarter_handler.get_appraisal_kra_obj(appraisal_kra_id=appraisal_kra_id)
        year_quarter_qr = appraisal_kra_year_quarter_handler.get_year_quarter_queryset(year=appraisal_kra_obj.quarter.year)

        result = []
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            is_not_approved = self.__is_incomplete_training_dev_exists(appraisal_id=appraisal_kra_obj.appraisal.id, quarter_obj_id=year_quarter_obj.id)

            approved_quarter_type_obj = None
            if is_not_approved:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=True)
            result.append(approved_quarter_type_obj)
        return result

    
class ReviewStageStrategy:
    
    def __is_appraisal_kra_quarter_reviewed(self, year_quarter_id: int)->bool:
        repo = AppraisalKraReviewerStatusRepository()
        appraisal_kra_status_review_qr = repo.retrieve_by_appraisal_kra_year_quarter_id(year_quarter_obj_id=year_quarter_id)
        
        if not appraisal_kra_status_review_qr.exists():
            return False
        
        accepted_appraisal_kra_status_review_qr = appraisal_kra_status_review_qr.filter(status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0])
        if not accepted_appraisal_kra_status_review_qr.exists():
            return False
        
        return True
        
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_kra_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_kra_obj = appraisal_kra_year_quarter_handler.get_appraisal_kra_obj(appraisal_kra_id=appraisal_kra_id)
        year_quarter_qr = appraisal_kra_year_quarter_handler.get_year_quarter_queryset(year=appraisal_kra_obj.quarter.year)

        result = []
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            is_approved = self.__is_appraisal_kra_quarter_reviewed(year_quarter_id=year_quarter_obj.id)

            approved_quarter_type_obj = None
            if is_approved:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=True)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=False)
            result.append(approved_quarter_type_obj)
        return result

class ApprovalWorkflowQuarterStagesStrategyContext:
    def __init__(self, strategy: ApprovalWorkflowQuarterStagesStrategyInterface):
        self.strategy = strategy
        
    def get_stage_quarters_approval(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        try:
            return self.strategy.get_approved_quarters(appraisal_kra_id=appraisal_kra_id)
        except Exception as e:
            logger.error(f"[ApprovalWorkflowQuarterStagesStrategyInterface] for {self.strategy.__class__()}, failed with error: {e}")
            return None