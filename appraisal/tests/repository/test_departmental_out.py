from unittest import TestCase
from unittest.mock import Mock, patch
from ...repository.departmental_workplan import DepartmentalOutRepository
from ...helpers.types.dept_workplan import DepartmentalOutTypes
from ...models.departmental_workplan import DepartmentObjective, DepartmentOutput
from it.users.models import UserProfile, Designations

class TestDepartmentalOutCreateRepository(TestCase):
    def setUp(self):
        self.repo = DepartmentalOutRepository()
        self.mock_dept_objective_obj = Mock(spec=DepartmentObjective)
        self.mock_creator_user = Mock(spec=UserProfile)
        self.mock_department_output = Mock(spec=DepartmentOutput)
        self.mock_designation = Mock(spec=Designations)
        
    def mock_dept_output_type(self):
        mock = Mock(spec=DepartmentalOutTypes)
        mock.output_description = "Output description"
        mock.weight = "Output weight"
        return mock
    
    def test_create_orm_called_once(self):
        mock_data = self.mock_dept_output_type()
        mock_creator_obj = self.mock_creator_user
        
        with patch('appraisal.repository.departmental_workplan.DepartmentOutput.objects.create') as mock_create_orm:
            self.repo.create(creator=mock_creator_obj, designation_obj=self.mock_designation, departmental_objective_obj=self.mock_dept_objective_obj, data=mock_data)
        
        mock_create_orm.assert_called_once_with(
            created_by=mock_creator_obj,
            designation=self.mock_designation,
            department_objective=self.mock_dept_objective_obj,
            output_description=mock_data.output_description,
            weight=mock_data.weight
        )
        
    def test_create_successful(self):
        mock_data = self.mock_dept_output_type()
        mock_creator_obj = self.mock_creator_user
        mock_dept_output = self.mock_department_output
        mock_dept_output.designation = self.mock_designation
        
        with patch('appraisal.repository.departmental_workplan.DepartmentOutput.objects.create') as mock_create_orm:
            mock_create_orm.return_value = mock_dept_output
            got = self.repo.create(creator=mock_creator_obj, designation_obj=self.mock_designation, departmental_objective_obj=self.mock_dept_objective_obj, data=mock_data)

            self.assertEqual(got, mock_dept_output)
            
    def test_create_orm_raise_error(self):
        mock_data = self.mock_dept_output_type()
        mock_creator_obj = self.mock_creator_user
        exception_description = "Database error"
        
        with patch('appraisal.repository.departmental_workplan.DepartmentOutput.objects.create') as mock_create_orm:
            with self.assertRaises(Exception) as context:
                mock_create_orm.side_effect = Exception(exception_description)
                self.repo.create(creator=mock_creator_obj, designation_obj=self.mock_designation, departmental_objective_obj=self.mock_dept_objective_obj, data=mock_data)
            self.assertIn(f"DepartmentalOutRepository Create Repo failed with error: {exception_description}", str(context.exception))

class TestDepartmentalOutUpdateRepository(TestCase):
    def setUp(self):
        self.repo = DepartmentalOutRepository()
        self.mock_dept_objective_obj = Mock(spec=DepartmentObjective)
        self.mock_updater_user = Mock(spec=UserProfile)
        self.mock_department_output = Mock(spec=DepartmentOutput)
        
    def mock_dept_output_type(self):
        mock = Mock(spec=DepartmentalOutTypes)
        mock.output_description = "Output description"
        mock.weight = 0.0
        return mock
    
    def test_update_save_orm_called_once_for_changes(self):
        mock_save_orm = Mock()
        mock_department_output = self.mock_department_output
        mock_department_output.weight = 20
        mock_data = self.mock_dept_output_type()
        
        mock_department_output.save = mock_save_orm
        
        self.repo.update(updater=self.mock_updater_user,
                            department_output_obj=mock_department_output,
                            department_objective_obj=self.mock_dept_objective_obj, 
                            data=mock_data)
        
        mock_department_output.save.called_once()
        
    def test_update_save_orm_success(self):
        mock_save_orm = Mock()
        mock_department_output = self.mock_department_output
        mock_department_output.weight = 20
        mock_data = self.mock_dept_output_type()
        
        mock_department_output.save = mock_save_orm
        
        got = self.repo.update(updater=self.mock_updater_user,
                            department_output_obj=mock_department_output,
                            department_objective_obj=self.mock_dept_objective_obj, 
                            data=mock_data)
        self.assertEqual(got, mock_department_output)
        
    def test_update_save_orm_raises_error(self):
        mock_save_orm = Mock()
        mock_department_output = self.mock_department_output
        mock_department_output.weight = 20
        mock_department_output.id = 1
        mock_data = self.mock_dept_output_type()
        exception_description = "Database error"
        
        mock_department_output.save = mock_save_orm
        mock_department_output.save.side_effect = Exception(exception_description)
        
        with self.assertRaises(Exception) as context:
            self.repo.update(
                                updater=self.mock_updater_user, 
                                department_output_obj=mock_department_output,
                                department_objective_obj=self.mock_dept_objective_obj, 
                                data=mock_data
                            )
        self.assertIn(f"DepartmentalOutRepository Update Repo for department out obj pk: 1, failed with error: {exception_description}", str(context.exception))