from typing import List, Dict, Annotated
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.db.models.query import QuerySet
from ..models import DepartmentOutput
from ..repository.departmental_workplan import DepartmentalOutRepository
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