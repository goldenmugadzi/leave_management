from typing import List
from dataclasses import dataclass
from django.db import transaction
from django.db.models.query import QuerySet

from ..repository.kra import KRARepository, AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository, YearQuarterRepository
from ..repository.departmental_workplan import OutPutPerformanceDimensionRepository, DepartmentalOutRepository
from ..repository.appraisal import AppraisalRepository
from it.users.models import Designations
from ..models import KeyResultArea, AppraisalOutPutPerformanceDimensionScore, AppraisalDepartmentOutput
from ..helpers.types.kra import KRAType
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
                    year_quarter_objects = year_quarter_qr.count()
                    if year_quarter_objects != 4:
                        logger.warning(f"[AppraisalDependanciesInitialisationService] create_all_dependencies, with pk: {appraisal_id}, has {year_quarter_objects} - not 4 required.")
                        return False
                    
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
                else:
                    logger.warning(f"[AppraisalDependanciesInitialisationService] create_all_dependencies, with pk: {appraisal_id}, has no designation")
            return True
        except Exception as e:
            raise KRAErr(f"[AppraisalDependanciesInitialisationService] create service, failed with error: {e}")

@dataclass
class AppraisalDepartmentOutputService:
    appraisal_department_output_repo: AppraisalDepartmentOutputRepository
        
    def get_quarter_data(self, queryset: QuerySet[AppraisalDepartmentOutput]):
        department_objectives_qr = []
        
        # Get queryset with only department objectives
        for obj in queryset:
            department_objective_obj = obj.department_output.department_objective
            if not department_objective_obj in department_objectives_qr:
                department_objectives_qr.append(department_objective_obj)

        quarter_data = []
        department_outputs_total_field_count = 2
        
        # Construct dict with department objectives with their related department outputs
        for department_objectives_obj in department_objectives_qr:
            appraisal_dept_output_filter_by_department_objectives_id = queryset.filter(department_output__department_objective__id=department_objectives_obj.id)
            data = {
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
        