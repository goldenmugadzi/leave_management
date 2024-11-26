from unittest import TestCase
from unittest.mock import Mock, call, patch
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
from ..helpers.types import ExperienceType, QualificationsType


class TestAppraisalServiceCreateUseCase(TestCase):
    
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
    
    def mock_appraisal_payload_input(self, experiences=[], qualifications=[]):
        mock_data = Mock(spec=AppraisalPayloadType)
        mock_data.experiences = experiences
        mock_data.qualifications = qualifications
        return mock_data
    
    def mock_appraisal_object(self, process_object):
        appraisal_object = Mock(spec=Appraisal)
        appraisal_object.process = process_object
        return appraisal_object
    
    def mock_experience_object(self, name):
        mock = Mock(spec=Experience)
        mock.name = name
        return mock
        
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
        mock_appraisal_object = self.mock_appraisal_object(process_object=mock_process_object)
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

    
    def test_experience_object_creation_success(self):
        # =================== ARRANGE =====================
        experience_type = ExperienceType(name="Python", years_of_experience=1, months_of_experience=1)
        experiences = [experience_type]
        
        mock_approval_payload = self.mock_appraisal_payload_input(experiences=experiences)
        
        mock_experience_object = self.mock_experience_object(name=experience_type.name)
        self.experience_repository_mock.get_or_create.return_value = mock_experience_object
        
        # ==================== ACT =====================
        result = self.appraisal_service.create_use_case(self.mock_user_object, mock_approval_payload)

        # ==================== ASSERT ===================
        self.experience_repository_mock.get_or_create.assert_called_once_with(name=experience_type.name)
        
    def test_multiple_experience_object_creation_success(self):
        
        # =================== ARRANGE =====================
        experience_type_1 = ExperienceType(name="Golang", years_of_experience=1, months_of_experience=1)
        experience_type_2 = ExperienceType(name="Python", years_of_experience=1, months_of_experience=1)
        experiences = [experience_type_1, experience_type_2]
        
        mock_approval_payload = self.mock_appraisal_payload_input(experiences=experiences)

        for experience in experiences:
            mock_experience_object = self.mock_experience_object(name=experience.name)
            self.experience_repository_mock.get_or_create.return_value = mock_experience_object
        
        # ==================== ACT =====================
        self.appraisal_service.create_use_case(self.mock_user_object, mock_approval_payload)

        # ==================== ASSERT ===================
        self.assertEqual(self.experience_repository_mock.get_or_create.call_count, 2)
        
        expected_calls = [
            call(name=experience_type_1.name),
            call(name=experience_type_2.name)
        ]
        self.experience_repository_mock.get_or_create.assert_has_calls(expected_calls, any_order=False)

    @patch("appraisal.services.appraisal.intiate")   
    def test_adding_experience_appraisal(self, mock_intiate):
        # =============================== ARRANGE =====================
        
        # Create a single mock process object to be used consistently
        mock_process_object = self.mock_process()
    
        # Mock intiate to always return the same mock_process_object
        mock_intiate.side_effect = lambda user_object, process_type: mock_process_object

        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object(process_object=mock_process_object)
        self.appraisal_repository_mock.create.return_value = mock_appraisal_object
        
        # mock payload data
        experience_type_1 = ExperienceType(name="Golang", years_of_experience=1, months_of_experience=1)
        experience_type_2 = ExperienceType(name="Python", years_of_experience=1, months_of_experience=1)
        experiences = [experience_type_1, experience_type_2]
        
        mock_approval_payload = self.mock_appraisal_payload_input(experiences=experiences)
        
        # mock experience object
        for experience in experiences:
            mock_experience_object = self.mock_experience_object(name=experience.name)
            self.experience_repository_mock.get_or_create.return_value = mock_experience_object
       
            # mock add_experiences
            self.appraisal_repository_mock.add_experience.return_value = None
        
        # ========================== ACT =========================
        self.appraisal_service.create_use_case(user_object=self.mock_user_object, data=mock_approval_payload)
        
        # ========================== ASSERT ======================
        expected_calls = [
            call(appraisal_object=mock_appraisal_object, experience_object=mock_experience_object, data=experience_type_1),
            call(appraisal_object=mock_appraisal_object, experience_object=mock_experience_object, data=experience_type_2),
        ]
        self.appraisal_repository_mock.add_experience.assert_has_calls(expected_calls, any_order=False)
        
        self.assertEqual(self.appraisal_repository_mock.add_experience.call_count, 2)
        
    
    @patch("appraisal.services.appraisal.intiate")   
    def test_user_qualification_create(self, mock_intiate):
        # ========================= ARRANGE ========================
        
        # mock process object
        mock_process_object = self.mock_process()
        mock_intiate.side_effect = lambda user_object, process_type: mock_process_object

        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object(process_object=mock_process_object)
        self.appraisal_repository_mock.create.return_value = mock_appraisal_object
       
        # mock qualifications payload
        qualification_1 = QualificationsType(name="AWS")
        qualification_2 = QualificationsType(name="AWS")
        
        qualifications = [qualification_1, qualification_2]
        mock_payload = self.mock_appraisal_payload_input(qualifications=qualifications)
        
        # mock qualification create repo
        for _ in qualifications:
            self.qualification_repository_mock.create.return_value = None
            
        # ========================= ACT ============================
        self.appraisal_service.create_use_case(user_object=self.mock_user_object, data=mock_payload)

        # ========================= ASSERT =========================
        expected_calls = [
            call(user_object=self.mock_user_object, name=qualification_1.name, file=None),
            call(user_object=self.mock_user_object, name=qualification_2.name, file=None)
        ]
        
        self.qualification_repository_mock.create.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.qualification_repository_mock.create.call_count, 2)