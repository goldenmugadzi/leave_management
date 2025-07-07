from unittest import TestCase
from unittest.mock import Mock, patch
from ...models.kra import KeyResultArea
from it.users.models import UserProfile
from ...repository.kra import KRARepository
from ...helpers.types.kra import KRAType

class TestKRARepository(TestCase):
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
        
        
    
        