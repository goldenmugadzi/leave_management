from unittest import TestCase
from unittest.mock import Mock, patch
from appraisal.repository import UserProfileRepository
from appraisal.services import UserProfileService
from it.users.models import UserProfile
    
USER_PROFILE_FAKER = UserProfile(
    id=1,
    first_name="John",
    last_name="Wick",
    username="ND22222",
    grade="A and B",
)

class TestUserProfileService(TestCase):
    def setUp(self) -> None:
        # Mock the repository to avoid db interactions
        self.user_profile_repository_mock = Mock(spec=UserProfileRepository)
        self.user_profile_service = UserProfileService(self.user_profile_repository_mock)
    
    @patch("django.forms.models.model_to_dict")
    def test_update_user_profile_success(self, mock_model_to_dict):
        # ========== Arrange =======================
        mock_model_to_dict.return_value = {
            "id": 1,
            "first_name": "John",
            "last_name": "Wick",
            "username": "ND22222",
            "grade": "A and B",
        }
        
        update_data = {"grade": "C and Above"}
        updated_user_data = USER_PROFILE_FAKER
        updated_user_data.grade = update_data
        
        # mock repository method
        self.user_profile_repository_mock.get_user_profile_by_id.return_value = USER_PROFILE_FAKER
        self.user_profile_repository_mock.update_user_profile.return_value = updated_user_data
        
        #  =========  Act ============
        updated_user_profile = self.user_profile_service.update_user(user_object=USER_PROFILE_FAKER, data=update_data)
        
        # ========== Assert ============
        self.user_profile_repository_mock.get_user_profile_by_id.assert_called_once_with(user_id=USER_PROFILE_FAKER.id)
        self.user_profile_repository_mock.update_user_profile.assert_called_once_with(user=USER_PROFILE_FAKER, data=update_data)
        self.assertEqual(updated_user_profile, USER_PROFILE_FAKER)
       
        
    def test_update_user_profile_not_found(self):
        # Arrange
        self.user_profile_repository_mock.get_user_profile_by_id.side_effect = ValueError("User not found")

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.user_profile_service.update_user(user_object=Mock(id=99), data={})
        
        self.assertEqual(str(context.exception), "User not found")
        self.user_profile_repository_mock.get_user_profile_by_id.assert_called_once_with(user_id=99)
