from django.db import models
from helpers.models.timestamp import TimeStamp
from django.contrib.auth import get_user_model
from it.users.models import CostCenter, Designations
from .kra import KeyResultArea

User = get_user_model()

class DepartmentObjective(TimeStamp):
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="dept_objectives_creator", null=True)
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="dept_objectives_updater", null=True)
    key_result_area = models.ForeignKey(KeyResultArea, on_delete=models.RESTRICT, related_name="dept_key_result_area", null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.RESTRICT, related_name="cost_center_ref", null=True, blank=True)
    objective_description = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.objective_description}"

class DepartmentOutput(TimeStamp):
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="dept_output_creator", null=True)
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="dept_output_updater", null=True)
    department_objective = models.ForeignKey(DepartmentObjective, on_delete=models.RESTRICT, related_name="dept_objective", null=True, blank=True)
    designation = models.ForeignKey(Designations, on_delete=models.RESTRICT, related_name="user_designation", null=True, blank=True)
    output_description = models.CharField(max_length=500)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.output_description}"
    
PERFORMANCE_INDICATOR = [
        ('Quantity', 'Quantity'),
        ('Quality', 'Quality'),
        ('Timeliness', 'Timeliness'),
        ('Cost', 'Cost'),
    ]


class OutPutPerformanceDimension(TimeStamp):
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="dept_perf_dimension_creator", null=True)
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="dept_perf_dimension_updater", null=True, blank=True)
    department_output = models.ForeignKey(DepartmentOutput, on_delete=models.RESTRICT, related_name="dept_output", null=True)
    performance_indicator = models.CharField(max_length=30, choices=PERFORMANCE_INDICATOR, null=True, blank=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    allowable_variance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    agreed_target = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.department_output} - {self.performance_indicator}"