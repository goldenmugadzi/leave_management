from dataclasses import dataclass
from typing import Protocol, List
from django.db.models.query import QuerySet
from django.db.models import Q
from ...repository.approval import AppraisalWorkflowRepository
from ...repository.performance import PerformanceReviewRepository
from ...repository.training import TrainingAndDevelopmentRepository
from ...repository.kra import AppraisalOutPutPerformanceDimensionScoreRepository, AppraisalDepartmentOutputRepository, ApprasialKraReviewerStatusRepository, AppraisalConfirmationStatusRepository
from ...repository.appraisal import AppraiseePersonalAttributeRepository, AppraisalOverallCommentsRepository, AppraisalRepository
from ...models.helpers import YearQuarter
from ...models.kra import AppraisalOutPutPerformanceDimensionScore, APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, AppraisalDepartmentOutput, REVIEWERS_CONFIRMATION_STATUS
from ..types.quarters import ApprovedQuartersType
from ..data.approval_stage import ApprovalStageData, APPRAISEE, APPRAISER, REVIEWER, HR
from loguru import logger


@dataclass
class AppraisalKraAndYearQuarterHandler:
    
    def get_appraisal_kra_obj(self, appraisal_id: int)->List[AppraisalDepartmentOutput]:
        appraisal_kra_repo = AppraisalDepartmentOutputRepository()
        return appraisal_kra_repo.fetch_by_appraisal_id(appraisal_id=appraisal_id)

    def get_year_quarter_queryset(self, year: int)->QuerySet[YearQuarter]:
        """Handler that returns queryset of YearQuarter for the given year

        Args:
            year_name (int): Year number

        Returns:
            QuerySet[YearQuarter]: queryset for the given year
        """
        return YearQuarter.objects.filter(year=year).order_by("quarter")


class ReviewersStatusHandler:
    
    def __get_unaccepted_status_qr(self, appraisal_id: int, year_quarter_id: int):
        repo = ApprasialKraReviewerStatusRepository()
        qr = repo.fetch_by_appraisal_id_quarter_year(
            year_q_id=year_quarter_id,
            appraisal_id=appraisal_id
        ).filter(
            (Q(confirmation_status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0])|Q(confirmation_status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[2][0]))
        )
        return qr
    
    def __get_confirmation_qr(self, appraisal_id: int, year_quarter_id: int):
        repo = AppraisalConfirmationStatusRepository()
        return repo.fetch_by_appraisal_id_quarter_id(
            appraisal_id=appraisal_id,
            quarter_id=year_quarter_id
        ).filter(
            (Q(confirmation_status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0])|Q(confirmation_status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[2][0]))
        )
    
    def __get_for_appraiser(self, appraisal_id: int, year_quarter_id: int):
        unaccepted_qr = self.__get_unaccepted_status_qr(
            appraisal_id=appraisal_id,
            year_quarter_id=year_quarter_id
        )
        return unaccepted_qr.filter(
            reviewer=REVIEWERS_CONFIRMATION_STATUS[0][0]
        )
    
    def __get_for_reviewer(self, appraisal_id: int, year_quarter_id: int):
        unaccepted_qr = self.__get_confirmation_qr(
            appraisal_id=appraisal_id,
            year_quarter_id=year_quarter_id
        )
        return unaccepted_qr.filter(
            confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]
        )
        
    def __get_for_hr(self, appraisal_id: int, year_quarter_id: int):
        unaccepted_qr = self.__get_confirmation_qr(
            appraisal_id=appraisal_id,
            year_quarter_id=year_quarter_id
        )
        return unaccepted_qr.filter(
            confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]
        )
        
    
    def get_quarters_approval(self, appraisal_kra_id: int, for_appraiser: bool, for_reviewer: bool, for_hr: bool)->List[ApprovedQuartersType]:
        appraisal_handler = AppraisalRepository()
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_obj = appraisal_handler.get_appraisal_by_pk(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_obj.created_date.year)
        result = []
        
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            if for_appraiser:
                not_accepted_review_status_qr = self.__get_for_appraiser(
                    appraisal_id=appraisal_obj.id,
                    year_quarter_id=year_quarter_obj.id
                )
            elif for_reviewer:
                not_accepted_review_status_qr = self.__get_for_reviewer(
                    appraisal_id=appraisal_obj.id,
                    year_quarter_id=year_quarter_obj.id
                )
            elif for_hr:
                not_accepted_review_status_qr = self.__get_for_hr(
                    appraisal_id=appraisal_obj.id,
                    year_quarter_id=year_quarter_obj.id
                )
            else:
                logger.error(f"[ReviewersStatusHandler] get_quarters_approval has no reviewer specified")
                return result
            
            approved_quarter_type_obj = None
            if not_accepted_review_status_qr.exists():
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=True)
            result.append(approved_quarter_type_obj)
        return result

@dataclass
class ApprovalStagesHandler:
    appraisal_id: int
    year_quarter_id: int
    
    def get_approval_queryset(self):
        """Retrieve all approval workflow stages for the given appraisal."""
        approval_workflow_repo = AppraisalWorkflowRepository()
        return approval_workflow_repo.fetch_by_appraisal_id_quarter_id(appraisal_id=self.appraisal_id, year_quarter_id=self.year_quarter_id)

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
        if uncompleted_qr.exists():
            current_stage_obj = uncompleted_qr.first()
            data["current_stage"] = current_stage_obj
            data["next_stage"] = self.__get_next_stage_obj__(current_stage_obj.stage_num)
        else:
            current_stage_obj = completed_qr.last()
            data["current_stage"] = current_stage_obj
            data["next_stage"] = self.__get_next_stage_obj__(current_stage_obj.stage_num)

        return data
    
    def is_current_stage(self, stage_id: int)->bool:
        current_stage_nxt_handler = self.get_current_and_next_stage()
        current_stage_obj = current_stage_nxt_handler["current_stage"]
        return stage_id == current_stage_obj.id
    
    def get_stages_info(self):
        """Retrieve all stages along with current and next stage information."""
        qr = self.get_approval_queryset()
        last_stage_number = qr.last().stage_num if qr and qr.exists() else None
        current_nxt_stage_data = self.get_current_and_next_stage()
        completed_stages_qr = self.get_completed_approval_queryset()
        completed_stages_count = 0
        if completed_stages_qr is not None:
            completed_stages_count = completed_stages_qr.count()
        return {
            "stages": qr,
            "last_stage_number": last_stage_number,
            "completed_stages_count": completed_stages_count,
            **current_nxt_stage_data
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
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        return repo.fetch_by_appraisal_id(appraisal_id=appraisal_kra_id)
    
    def __get_unscored_per_quarter(self, target_score_objects: QuerySet[AppraisalOutPutPerformanceDimensionScore], quarter_obj_id: int):
        return target_score_objects.filter(appraisal_department_output__year_quarter__id=quarter_obj_id, is_scored=False)
    
    def __get_scored_per_quarter(self, target_score_objects: QuerySet[AppraisalOutPutPerformanceDimensionScore], quarter_obj_id: int):
        return target_score_objects.filter(appraisal_department_output__year_quarter__id=quarter_obj_id, is_scored=True)
    
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_handler = AppraisalRepository()
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_obj = appraisal_handler.get_appraisal_by_pk(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_obj.created_date.year)
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
    
class AppraiserReviewStageStrategy:
        
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        reviewers_status_handler = ReviewersStatusHandler()
        return reviewers_status_handler.get_quarters_approval(
            appraisal_kra_id=appraisal_kra_id,
            for_appraiser=True,
            for_reviewer=False,
            for_hr=False
        )
        
class ReviewerReviewStageStrategy:
        
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        reviewers_status_handler = ReviewersStatusHandler()
        return reviewers_status_handler.get_quarters_approval(
            appraisal_kra_id=appraisal_kra_id,
            for_appraiser=False,
            for_reviewer=True,
            for_hr=False
        )
        
class HrReviewStageStrategy:
        
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        reviewers_status_handler = ReviewersStatusHandler()
        return reviewers_status_handler.get_quarters_approval(
            appraisal_kra_id=appraisal_kra_id,
            for_appraiser=False,
            for_reviewer=False,
            for_hr=True
        )

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
        appraisal_handler = AppraisalRepository()
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_obj = appraisal_handler.get_appraisal_by_pk(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_obj.created_date.year)

        result = []
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            is_not_approved = self.__is_incomplete_performance_review_exists(appraisal_id=appraisal_kra_id, quarter_obj_id=year_quarter_obj.id)
            
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
        training_dev_qr = training_dev_repo.fetch_by_appraisal_id(appraisal_id=appraisal_id)

        incomplete_training_dev_qr = training_dev_qr.filter(quarter__id=quarter_obj_id, is_completed=False)
        if incomplete_training_dev_qr.exists():
            return True
        return False
    
    
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_handler = AppraisalRepository()
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_obj = appraisal_handler.get_appraisal_by_pk(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_obj.created_date.year)

        result = []
        for year_quarter_obj in year_quarter_qr:
            year_quarter_name = year_quarter_obj.__str__()
            is_not_approved = self.__is_incomplete_training_dev_exists(appraisal_id=appraisal_kra_id, quarter_obj_id=year_quarter_obj.id)

            approved_quarter_type_obj = None
            if is_not_approved:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_name, is_approved=True)
            result.append(approved_quarter_type_obj)
        return result
    
class AppraisalPersonalAttributesStrategy:
    def __get_qr(self, appraisal_id: int):
        repo = AppraiseePersonalAttributeRepository()
        return repo.fetch_appraisal_id(appraisal_id=appraisal_id)
    
    def __get_updated_qr(self, year_quarter_id: int, appraisee_personal_attr_qr):
        qr = appraisee_personal_attr_qr.filter(quarter__id=year_quarter_id)
        return qr.filter(
            Q(excellent=True) |
            Q(very_good=True) |
            Q(satisfactory=True) |
            Q(requires_improvement=True) |
            Q(unsatisfactory=True)
        )
        
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_handler = AppraisalRepository()
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_obj = appraisal_handler.get_appraisal_by_pk(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_obj.created_date.year)
        result = []
        
        apprasee_personal_attr_qr = self.__get_qr(appraisal_id=appraisal_kra_id)
        for year_quarter_obj in year_quarter_qr:
            updated_qr = self.__get_updated_qr(year_quarter_id=year_quarter_obj.id, appraisee_personal_attr_qr=apprasee_personal_attr_qr)
            
            approved_quarter_type_obj = None
            if not updated_qr.exists():
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_obj.__str__(), is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_obj.__str__(), is_approved=True)
            result.append(approved_quarter_type_obj)
        return result
    
    
class AppraisalOverallCommentStrategy:
    
    def __get_qr(self, appraisal_id: int):
        repo = AppraisalOverallCommentsRepository()
        return repo.fetch_by_appraisal_id(appraisal_id=appraisal_id)
    
    def __get_completed_qr(self, qr, quarter_id):
        return qr.filter(
            Q(quarter__id=quarter_id) &
            (Q(appraiser_comment__isnull=False) | Q(appraiser_comment=''))
        )
    
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_handler = AppraisalRepository()
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_obj = appraisal_handler.get_appraisal_by_pk(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_obj.created_date.year)
        
        result = []
        overall_comm_qr = self.__get_qr(appraisal_id=appraisal_kra_id)
        for year_quarter_obj in year_quarter_qr:
            completed_qr = self.__get_completed_qr(qr=overall_comm_qr, quarter_id=year_quarter_obj.id)
            approved_quarter_type_obj = None
            if not completed_qr.exists():
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_obj.__str__(), is_approved=False)
            else:
                approved_quarter_type_obj = ApprovedQuartersType(appraisal_kra_id=appraisal_kra_id, quarter_name=year_quarter_obj.__str__(), is_approved=True)
            result.append(approved_quarter_type_obj)
        return result
    
class ReviewStageStrategy:
    
    def __is_appraisal_kra_quarter_reviewed(self, year_quarter_id: int)->bool:
        repo = ApprasialKraReviewerStatusRepository()
        appraisal_kra_status_review_qr = repo.fetch_by_quarter_year(year_quarter_obj_id=year_quarter_id)
        
        if not appraisal_kra_status_review_qr.exists():
            return False
        
        accepted_appraisal_kra_status_review_qr = appraisal_kra_status_review_qr.filter(status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0])
        if not accepted_appraisal_kra_status_review_qr.exists():
            return False
        
        return True
        
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        appraisal_year_quarter_handler = AppraisalKraAndYearQuarterHandler()
        appraisal_kra_obj = appraisal_year_quarter_handler.get_appraisal_kra_obj(appraisal_id=appraisal_kra_id)
        year_quarter_qr = appraisal_year_quarter_handler.get_year_quarter_queryset(year=appraisal_kra_obj.year_quarter.year)

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
            logger.warning(f"[ApprovalWorkflowQuarterStagesStrategyInterface] for {self.strategy.__class__()}, failed with error: {e}")
            return None
        

class ApprovalStageGetterHandler:
    def get_stage_num_by_name(self, stage_name: str):
        stage_num = 0
        for index, stage in enumerate(ApprovalStageData):
            if stage.value["stage_name"].lower() == stage_name.lower():
                stage_num = index + 1
        return stage_num
    
    def get_user_responsible(self, approval_stage_id: int):
        try:
            approval_stage_repo = AppraisalWorkflowRepository()
            obj = approval_stage_repo.get_by_id(appraisal_workflow_id=approval_stage_id)
            
            if obj is None:
                raise Exception(f"AppraisalWorkflow not found")
            
            appraisal_object = obj.appraisal
            user_responsible = None
            
            for _, stage in enumerate(ApprovalStageData):
                if stage.value["stage_name"].lower() == obj.stage_name.lower():
                    role = stage.value["set_by"].lower()
                    
                    if role == APPRAISEE.lower():
                        user_responsible = appraisal_object.user
                    elif role == APPRAISER.lower():
                        user_responsible = appraisal_object.appraiser
                    elif role == REVIEWER.lower():
                        user_responsible = appraisal_object.reviewer
                    elif role == HR.lower():
                        user_responsible = appraisal_object.hr
                        
            if user_responsible is None:
                raise Exception("user responsible not found")
            return user_responsible
        except Exception as e:
            raise Exception(f"[ApprovalStageGetterHandler] get_user_responsible with approval_stage_id: {approval_stage_id}, failed with error: {e}")