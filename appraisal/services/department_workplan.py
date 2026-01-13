from typing import List, Dict, Annotated
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.db.models.query import QuerySet
from ..models import DepartmentOutput
from ..repository.departmental_workplan import DepartmentalOutRepository, OutPutPerformanceDimensionRepository
from ..helpers.types.kra import WeightProgressType


@dataclass
class DepartmentOutputService:
    repo: DepartmentalOutRepository
        
    def get_designation_weight_progress(self, dept_objective_id: int, designation_id: int)->WeightProgressType:
        try:
            total_weight = 100
            dept_output_qr = self.repo.fetch_by_department_objective_id(department_objective_id=dept_objective_id)
            dept_output_filter_designation = dept_output_qr.filter(designation__id=designation_id)
            
            if dept_output_filter_designation.exists():
                covered_weight = dept_output_filter_designation.aggregate(Sum("weight"))["weight__sum"]

                if total_weight < covered_weight:
                    raise ValueError("total weight covered cannot be greater than 100")
                
                remaining_weight = total_weight - covered_weight
                return WeightProgressType(covered_weight=covered_weight, remaining_weight=remaining_weight)
            
            return WeightProgressType(covered_weight=0, remaining_weight=total_weight)
        except Exception as e:
            raise Exception(f"[DepartmentOutputService] get_weight_progress with dept_objective_id pk: {dept_objective_id}, failed with error: {e}")
        
@dataclass
class OutPutPerformanceDimensionService:
    repo: OutPutPerformanceDimensionRepository
    
    def get_outputs_weight_progress(self, department_output_obj: DepartmentOutput):
        try:
            qr = self.repo.fetch_by_department_output_id(department_output_id=department_output_obj.id)
            
            if qr.exists():
                department_output_weight = qr.first().department_output.weight
                total_output_perf_dimensions_weight = qr.aggregate(Sum("weight"))["weight__sum"]
                remaining_weight = department_output_weight - total_output_perf_dimensions_weight
                
                if total_output_perf_dimensions_weight > department_output_weight:
                    raise ValueError("total output performance dimension weight covered cannot be greater than performance output weight")
                return WeightProgressType(covered_weight=total_output_perf_dimensions_weight, remaining_weight=remaining_weight)
            return WeightProgressType(covered_weight=0, remaining_weight=department_output_obj.weight)
        except Exception as e:
            raise Exception(f"[OutPutPerformanceDimensionService] get_outputs_weight_progress with department_output_id pk: {department_output_obj.id}, failed with error: {e}")
    