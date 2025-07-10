from it.users.models import UserProfile, CostCenter
from ..models import KeyResultArea, DepartmentObjective


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