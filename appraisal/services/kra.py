from typing import List, Dict, Annotated
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.db.models.query import QuerySet
from django.db import transaction


from ..repository.kra import KRARepository, AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository, YearQuarterRepository
from ..repository.departmental_workplan import OutPutPerformanceDimensionRepository, DepartmentalOutRepository
from ..repository.appraisal import AppraisalRepository
from it.users.models import Designations
from ..models import KeyResultArea, Appraisal, AppraisalDepartmentOutput, AppraisalOutPutPerformanceDimensionScore, OutPutPerformanceDimension
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
            appraisal_output_perf_dimension_obj = AppraisalOutPutPerformanceDimensionScore(
                appraisal_department_output=appraisal_department_output_obj,
                performance_dimension=output_perf_dimension_obj
            )
            appraisal_output_perf_dimension_objs_list.append(appraisal_output_perf_dimension_obj)
            
        return self.appraisal_output_perf_dimension_repo.bulk_create(appraisal_output_perf_dimension_objs_list=appraisal_output_perf_dimension_objs_list)
    
    def create_all_dependencies(self, appraisal_id: int, year: int)->bool|None:
        try:
            with transaction.atomic():
                appraisal_obj = self.appraisal_repo.get_appraisal_by_pk(appraisal_id=appraisal_id)
                designation_obj = appraisal_obj.user.designation
                
                if designation_obj:
                    year_quarter_qr = self.year_quarter_repo.fetch_by_year(year=year)
                    department_output_qr = self.department_output_repo.fetch_by_designation_id(designation_id=designation_obj.id)
                    
                    for department_output_obj in department_output_qr:
                        for year_quarter_obj in year_quarter_qr:
                            
                            # ============= create AppraisalDepartmentOutput object
                            appraisal_department_output_obj = self.create_appraisal_department_output(appraisal_object=appraisal_obj, department_output_obj=department_output_obj, year_quarter=year_quarter_obj)
                            
                            if appraisal_department_output_obj is not None:
                                
                                # ========== create AppraisalOutPutPerformanceDimensionScore objects ==========
                                self.create_output_perf_dimension(
                                    appraisal_department_output_obj=appraisal_department_output_obj,
                                    department_output_id=department_output_obj.id
                                    )
            return True

        except Exception as e:
            raise KRAErr(f"[AppraisalDependanciesInitialisationService] create service, failed with error: {e}")
