from unittest import TestCase
from unittest.mock import Mock, patch
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, AppraisalRepository
from ..services import AppraisalService
from .faker import USER_PROFILE_FAKER, APPRAISAL_PAYLOAD_FAKER, PROCESS_FAKER, APPRAISAL_FAKER, EXPERIENCE_FAKER
from approve.models import Process

class TestAppraisalService(TestCase):
    def setUp(self) -> None:
        # mock repositories
        self.qualification_repository_mock = Mock(spec=UserQualificationRepository)
        self.appraisal_experience_repository_mock = Mock(spec=AppraisalExperienceRepository)
        self.experience_repository_mock = Mock(spec=ExperienceRepository)
        self.appraisal_repository_mock = Mock(spec=AppraisalRepository)
        self.user_mock = USER_PROFILE_FAKER
    
        # appraisal service init
        self.appraisal_service = AppraisalService(
            appraisal_experience_repository=self.appraisal_experience_repository_mock,
            experience_repository=self.experience_repository_mock,
            appraisal_repository=self.appraisal_repository_mock,
            qualification_repository=self.qualification_repository_mock
        )
    
        # Mock Appraisal object and its experience relation
        self.appraisal_mock = Mock()
        self.appraisal_mock.experience.add = Mock()  # Mock the add() method
        self.appraisal_repository_mock.create.return_value = self.appraisal_mock

        
    @patch("approve.views.intiate")
    def test_appraisal_creation_success(self, mock_intiate):
        # ======================== Arrange =======================
        
        # mock process
        mock_process = PROCESS_FAKER
        mock_intiate.return_value = mock_process
        
        # mock appraisal and experience object
        self.experience_repository_mock.get_or_create.return_value = EXPERIENCE_FAKER
        
        # mock appraisal object
        payload = APPRAISAL_PAYLOAD_FAKER
        
        # ======================== Act =======================
        got = self.appraisal_service.create_use_case(user_object=USER_PROFILE_FAKER, data=payload)
        print("============>>>>> ", got)
        # ======================== Assert =======================
        self.appraisal_repository_mock.create.assert_called_once_with(
                    user_object=USER_PROFILE_FAKER, process_object=mock_process
                )
        self.experience_repository_mock.get_or_create.assert_any_call(name="Golang")
        self.experience_repository_mock.get_or_create.assert_any_call(name="Python")
        self.appraisal_mock.experience.add.assert_any_call(EXPERIENCE_FAKER)
        