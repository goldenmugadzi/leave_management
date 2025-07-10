from unittest import TestCase
from unittest.mock import Mock, patch
from it.users.models import UserProfile, CostCenter
from ...models import KeyResultArea, DepartmentObjective
from ...repository.departmental_workplan import DepartmentalObjectiveRepository

class TestDepartmentalObjectiveCreateRepository(TestCase):
    def setUp(self):
        self.repo = DepartmentalObjectiveRepository()
        self.mock_creator_user = Mock(spec=UserProfile)
        self.mock_kra_obj = Mock(spec=KeyResultArea)
        self.mock_cost_center_obj = Mock(spec=CostCenter)
        self.mock_objective_desc = "Department Objective"
        
    def mock_department_objective_obj(self):
        mock = Mock(spec=DepartmentObjective)
        return mock
        
    def test_create_orm_called_once(self):
        
        with patch('appraisal.repository.departmental_workplan.DepartmentObjective.objects.create') as mock_create_orm:
            self.repo.create(
                creator=self.mock_creator_user,
                key_result_area=self.mock_kra_obj,
                cost_center=self.mock_cost_center_obj,
                department_objective_desc=self.mock_objective_desc
            )
        mock_create_orm.assert_called_once_with(
            created_by=self.mock_creator_user,
            key_result_area=self.mock_kra_obj,
            cost_center=self.mock_cost_center_obj,
            objective_description=self.mock_objective_desc
        )
        
    def test_create_successfully(self):
        mock_department_objective_obj = self.mock_department_objective_obj()
        
        with patch('appraisal.repository.departmental_workplan.DepartmentObjective.objects.create') as mock_create_orm:
            mock_create_orm.return_value = mock_department_objective_obj
            got = self.repo.create(
                creator=self.mock_creator_user,
                key_result_area=self.mock_kra_obj,
                cost_center=self.mock_cost_center_obj,
                department_objective_desc=self.mock_objective_desc
            )
            self.assertEqual(got, mock_department_objective_obj)
            
    def test_create_raises_exception(self):
        exception_desc = "Database error"
        
        with patch('appraisal.repository.departmental_workplan.DepartmentObjective.objects.create') as mock_create_orm:
            with self.assertRaises(Exception) as context:
                mock_create_orm.side_effect = Exception(exception_desc)
                self.repo.create(
                    creator=self.mock_creator_user,
                    key_result_area=self.mock_kra_obj,
                    cost_center=self.mock_cost_center_obj,
                    department_objective_desc=self.mock_objective_desc
                )
                
            self.assertIn(f"DepartmentalObjectiveRepository Create Repo failed with error: {exception_desc}", str(context.exception))