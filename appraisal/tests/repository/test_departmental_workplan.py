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
            
class TestDepartmentalObjectiveUpdateRepository(TestCase):
    def setUp(self):
        self.repo = DepartmentalObjectiveRepository()
        self.mock_updater_user = Mock(spec=UserProfile)
        self.mock_kra_obj = Mock(spec=KeyResultArea)
        self.mock_objective_desc = "Department Objective"
        
    def mock_department_objective_instance(self):
        mock = Mock(spec=DepartmentObjective)
        mock.updated_by = self.mock_updater_user
        mock.key_result_area = self.mock_kra_obj
        mock.objective_description = self.mock_objective_desc
        return mock
        
    def test_update_orm_called_once_for_changes(self):
        mock_save_orm = Mock()
        mock_department_objective_instance = self.mock_department_objective_instance()
        changed_objective_description = "Changed Description"
        mock_department_objective_instance.save = mock_save_orm
        
        self.repo.update(
            dep_objective_instance=mock_department_objective_instance,
            update_user_obj=self.mock_updater_user,
            key_result_area_obj=self.mock_kra_obj,
            department_objective_desc=changed_objective_description
        )
        
        mock_department_objective_instance.save.assert_called_once()
    
    def test_update_orm_not_called_no_changes(self):
        mock_save_orm = Mock()
        mock_department_objective_instance = self.mock_department_objective_instance()
        mock_department_objective_instance.save = mock_save_orm
        
        self.repo.update(
            dep_objective_instance=mock_department_objective_instance,
            update_user_obj=self.mock_updater_user,
            key_result_area_obj=self.mock_kra_obj,
            department_objective_desc=self.mock_objective_desc
        )
        
        mock_department_objective_instance.save.assert_not_called()
        
    def test_update_successfully(self):
        mock_save_orm = Mock()
        mock_department_objective_instance = self.mock_department_objective_instance()
        changed_objective_description = "Changed Description"
        mock_department_objective_instance.save = mock_save_orm
        
        got = self.repo.update(
            dep_objective_instance=mock_department_objective_instance,
            update_user_obj=self.mock_updater_user,
            key_result_area_obj=self.mock_kra_obj,
            department_objective_desc=changed_objective_description
        )
        
        mock_department_objective_instance.objective_description = changed_objective_description
        self.assertEqual(got, mock_department_objective_instance)
        
    def test_update_error(self):
        mock_save_orm = Mock()
        mock_department_objective_instance = self.mock_department_objective_instance()
        mock_department_objective_instance.id = 1
        exception_desc = "Database error"
        changed_objective_description = "Changed Description"

        mock_department_objective_instance.save= mock_save_orm
        mock_department_objective_instance.save.side_effect = Exception(exception_desc)
        
        with self.assertRaises(Exception) as context:
            
            self.repo.update(
                dep_objective_instance=mock_department_objective_instance,
                update_user_obj=self.mock_updater_user,
                key_result_area_obj=self.mock_kra_obj,
                department_objective_desc=changed_objective_description
            )
            
        self.assertIn(f"DepartmentalObjectiveRepository Update repo with pk: 1, failed with error: {exception_desc}", str(context.exception))


