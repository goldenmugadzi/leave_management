from django.db import models
from helpers.models.timestamp import TimeStamp
from it.users.models import CostCenter
from .kra import KeyResultArea

class DepartmentObjective(TimeStamp):
    key_result_area = models.ForeignKey(KeyResultArea, on_delete=models.RESTRICT, related_name="dept_key_result_area", null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.RESTRICT, related_name="cost_center_ref", null=True, blank=True)
    objective_description = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.objective_description}"

class DepartmentOutput(TimeStamp):
    department_objective = models.ForeignKey(DepartmentObjective, on_delete=models.RESTRICT, related_name="dept_objective", null=True, blank=True)
    outcome_description = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.department_objective}"

