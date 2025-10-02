from dataclasses import dataclass
from typing import Protocol, List
from ...models.appraisal import Appraisal
from ...repository.kra import YearQuarterRepository, AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository
from ...repository.departmental_workplan import DepartmentalObjectiveRepository
from ...repository.qualification_experience import UserQualificationRepository, UserExperienceRepository
from ...repository.training import TrainingAndDevelopmentRepository
from ...repository.performance import PerformanceReviewRepository
from ...repository.appraisal import AppraiseePersonalAttributeRepository
from .quarter import get_all_quarter_ratings_per_appraiser

from ...helpers.types.appraisal import AppraisalPersonalDetails, AppraisalOutputType, AppraisalPerformanceAssessmentType, TrainingAndDevType, PerformanceProgressReviewType, FinalPerformanceAssType


class AppraisalDependanciesStrategyInterface(Protocol):
    def dependance(self):
        pass

@dataclass
class AppraisalPersonalDetailsStrategy:
    appraisal_object: Appraisal
    def __get_appraisee_ec_no_name(self):
        appraisee_user_object = self.appraisal_object.user
        return appraisee_user_object.username, appraisee_user_object.get_full_name()
    
    def __get_appraisee_nation_id_position(self):
        appraisee_user_object = self.appraisal_object.user
        return appraisee_user_object.national_id, appraisee_user_object.designation
    
    def __get_appraisee_section_region(self):
        appraisee_user_object = self.appraisal_object.user
        return appraisee_user_object.section, appraisee_user_object.region
    
    def __get_appraisee_qualification_and_experiances(self):
        appraisee_user_object = self.appraisal_object.user
        qualification_repo = UserQualificationRepository()
        appraisee_qualification = []
        appraisee_qualification_qr = qualification_repo.fetch_by_user(user_id=appraisee_user_object.id)
        for appraisee_qualification_obj in appraisee_qualification_qr:
            appraisee_qualification_name = appraisee_qualification_obj.description
            appraisee_qualification.append(appraisee_qualification_name)
            
        
        experiences_repo = UserExperienceRepository()
        appraisee_experiences = []
        appraisee_experiences_qr = experiences_repo.fetch_by_user_id(user_id=appraisee_user_object.id)
        for appraisee_exp_obj in appraisee_experiences_qr:
            exp_name = f"{appraisee_exp_obj.name} ({appraisee_exp_obj.years_of_experience})"
            appraisee_experiences.append(exp_name)
        
        return appraisee_qualification, appraisee_experiences
    
    def __get_appraisee_appointment_date_and_position_appointment_date(self):
        return None, None
    
    def __get_appraiser_name_and_position(self):
        appraiser_user_obj = self.appraisal_object.appraiser
        return appraiser_user_obj.get_full_name(), appraiser_user_obj.designation
    
    def __get_reviewer_name_and_position(self):
        reviewer_user_obj = self.appraisal_object.reviewer
        return reviewer_user_obj.get_full_name(), reviewer_user_obj.designation
    
    def dependance(self):
        appraisee_ec_no, appraisee_name = self.__get_appraisee_ec_no_name()
        appraisee_national_id, appraisee_position = self.__get_appraisee_nation_id_position()
        appraisee_qualification, appraisee_exp = self.__get_appraisee_qualification_and_experiances()
        appointed_date, position_appointed_date = self.__get_appraisee_appointment_date_and_position_appointment_date()
        appraisee_section, appraisee_region = self.__get_appraisee_section_region()
        
        appraiser_name, appraiser_position = self.__get_appraiser_name_and_position()
        reviewer_name, reviewer_position = self.__get_reviewer_name_and_position()
        
        return AppraisalPersonalDetails(
            appraisee_name=appraisee_name,
            appraisee_position=appraisee_position,
            appraisee_qualifications=appraisee_qualification,
            appraisee_experiance=appraisee_exp,
            appraisee_national_id=appraisee_national_id,
            appraisee_ec_no=appraisee_ec_no,
            appraisee_date_of_appointment=appointed_date,
            appraisee_position_appointment_date=position_appointed_date,
            appraisee_department=appraisee_section,
            appraisee_station=appraisee_region,
            appraiser_name=appraiser_name,
            appraiser_position=appraiser_position,
            reviewer_name=reviewer_name,
            reviewer_position=reviewer_position
        )

@dataclass   
@dataclass
class PerformanceAssessmentStrategy:
    appraisal_object: Appraisal
    
    
    def __get_appraisal_outputs(self, quarter_id: int):
        
        repo = AppraisalDepartmentOutputRepository()
        return repo.fetch_by_appraisal_id_quarter(
            appraisal_id=self.appraisal_object.id,
            quarter_id=quarter_id
        )

    def __get_perf_dimension(self, output_id: int):
        """
        Fetch all performance dimension scores for a given appraisal department output.

        Args:
            output_id (int): The ID of the AppraisalDepartmentOutput.

        Returns:
            QuerySet[AppraisalOutPutPerformanceDimensionScore]: A queryset of 
            performance dimension scores linked to the output.
        """
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        return repo.fetch_by_department_output_id(
            appraisal_department_output_id=output_id
        )
    
    def __get_quarters(self):
        """
        Fetch all quarters for the appraisal year.

        Returns:
            QuerySet[YearQuarter]: A queryset of quarters associated 
            with the appraisal year.
        """
        repo = YearQuarterRepository()
        return repo.fetch_by_year(year=self.appraisal_object.created_date.year)
    
    def dependance(self) -> List[AppraisalPerformanceAssessmentType]:
        
        appraisal_assessments_list: List[AppraisalPerformanceAssessmentType] = []

        for quarter_obj in self.__get_quarters():
            appraisal_output_qr = self.__get_appraisal_outputs(quarter_id=quarter_obj.id)
            
            appraisal_output_types_list = []
            for output_obj in appraisal_output_qr:
                appraisal_output_type = AppraisalOutputType(
                    output_obj=output_obj,
                    performance_dimensions=self.__get_perf_dimension(output_id=output_obj.id)
                )
                appraisal_output_types_list.append(appraisal_output_type)
            
            appraisal_assessment = AppraisalPerformanceAssessmentType(
                quarter=quarter_obj.quarter,
                dept_outputs=appraisal_output_types_list
            )
            appraisal_assessments_list.append(appraisal_assessment)

        return appraisal_assessments_list


    
@dataclass
class TrainingAndDevStrategy:
    appraisal_object: Appraisal
    
    def dependance(self):
        appraisal_year = self.appraisal_object.created_date.year
        year_quarter_repo = YearQuarterRepository()
        appraisal_year_quarter_qr = year_quarter_repo.fetch_by_year(appraisal_year)

        quarters_training_dev = []
        for year_quarter_obj in appraisal_year_quarter_qr:
            training_dev_repo = TrainingAndDevelopmentRepository()
            training_dev_obj = training_dev_repo.get_by_appraisal_id_quarter(
                appraisal_id=self.appraisal_object.id,
                quarter_id=year_quarter_obj.id
            )
            
            training_dev_type = TrainingAndDevType(
                quarter=year_quarter_obj.quarter,
                quarter_training_dev=training_dev_obj,
                competency_gap=training_dev_repo.fetch_competency_gaps(training_dev_obj=training_dev_obj)
            )
            quarters_training_dev.append(training_dev_type)
            
        return quarters_training_dev
    

@dataclass
class PerformanceProgressReviewStrategy:
    appraisal_object: Appraisal
    
    def dependance(self):
        appraisal_year = self.appraisal_object.created_date.year
        year_quarter_repo = YearQuarterRepository()
        appraisal_year_quarter_qr = year_quarter_repo.fetch_by_year(appraisal_year)

        perf_progress_review = []
        for year_quarter_obj in appraisal_year_quarter_qr:
            perf_progress_review_repo = PerformanceReviewRepository()
            perf_progress_review_obj = perf_progress_review_repo.get_performance_by_appraisal_id_quarter(
                appraisal_id=self.appraisal_object.id,
                quarter_id=year_quarter_obj.id
            )
            
            perf_progress_type = PerformanceProgressReviewType(
                quarter=year_quarter_obj.quarter,
                perf_progress_review=perf_progress_review_obj
            )
            perf_progress_review.append(perf_progress_type)
            
        return perf_progress_review

@dataclass
class FinalPerformanceAssStrategy:
    appraisal_object: Appraisal
    
    def __get_personal_attr(self, appraisal_id: int):
        repo = AppraiseePersonalAttributeRepository()
        return repo.fetch_appraisal_id(appraisal_id=appraisal_id)
    
    def dependance(self):
        appraisal_object = self.appraisal_object
        appraisal_year = appraisal_object.created_date.year
        final_score_obj = get_all_quarter_ratings_per_appraiser(
            year=appraisal_year,
            appraisal_id=appraisal_object.id
        )
        
        return FinalPerformanceAssType(
            final_score=final_score_obj,
            personal_attributes=self.__get_personal_attr(appraisal_id=appraisal_object.id)
        )
        
class AppraisalDependanciesStrategyContext:
    def __init__(self, strategy: AppraisalDependanciesStrategyInterface):
        self.strategy = strategy
        
    def get_dependance(self):
        return self.strategy.dependance()
        