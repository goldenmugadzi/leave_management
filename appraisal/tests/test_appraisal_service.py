from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from ..repository import (
    UserQualificationRepository,
    AppraisalExperienceRepository,
    ExperienceRepository,
    AppraisalRepository,
)
from ..services import AppraisalService
from ..services.appraisal import AppraisalCreationError
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
    
    def mock_appraisal_payload_input(self):
        mock_data = Mock(spec=AppraisalPayloadType)
        mock_data.experiences = []
        mock_data.qualifications = []
        return mock_data
        
        
    @patch("appraisal.services.appraisal.intiate")  
    def test_process_object_initialized(self, mock_intiate):
        
        # =========================== ARRANGE ========================
        
        # Mock intiate to use the mock_process function
        mock_intiate.side_effect = self.mock_intiate
        
        # Mock AppraisalPayloadType input
        mock_data = self.mock_appraisal_payload_input()

        # ========================== ACT =================================
        
        # Call the service's create_use_case method
        self.appraisal_service.create_use_case(self.mock_user_object, mock_data)

        # ============================ ASSERT ==============================
        
        # Assert intiate was called correctly
        mock_intiate.assert_called_once_with(self.mock_user_object, "Appraisal")
        
    
    @patch("appraisal.services.appraisal.intiate")    
    def test_appraisal_object_creation_success(self, mock_intiate):
        
        # =========================== ARRANGE ========================
        
        # Create a single mock process object to be used consistently
        mock_process_object = self.mock_process()
    
        # Mock intiate to always return the same mock_process_object
        mock_intiate.side_effect = lambda user_object, process_type: mock_process_object

        # Mock AppraisalPayloadType input
        mock_data = self.mock_appraisal_payload_input()
        
        # mock Appraisal object
        mock_appraisal_object = Mock(spec=Appraisal)
        mock_appraisal_object.process = mock_process_object
        self.appraisal_repository_mock.create.return_value = mock_appraisal_object
        
        # ========================= ACT ================================
        result = self.appraisal_service.create_use_case(self.mock_user_object, mock_data)
        
        # ======================= ASSERT ================================
        self.appraisal_repository_mock.create.assert_called_once_with(user_object=self.mock_user_object, process_object=mock_process_object)
        self.assertEqual(result, mock_appraisal_object)
        
        
    def test_appraisal_object_creation_failure(self):
        
        # =========================== ARRANGE ========================
        # Mock AppraisalPayloadType input
        mock_data = self.mock_appraisal_payload_input()  
        db_err_str = "Database error"
        
        with patch.object(self.appraisal_repository_mock, 'create', side_effect=Exception(db_err_str)):
            
            # ========================= ACT ============================
            try:
                self.appraisal_service.create_use_case(self.mock_user_object, mock_data)
                self.fail("Expected AppraisalCreationError not raised")
            except AppraisalCreationError as e:
                # ===================== ASSERT ============================

                self.assertEqual(str(e), f"Failed to create appraisal with error: {db_err_str}")
