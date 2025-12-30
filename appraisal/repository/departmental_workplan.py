from typing import List
from django.db.models.query import QuerySet
from it.users.models import UserProfile, CostCenter, Designations
from ..models import KeyResultArea, DepartmentObjective, DepartmentOutput, OutPutPerformanceDimension, JobCompetency
from ..models.departmental_workplan import PERFORMANCE_INDICATOR, DepartmentOutputCompetency
from ..helpers.types.dept_workplan import DepartmentalOutTypes, OutputPerformanceDimensionType

class DepartmentalObjectiveRepository:
    def create(self, creator: UserProfile, key_result_area: KeyResultArea, cost_center: CostCenter, department_objective_desc: str)->DepartmentObjective:
        try:
            return DepartmentObjective.objects.create(
                created_by=creator,
                key_result_area=key_result_area,
                cost_center=cost_center,
                objective_description=department_objective_desc
            )
        except Exception as e:
            raise Exception(f"DepartmentalObjectiveRepository Create Repo failed with error: {e}")
        
    def update(self, dep_objective_instance: DepartmentObjective, update_user_obj: UserProfile, key_result_area_obj: KeyResultArea, department_objective_desc: str)->DepartmentObjective:
        try:
            is_changed = False
            
            if dep_objective_instance.updated_by != update_user_obj:
                dep_objective_instance.updated_by = update_user_obj
                is_changed = True
            
            if dep_objective_instance.key_result_area != key_result_area_obj:
                dep_objective_instance.key_result_area = key_result_area_obj
                is_changed = True
                
            if dep_objective_instance.objective_description != department_objective_desc:
                dep_objective_instance.objective_description = department_objective_desc
                is_changed = True
            
            if is_changed:
                dep_objective_instance.save()
            return dep_objective_instance
        except Exception as e:
            raise Exception(f"DepartmentalObjectiveRepository Update repo with pk: {dep_objective_instance.id}, failed with error: {e}")
        
    def fetch_by_cost_center_year(self, cost_center_id: int, year: int)->QuerySet[DepartmentObjective]:
        try:
            qr = DepartmentObjective.objects.filter(cost_center__id=cost_center_id, created_date__year=year)
            return qr
        except Exception as e:
            raise Exception(f"DepartmentalObjectiveRepository fetch_by_cost_center_year with cost_center pk: {cost_center_id}, failed with error: {e}")
    
        
    def fetch_by_cost_center_kra(self, cost_center_id: int, kra_id: int)->QuerySet[DepartmentObjective]:
        try:
            qr = DepartmentObjective.objects.filter(
                cost_center__id=cost_center_id,
                key_result_area__id=kra_id
                )
            return qr
        except Exception as e:
            raise Exception(f"DepartmentalObjectiveRepository fetch_by_cost_center_kra with cost_center pk: {cost_center_id} and kra pk: {kra_id}, failed with error: {e}")
    
        
    def fetch_by_designation_year(self, designation_id: int, year: int)->QuerySet[DepartmentObjective]:
        try:
            qr = DepartmentObjective.objects.filter(designation__id=designation_id, created_date__year=year)
            return qr
        except Exception as e:
            raise Exception(f"DepartmentalObjectiveRepository fetch_by_designation_year with designation pk: {designation_id}, failed with error: {e}")
    
    def get_by_id(self, dept_objective_id: int)->DepartmentObjective|None:
        try:
            qr = DepartmentObjective.objects.filter(id=dept_objective_id)
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"DepartmentalObjectiveRepository get_by_id with departmental objective pk: {dept_objective_id}, failed with error: {e}")

class DepartmentalOutRepository:
    
    def create(self, creator: UserProfile, designation_obj: Designations, departmental_objective_obj: DepartmentObjective, data: DepartmentalOutTypes)->DepartmentOutput:
        try:
            return DepartmentOutput.objects.create(
                created_by=creator,
                designation=designation_obj,
                department_objective=departmental_objective_obj,
                output_description=data.output_description,
                weight=data.weight
            )
        except Exception as e:
            raise Exception(f"DepartmentalOutRepository Create Repo failed with error: {e}")
        
    def update(self, updater: UserProfile, department_output_obj: DepartmentOutput, department_objective_obj: DepartmentObjective, data: DepartmentalOutTypes)->DepartmentOutput:
        
        is_updated = False
        
        try:
            
            if department_output_obj.updated_by != updater:
                department_output_obj.updated_by = updater
                is_updated = True
                
            if department_output_obj.department_objective != department_objective_obj:
                department_output_obj.department_objective = department_objective_obj
                is_updated = True
                
            if department_output_obj.output_description != data.output_description:
                department_output_obj.output_description = data.output_description
                is_updated = True
                
            if department_output_obj.weight != data.weight:
                department_output_obj.weight = data.weight
                is_updated = True
            
            if is_updated:
                department_output_obj.save()

            return department_output_obj
        except Exception as e:
            raise Exception(f"DepartmentalOutRepository Update Repo for department out obj pk: {department_output_obj.id}, failed with error: {e}")
 
    def fetch_by_department_objective_id(self, department_objective_id: int)->QuerySet[DepartmentOutput]:
        try:
            return DepartmentOutput.objects.filter(department_objective__id=department_objective_id).select_related("department_objective", "designation")

        except Exception as e:
            raise Exception(f"DepartmentalOutRepository fetch_by_department_objective_id with department objective pk: {department_objective_id}, failed with error: {e}")
    
    def fetch_by_department_objective_and_designation_id(self, department_objective_id: int, designation_id: int)->QuerySet[DepartmentOutput]:
        try:
            return DepartmentOutput.objects.filter(department_objective__id=department_objective_id, designation__id=designation_id).select_related("department_objective", "designation")

        except Exception as e:
            raise Exception(f"DepartmentalOutRepository fetch_by_department_objective_id with department objective pk: {department_objective_id}, failed with error: {e}")
    
    def fetch_by_designation_id(self, designation_id: int)->QuerySet[DepartmentOutput]:
        try:
            return DepartmentOutput.objects.filter(designation__id=designation_id).select_related("department_objective", "designation")

        except Exception as e:
            raise Exception(f"DepartmentalOutRepository fetch_by_fetch_by_designation_id with designation pk: {designation_id}, failed with error: {e}")
    
    def fetch_by_cost_center_id_designation_id(self, designation_id: int, cost_center_id: int)->QuerySet[DepartmentOutput]:
        try:
            return DepartmentOutput.objects.filter(designation__id=designation_id, department_objective__cost_center__id=cost_center_id).select_related("department_objective", "designation")

        except Exception as e:
            raise Exception(f"DepartmentalOutRepository fetch_by_cost_center_id_designation_id with designation pk: {designation_id} and cost_center pk: {cost_center_id}, failed with error: {e}")
    
    def fetch_by_cost_center_id_designation_id_year(self, designation_id: int, cost_center_id: int, year: int)->QuerySet[DepartmentOutput]:
        try:
            return DepartmentOutput.objects.filter(designation__id=designation_id, department_objective__cost_center__id=cost_center_id, created_date__year=year).select_related("department_objective", "designation")

        except Exception as e:
            raise Exception(f"DepartmentalOutRepository fetch_by_cost_center_id_designation_id_year with designation pk: {designation_id} and cost_center pk: {cost_center_id} year: {year}, failed with error: {e}")

    def get_by_id(self, dept_output_id: int)->DepartmentOutput|None:
        try:
            qr = DepartmentOutput.objects.filter(id=dept_output_id)
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"DepartmentalOutRepository get_by_id with department out pk: {dept_output_id}, failed with error: {e}")

class OutPutPerformanceDimensionRepository:
    def create_in_bulk(self, department_output_obj: DepartmentOutput)->bool:
        try:
            output_perf_dimension_instances = []
            
            for perf_dimension_type in PERFORMANCE_INDICATOR:
                perf_indicator = perf_dimension_type[1]
                agreed_target = 0.0
                
                # Quality has 100 % agreed target
                if perf_indicator == PERFORMANCE_INDICATOR[1][0]:
                    agreed_target = 100
                    
                perf_dimension_obj = OutPutPerformanceDimension(
                        created_by=department_output_obj.created_by,
                        department_output=department_output_obj,
                        description="",
                        performance_indicator=perf_indicator,
                        allowable_variance=0.0,
                        agreed_target=agreed_target,
                        weight=0.0
                    )
                output_perf_dimension_instances.append(perf_dimension_obj)
            OutPutPerformanceDimension.objects.bulk_create(output_perf_dimension_instances)
            
            return True
        except Exception as e:
            raise Exception(f"[OutPutPerformanceDimensionRepository] create_in_bulk, failed with error: {e}")
        
    def update(self, output_perf_dimension_obj: OutPutPerformanceDimension, data: OutputPerformanceDimensionType)->OutPutPerformanceDimension:
        try:
            is_changed = False
            
            if output_perf_dimension_obj.performance_indicator != data.performance_indicator:
                output_perf_dimension_obj.performance_indicator = data.performance_indicator
                is_changed = True
                
            if output_perf_dimension_obj.description != data.description:
                output_perf_dimension_obj.description = data.description
                is_changed = True
            
                
            if output_perf_dimension_obj.weight != data.weight:
                output_perf_dimension_obj.weight = data.weight
                is_changed = True
            
                
            if output_perf_dimension_obj.allowable_variance != data.allowable_variance:
                output_perf_dimension_obj.allowable_variance = data.allowable_variance
                is_changed = True
            
                
            if output_perf_dimension_obj.agreed_target != data.agreed_target:
                output_perf_dimension_obj.agreed_target = data.agreed_target
                is_changed = True
            
            if is_changed:
                output_perf_dimension_obj.save()
            
            return output_perf_dimension_obj
        except Exception as e:
            raise Exception(f"[OutPutPerformanceDimensionRepository] Update Repo for output perf_dimension obj pk: {output_perf_dimension_obj.id}, failed with error: {e}")
    
        
    def fetch_by_department_output_id(self, department_output_id: int)->QuerySet[OutPutPerformanceDimension]:
        try:
            return OutPutPerformanceDimension.objects.filter(department_output__id=department_output_id).select_related("department_output")
            
        except Exception as e:
            raise Exception(f"[OutPutPerformanceDimensionRepository] fetch_by_department_output with pk: {department_output_id}, failed with error: {e}")

    def get_by_id(self, output_perf_dimension_id: int)->OutPutPerformanceDimension|None:
        try:
            qr = OutPutPerformanceDimension.objects.filter(id=output_perf_dimension_id).select_related("department_output")
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"[OutPutPerformanceDimensionRepository] output_perf_dimension_id with pk: {output_perf_dimension_id}, failed with error: {e}")

class DepartmentOutputCompetencyRepository:
    def create_in_bulk(self, competency_objs: List[DepartmentOutputCompetency])->bool:
        try:
            DepartmentOutputCompetency.objects.bulk_create(competency_objs)
            return True
        except Exception as e:
            raise Exception(f"[DepartmentOutputCompetencyRepository] create_in_bulk, failed with error: {e}")
    
    def fetch_department_output_id(self, department_output_id: int)->QuerySet[DepartmentOutputCompetency]:
        try:
            return DepartmentOutputCompetency.objects.filter(department_output__id=department_output_id)
        except Exception as e:
            raise Exception(f"[DepartmentOutputCompetencyRepository] fetch_department_output_id with pk: {department_output_id}, failed with error: {e}")

class JobCompetencyRepository:
    def create_in_bulk(self, job_competency_objs: JobCompetency)->bool:
        try:
            JobCompetency.objects.bulk_create(job_competency_objs)
            return True
        except Exception as e:
            raise Exception(f"[JobCompetencyRepository] create_in_bulk, failed with error: {e}")
        
    def create(self, designation_obj: Designations, required_competency: str)->JobCompetency:
        try:
            return JobCompetency.objects.create(designation=designation_obj, required_competency=required_competency)

        except Exception as e:
            raise Exception(f"[JobCompetencyRepository] create with designation id: {designation_obj.id}, failed with error: {e}")
        
    def fetch_by_designation_id_year(self, designation_id: int, year: int)->QuerySet[JobCompetency]:
        try:
            return JobCompetency.objects.filter(designation__id=designation_id, created_date__year=year)
        except Exception as e:
            raise Exception(f"[JobCompetencyRepository] fetch_by_designation_id_year, designation_id: {designation_id}, year: {year}, failed with error: {e}")
        
    def get_by_id(self, pk: int)->JobCompetency:
        try:
            qr = JobCompetency.objects.filter(id=pk)
            return qr.first()
        except Exception as e:
            raise Exception(f"[JobCompetencyRepository] get_by_id with pk: {pk}, failed with error: {e}")
    
    def update(self, job_competency_obj: JobCompetency, required_competency)->JobCompetency:
        try:
            is_changed = False
            
            if required_competency != job_competency_obj.required_competency:
                job_competency_obj.required_competency = required_competency
                is_changed = True
                
            if is_changed:
                job_competency_obj.save()
            return job_competency_obj
        except Exception as e:
            raise Exception(f"[JobCompetencyRepository] update with job_competency pk: {job_competency_obj.id}, failed with error: {e}")

    def update_in_bulk(self, job_competency_objs: List[JobCompetency], fields: list[str])->bool:
        try:
            JobCompetency.objects.bulk_update(job_competency_objs, fields)
            return True
        except Exception as e:
            raise Exception(f"[JobCompetencyRepository] update_in_bulk, failed with error: {e}")

    