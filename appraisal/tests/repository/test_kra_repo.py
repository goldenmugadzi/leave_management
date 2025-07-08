from unittest import TestCase
from unittest.mock import Mock, patch
from ...models.kra import KeyResultArea
from it.users.models import UserProfile
from ...repository.kra import KRARepository
from ...helpers.types.kra import KRAType

class TestKRARepositoryCreateRepo(TestCase):
    def setUp(self):
        self.kra_repo = KRARepository()
        self.create_data = KRAType(
            key_result_area_description="Cooperate governance",
            goal_description="Increase employeement"
        )
        
    def mock_user(self):
        mock = Mock(spec=UserProfile)
        return mock
    
    def mock_kra_instance(self):
        mock = Mock(spec=KeyResultArea)
        return mock
        
    @patch('appraisal.repository.kra.KeyResultArea.objects.create')
    def test_create_kra_called_once(self, patch_kra_create_orm):
        mock_user_object = self.mock_user()
        
        self.kra_repo.create(creator=mock_user_object, data=self.create_data)
        patch_kra_create_orm.assert_called_once_with(
            key_result_area_description=self.create_data.key_result_area_description, 
            goal_description=self.create_data.goal_description, 
            created_by=mock_user_object
        )
        
    @patch('appraisal.repository.kra.KeyResultArea.objects.create')
    def test_create_kra_success(self, patch_kra_create_orm):
        mock_user_object = self.mock_user()
        mock_kra_object = self.mock_kra_instance()
        
        # Mock the return value of django create orm
        patch_kra_create_orm.return_value = mock_kra_object
        
        got_instance = self.kra_repo.create(creator=mock_user_object, data=self.create_data)
        
        self.assertEqual(got_instance, mock_kra_object)
        
    @patch('appraisal.repository.kra.KeyResultArea.objects.create')
    def test_create_kra_raises_exception(self, patch_kra_create_orm):
        mock_user_object = self.mock_user()
        exception_desc = "Database error"
        # simulate the orm exception
        patch_kra_create_orm.side_effect = Exception(exception_desc)
        
        with self.assertRaises(Exception) as context:
            self.kra_repo.create(creator=mock_user_object, data=self.create_data)
        
        self.assertIn(f"KRA Create Repo failed with error: {exception_desc}", str(context.exception))
        
        
    
        
class TestKRARepositoryUpdateRepo(TestCase):
    def setUp(self):
        self.kra_repo = KRARepository()
        self.update_data = KRAType(
            key_result_area_description="Cooperate governance",
            goal_description="Increase employeement"
        )
        
    def mock_user(self):
        mock = Mock(spec=UserProfile)
        return mock
    
    def mock_kra_instance(self):
        mock = Mock(spec=KeyResultArea)
        mock.key_result_area_description = "Corporate governance"
        mock.goal_description = "Increase efficiency"
        mock.updated_by = None
        return mock
        
        
    def test_update_kra_called_once(self):
        mock_user_object = self.mock_user()
        mock_kra_object = self.mock_kra_instance()
        
        # mock django save() explicitly
        mock_kra_object.save = Mock()

        self.kra_repo.update(kra_object=mock_kra_object, updated_by=mock_user_object, data=self.update_data)
        mock_kra_object.save.assert_called_once()
        
    def test_update_kra_success(self):
        mock_user_object = self.mock_user()
        mock_kra_object = self.mock_kra_instance()
        
        # mock django save() explicitly
        mock_kra_object.save = Mock()
        
        # Mock the return value of django save orm
        mock_kra_object.return_value = mock_kra_object
        
        got_instance = self.kra_repo.update(kra_object=mock_kra_object, updated_by=mock_user_object, data=self.update_data)
        self.assertEqual(got_instance, mock_kra_object)
        
    def test_update_kra_raises_exception(self):
        mock_user_object = self.mock_user()
        mock_kra_object = self.mock_kra_instance()
        exception_desc = "Database error"
        
        # simulate the orm exception
        mock_kra_object.save.side_effect = Exception(exception_desc)
        
        with self.assertRaises(Exception) as context:
            self.kra_repo.update(kra_object=mock_kra_object, updated_by=mock_user_object, data=self.update_data)
        
        self.assertIn(f"KRA update Repo failed with error: {exception_desc}", str(context.exception))
        
        
    
        