from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from ..repository import (
    UserQualificationRepository,
    AppraisalExperienceRepository,
    ExperienceRepository,
    AppraisalRepository,
)
from ..services import AppraisalService
from ..helpers.types import AppraisalPayloadType
from approve.models import Process
from ..models import Appraisal, Experience
from it.users.models import UserProfile

class TestAppraisalService(TestCase):
    
    def setUp(self) -> None:
        # Mock repositories
        self.qualification_repository_mock = Mock(spec=UserQualificationRepository)
        self.appraisal_experience_repository_mock = Mock(spec=AppraisalExperienceRepository)
        self.experience_repository_mock = Mock(spec=ExperienceRepository)
        self.appraisal_repository_mock = Mock(spec=AppraisalRepository)
        
        # Mock UserProfile
        self.mock_user_object = Mock(spec=UserProfile)
        
        # AppraisalService init
        self.appraisal_service = AppraisalService(
            appraisal_experience_repository=self.appraisal_experience_repository_mock,
            experience_repository=self.experience_repository_mock,
            qualification_repository=self.qualification_repository_mock,
            appraisal_repository=self.appraisal_repository_mock
        )
        
    def mock_process(self):
        mock_process = Mock(spec=Process)
        mock_process.id = 1
        return mock_process
    
    def mock_intiate(self, user_object, process_type):
        return self.mock_process()
        
        
    @patch("appraisal.services.appraisal.intiate")  
    def test_process_object_initialized(self, mock_intiate):
        
        # =========================== ARRANGE ========================
        
        # Mock intiate to use the mock_process function
        mock_intiate.side_effect = self.mock_intiate
        
        # Mock AppraisalPayloadType input
        mock_data = Mock(spec=AppraisalPayloadType)
        mock_data.experiences = []
        mock_data.qualifications = []

        # ========================== ACT =================================
        
        # Call the service's create_use_case method
        result = self.appraisal_service.create_use_case(self.mock_user_object, mock_data)

        # ============================ ASSERT ==============================
        
        # Assert intiate was called correctly
        mock_intiate.assert_called_once_with(self.mock_user_object, "Appraisal")
        