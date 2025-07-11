from django.db.models.query import QuerySet
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
