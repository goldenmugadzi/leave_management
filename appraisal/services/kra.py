from typing import List
from dataclasses import dataclass
from django.db import transaction
from django.db.models.query import QuerySet
from decimal import Decimal

from ..repository.kra import KRARepository, AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository, YearQuarterRepository, ApprasialKraReviewerStatusRepository, AppraisalConfirmationStatusRepository
from ..repository.departmental_workplan import OutPutPerformanceDimensionRepository, DepartmentalOutRepository
from ..repository.appraisal import AppraisalRepository, PersonalAttributeRepository, AppraiseePersonalAttributeRepository, AppraisalOverallCommentsRepository
from it.users.models import Designations
from ..models import KeyResultArea, AppraisalOutPutPerformanceDimensionScore, AppraisalDepartmentOutput, AppraiseePersonalAttribute, AppraisalOverallComments, AppraisalConfirmationStatus
from ..models.kra import REVIEWERS_CONFIRMATION_STATUS
from ..helpers.types.kra import KRAType
from ..helpers.getters import RatingCalculation

from loguru import logger

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
class AppraisalDependanciesInitialisationService:
    appraisal_department_output_repo: AppraisalDepartmentOutputRepository
    appraisal_output_perf_dimension_repo: AppraisalOutPutPerformanceDimensionScoreRepository
    appraisal_repo: AppraisalRepository
    year_quarter_repo: YearQuarterRepository
    performance_dimension_repo: OutPutPerformanceDimensionRepository
    department_output_repo: DepartmentalOutRepository
    
    def create_appraisal_department_output(self, appraisal_object, department_output_obj, year_quarter):
        if department_output_obj is None or appraisal_object is None or year_quarter is None:
            return None
        
        return self.appraisal_department_output_repo.create(appraisal_object, department_output_obj=department_output_obj, year_quarter_obj=year_quarter)

    def create_output_perf_dimension(self, appraisal_department_output_obj: AppraisalOutPutPerformanceDimensionScore, department_output_id: int):
        output_perf_dimension_qr = self.performance_dimension_repo.fetch_by_department_output_id(department_output_id=department_output_id)
        appraisal_output_perf_dimension_objs_list = []
        
        for output_perf_dimension_obj in output_perf_dimension_qr:
            is_scored = False
            if output_perf_dimension_obj.weight == 0:
                is_scored = True
            
            appraisal_output_perf_dimension_obj = AppraisalOutPutPerformanceDimensionScore(
                appraisal_department_output=appraisal_department_output_obj,
                performance_dimension=output_perf_dimension_obj,
                is_scored=is_scored
            )
            appraisal_output_perf_dimension_objs_list.append(appraisal_output_perf_dimension_obj)
            
        return self.appraisal_output_perf_dimension_repo.bulk_create(appraisal_output_perf_dimension_objs_list=appraisal_output_perf_dimension_objs_list)
    
    def create_appraisee_personal_attr(self, appraisal_object, year_quarter_qr):
        appraisee_personal_attr_objs_list = []
        personal_attr_repo = PersonalAttributeRepository()
        personal_attr_qr = personal_attr_repo.fetch_all()
        
        for year_quarter_obj in year_quarter_qr:
            for personal_attr_obj in personal_attr_qr:
                appraisee_personal_attr_obj = AppraiseePersonalAttribute(
                    appraisal=appraisal_object,
                    personal_attribute=personal_attr_obj,
                    quarter=year_quarter_obj
                )
                appraisee_personal_attr_objs_list.append(appraisee_personal_attr_obj)
        apprasee_personal_attr_repo = AppraiseePersonalAttributeRepository()
        return apprasee_personal_attr_repo.bulk_create(appraisee_personal_attr_list=appraisee_personal_attr_objs_list)
    
    
    def create_appraisal_confirmation_status(self, appraisal_object, year_quarter_qr):
        appraisal_confirmation_list = []
        appraisal_confirmation_status_repo = AppraisalConfirmationStatusRepository()
        
        for year_quarter_obj in year_quarter_qr:
            hr_obj = AppraisalConfirmationStatus(
                appraisal=appraisal_object,
                year_quarter=year_quarter_obj,
                confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]
            )
            reviewer_obj = AppraisalConfirmationStatus(
                appraisal=appraisal_object,
                year_quarter=year_quarter_obj,
                confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]
            )
            appraisal_confirmation_list.append(hr_obj)
            appraisal_confirmation_list.append(reviewer_obj)
        return appraisal_confirmation_status_repo.bulk_create(appraisal_confirmation_status_list=appraisal_confirmation_list)
    
    def create_overall_comments(self, appraisal_obj, year_quarter_qr):
        comments_list = []
        
        for year_quarter_obj in year_quarter_qr:
            overall_comment_obj = AppraisalOverallComments(
                appraisal=appraisal_obj,
                quarter=year_quarter_obj
            )
            comments_list.append(overall_comment_obj)
        repo = AppraisalOverallCommentsRepository()
        return repo.bulk_create(appraisal_overall_comm_list=comments_list)
        
    
    def create_all_dependencies(self, appraisal_id: int, year: int)->bool|None:
        try:
            with transaction.atomic():
                logger.info(f"[AppraisalDependanciesInitialisationService] with with appraisal pk: {appraisal_id}, year: {year}, process started ...")
                
                appraisal_obj = self.appraisal_repo.get_appraisal_by_pk(appraisal_id=appraisal_id)
                designation_obj = appraisal_obj.user.designation
                
                if designation_obj:
                    year_quarter_qr = self.year_quarter_repo.fetch_by_year(year=year)
                    year_quarter_objects = year_quarter_qr.count()
                    if year_quarter_objects != 4:
                        raise Exception(f"create_all_dependencies, with pk: {appraisal_id}, has {year_quarter_objects} - 4 instances required.")
                                       
                    department_output_qr = self.department_output_repo.fetch_by_designation_id(designation_id=designation_obj.id)
                    
                    for department_output_obj in department_output_qr:
                        
                        for year_quarter_obj in year_quarter_qr:
                            
                            # ============= create AppraisalDepartmentOutput object
                            appraisal_department_output_obj = self.create_appraisal_department_output(appraisal_object=appraisal_obj, department_output_obj=department_output_obj, year_quarter=year_quarter_obj)
                            
                            if appraisal_department_output_obj is not None:
                                logger.success(f"AppraisalDepartmentOutput object created successfully")
                                
                                # ========== create AppraisalOutPutPerformanceDimensionScore objects ==========
                                self.create_output_perf_dimension(
                                    appraisal_department_output_obj=appraisal_department_output_obj,
                                    department_output_id=department_output_obj.id
                                )
                                logger.success(f"AppraisalOutPutPerformanceDimensionScore objects created successfully")

                                
                                # =============== AppraisalDepartmentOutputReviewerStatus ===================
                                try:
                                    repo = ApprasialKraReviewerStatusRepository()
                                    repo.create(appraisal_department_output_obj=appraisal_department_output_obj)
                                    logger.success(f"AppraisalDepartmentOutputReviewerStatus objects created successfully")

                                except Exception as e:
                                    raise Exception(f"reviewers status creation failed with error: {e}")
                    
                    # ======================== create appraisee personal attributes ====================>>
                    self.create_appraisee_personal_attr(appraisal_object=appraisal_obj, year_quarter_qr=year_quarter_qr)
                    logger.success(f"appraisee personal attributes created successfully")

                    # ====================== create appraisal overall comments ======================
                    self.create_overall_comments(appraisal_obj=appraisal_obj, year_quarter_qr=year_quarter_qr)
                    logger.success(f"appraisal overall comments created successfully")
                    
                    # ====================== create appraisal confirmation status ======================
                    self.create_appraisal_confirmation_status(appraisal_object=appraisal_obj, year_quarter_qr=year_quarter_qr)
                    logger.success(f"appraisal confirmation status created successfully")
                else:
                    raise Exception(f"appraisee with appraisal id: {appraisal_id}. has no designation")
            
            return True
        except Exception as e:
            raise KRAErr(f"[AppraisalDependanciesInitialisationService] create service, failed with error: {e}")


@dataclass
class AppraisalScoreDimensionService:
    score_object: AppraisalOutPutPerformanceDimensionScore 
    
    def calculate_actual_variance_use_case(self)->float:
        """Calculate the actual variance between the actual score and the target score."""
        try:
            actual_score = self.score_object.score
            target_score = self.score_object.performance_dimension.agreed_target
            rating_calc_handler = RatingCalculation()
            
            actual_variance = rating_calc_handler.get_actual_variance(actual_score=actual_score, target_score=target_score)
            return actual_variance
        except Exception as e:
            raise Exception(f"[AppraisalScoreDimensionService] calculate_actual_variance_use_case() for performance dimension pk: {self.score_object.id} with error: {e}")
        
    def calculate_performance_dimension_rating_score_use_case(self)->float:
        """Calculate the rating score for an performance dimension based on actual variance and allowable variance."""
        try:
            performance_dimension_obj = self.score_object.performance_dimension
            rating_calc_handler = RatingCalculation()
            
            is_target_met = rating_calc_handler.is_target_met(agreed_target=performance_dimension_obj.agreed_target, actual_target=self.score_object.score)
            variance_range_classifier = rating_calc_handler.classify_variance_range(agreed_target=performance_dimension_obj.agreed_target, allowable_variance=performance_dimension_obj.allowable_variance, actual_score=self.score_object.score)
            rating = rating_calc_handler.calculate_rating(is_target_met=is_target_met, variance_range_classify=variance_range_classifier)

            return rating
        except Exception as e:
            raise Exception(f"[AppraisalScoreDimensionService] calculate_performance_dimension_rating_score_use_case() for performance dimension pk: {self.score_object.id} with error: {e}")

    def calculate_performance_dimension_weighted_score(self)->float:
        """Calculate the weighted score for an performance dimension by multiplying the performance dimension score by its weight."""
        try:
            performance_dimension_rate = self.calculate_performance_dimension_rating_score_use_case()
            performance_dimension_weight = self.score_object.performance_dimension.weight/100
            weighted_score = performance_dimension_rate * performance_dimension_weight

            return weighted_score
        except Exception as e:
            raise Exception(f"[AppraisalScoreDimensionService] calculate_performance_dimension_weighted_score() for performance dimension pk: {self.score_object.id} with error: {e}")
    


class AppraisalDepartmentOutputService:
    
    def __init__(self, appraisal_department_output_repo: AppraisalDepartmentOutputRepository=None):
        self.appraisal_department_output_repo = appraisal_department_output_repo
    
    def get_quarter_data(self, queryset: QuerySet[AppraisalDepartmentOutput]):
        department_objectives_qr = []
        
        # Get queryset with only department objectives
        for obj in queryset:
            department_objective_obj = obj.department_output.department_objective
            if not department_objective_obj in department_objectives_qr:
                department_objectives_qr.append(department_objective_obj)

        quarter_data = []
        department_outputs_total_field_count = 1
        
        # Construct dict with department objectives with their related department outputs
        for department_objectives_obj in department_objectives_qr:
            appraisal_dept_output_filter_by_department_objectives_id = queryset.filter(department_output__department_objective__id=department_objectives_obj.id)
            quarter_object = appraisal_dept_output_filter_by_department_objectives_id.first().year_quarter
            data = {
                "quarter_object": quarter_object,
                "department_objective": department_objectives_obj,
                "department_outputs_qr": appraisal_dept_output_filter_by_department_objectives_id,
                "num_department_outputs": len(appraisal_dept_output_filter_by_department_objectives_id) + department_outputs_total_field_count
            }
            quarter_data.append(data)
            
        return quarter_data
    
    def first_quarter_data(self, appraisal_dept_output_qr: QuerySet[AppraisalDepartmentOutput]):
        qr = appraisal_dept_output_qr.filter(year_quarter__quarter=1)
        return self.get_quarter_data(queryset=qr)
        
    def second_quarter_data(self, appraisal_dept_output_qr: QuerySet[AppraisalDepartmentOutput]):
        qr = appraisal_dept_output_qr.filter(year_quarter__quarter=2)
        return self.get_quarter_data(queryset=qr)
        
    def third_quarter_data(self, appraisal_dept_output_qr: QuerySet[AppraisalDepartmentOutput]):
        qr = appraisal_dept_output_qr.filter(year_quarter__quarter=3)
        return self.get_quarter_data(queryset=qr)
        
    def fourth_quarter_data(self, appraisal_dept_output_qr: QuerySet[AppraisalDepartmentOutput]):
        qr = appraisal_dept_output_qr.filter(year_quarter__quarter=4)
        return self.get_quarter_data(queryset=qr)
        
    def fetch_quarterly(self, appraisal_id, year):
        appraisal_dept_output_qr = self.appraisal_department_output_repo.fetch_by_appraisal_id_and_year(appraisal_id=appraisal_id, year=year)
        data = {
            "first_quarter": self.first_quarter_data(appraisal_dept_output_qr=appraisal_dept_output_qr),
            "second_quarter": self.second_quarter_data(appraisal_dept_output_qr=appraisal_dept_output_qr),
            "third_quarter": self.third_quarter_data(appraisal_dept_output_qr=appraisal_dept_output_qr),
            "fourth_quarter": self.fourth_quarter_data(appraisal_dept_output_qr=appraisal_dept_output_qr)
        }
        
        return data
        
    def get_output_total_weighted_score(self, appraisal_dept_output_id: int, performance_dimension_repo: AppraisalOutPutPerformanceDimensionScoreRepository)->float:
        try:
            
            total_weight = Decimal(0)
            qr = performance_dimension_repo.fetch_by_department_output_id(appraisal_department_output_id=appraisal_dept_output_id)
            
            for perform_dimension_obj in qr:
                service_handler = AppraisalScoreDimensionService(score_object=perform_dimension_obj)
                score_weighted_score = service_handler.calculate_performance_dimension_weighted_score()
                total_weight += score_weighted_score
                
            return total_weight
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputService] get_total_weighted_score(), with appraisal_dept_output_id: {appraisal_dept_output_id}, failed with error: {e}")
        
    def get_department_objective_total_weighted_score(self, department_objective_id: int, performance_dimension_repo: AppraisalOutPutPerformanceDimensionScoreRepository)->float:
        try:
            total_weight = Decimal(0)
            qr = performance_dimension_repo.fetch_by_department_objective_id(department_objective_id=department_objective_id)
            
            for perform_dimension_obj in qr:
                service_handler = AppraisalScoreDimensionService(score_object=perform_dimension_obj)
                score_weighted_score = service_handler.calculate_performance_dimension_weighted_score()
                total_weight += score_weighted_score
                
            return total_weight
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputService] department_objective_id(), with department_objective_id: {department_objective_id}, failed with error: {e}")
     
    def get_department_objectives_total_year_quarter_weighted_score(self, year_quarter_id: int, appraisal_id: int, performance_dimension_repo: AppraisalOutPutPerformanceDimensionScoreRepository)->float:
        try:
            total_weight = Decimal(0)
            qr = performance_dimension_repo.fetch_by_appraisal_id_year_quarter_id(year_quarter_id=year_quarter_id, appraisal_id=appraisal_id)
            
            for perform_dimension_obj in qr:
                service_handler = AppraisalScoreDimensionService(score_object=perform_dimension_obj)
                score_weighted_score = service_handler.calculate_performance_dimension_weighted_score()
                total_weight += score_weighted_score
                
            return total_weight
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputService] get_department_objectives_total_year_quarter_weighted_score(), with year_quarter_id: {year_quarter_id}, failed with error: {e}")
     