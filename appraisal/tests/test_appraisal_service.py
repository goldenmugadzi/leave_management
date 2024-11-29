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


@patch("appraisal.services.appraisal.transaction.atomic")
class TestAppraisalServiceCreateUseCase(TestCase):

    def setUp(self) -> None:
        # Mock repositories
        self.qualification_repository_mock = Mock(spec=UserQualificationRepository)
        self.appraisal_experience_repository_mock = Mock(spec=AppraisalExperienceRepository)
        self.experience_repository_mock = Mock(spec=ExperienceRepository)
        self.appraisal_repository_mock = Mock(spec=AppraisalRepository)

        # Mock Process object
        self.mock_process_object = Mock(spec=Process)

        # Mock UserProfile
        self.mock_user_object = Mock(spec=UserProfile)

        # AppraisalService init
        self.appraisal_service = AppraisalService(
            appraisal_experience_repository=self.appraisal_experience_repository_mock,
            experience_repository=self.experience_repository_mock,
            qualification_repository=self.qualification_repository_mock,
            appraisal_repository=self.appraisal_repository_mock
        )

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

    def test_appraisal_object_creation_success(self, mock_atomic):

        # =========================== ARRANGE ========================

        # Mock AppraisalPayloadType input and process object
        mock_data = self.mock_appraisal_payload_input()
        mock_process_object = self.mock_process_object

        # mock Appraisal object
        mock_appraisal_object = self.mock_appraisal_object(process_object=mock_process_object)
        self.appraisal_repository_mock.create.return_value = mock_appraisal_object

        # ========================= ACT ================================
        result = self.appraisal_service.create_use_case(
            user_object=self.mock_user_object,
            process_object=mock_process_object,
            data=mock_data
        )

        # ======================= ASSERT ================================
        self.appraisal_repository_mock.create.assert_called_once_with(user_object=self.mock_user_object, process_object=mock_process_object)
        self.assertEqual(result, mock_appraisal_object)

    def test_appraisal_object_creation_failure(self, mock_atomic):

        # =========================== ARRANGE ========================

        # Create a single mock process object to be used consistently
        mock_process_object = self.mock_process_object

       # Mock AppraisalPayloadType input
        mock_data = self.mock_appraisal_payload_input()
        db_err_str = "Database error"

        with patch.object(self.appraisal_repository_mock, 'create', side_effect=Exception(db_err_str)):

            # ========================= ACT ============================
            try:
                self.appraisal_service.create_use_case(
                    user_object=self.mock_user_object,
                   process_object=mock_process_object,
                  data=mock_data)
                self.fail("Expected AppraisalCreationError not raised")
            except AppraisalCreationError as e:
                # ===================== ASSERT ============================

                self.assertEqual(str(e), f"Failed to create appraisal with error: {db_err_str}")

    def test_experience_object_creation_success(self, mock_atomic):
        # =================== ARRANGE =====================

        # Create a single mock process object to be used consistently
        mock_process_object = self.mock_process_object

        experience_type = ExperienceType(name="Python", years_of_experience=1, months_of_experience=1)
        experiences = [experience_type]

        mock_approval_payload = self.mock_appraisal_payload_input(experiences=experiences)

        mock_experience_object = self.mock_experience_object(name=experience_type.name)
        self.experience_repository_mock.get_or_create.return_value = mock_experience_object

        # ==================== ACT =====================
        self.appraisal_service.create_use_case(
            user_object=self.mock_user_object,
           process_object=mock_process_object,
          data=mock_approval_payload)

        # ==================== ASSERT ===================
        self.experience_repository_mock.get_or_create.assert_called_once_with(name=experience_type.name)

    def test_multiple_experience_object_creation_success(self, mock_atomic):

        # =================== ARRANGE =====================
        experience_type_1 = ExperienceType(name="Golang", years_of_experience=1, months_of_experience=1)
        experience_type_2 = ExperienceType(name="Python", years_of_experience=1, months_of_experience=1)
        experiences = [experience_type_1, experience_type_2]

        mock_approval_payload = self.mock_appraisal_payload_input(experiences=experiences)

        for experience in experiences:
            mock_experience_object = self.mock_experience_object(name=experience.name)
            self.experience_repository_mock.get_or_create.return_value = mock_experience_object

        # ==================== ACT =====================
        self.appraisal_service.create_use_case(
            user_object=self.mock_user_object,
           process_object=self.mock_process_object,
          data=mock_approval_payload)

        # ==================== ASSERT ===================
        self.assertEqual(self.experience_repository_mock.get_or_create.call_count, 2)

        expected_calls = [
            call(name=experience_type_1.name),
            call(name=experience_type_2.name)
        ]
        self.experience_repository_mock.get_or_create.assert_has_calls(expected_calls, any_order=False)


    def test_adding_experience_appraisal(self, mock_atomic):
        # =============================== ARRANGE =====================

        # Create a single mock process object to be used consistently
        mock_process_object = self.mock_process_object

        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object(process_object=mock_process_object)
        self.appraisal_repository_mock.create.return_value = mock_appraisal_object

        # mock payload data
        experience_type_1 = ExperienceType(name="Golang", years_of_experience=1, months_of_experience=1)
        experience_type_2 = ExperienceType(name="Python", years_of_experience=1, months_of_experience=1)
        experiences = [experience_type_1, experience_type_2]

        mock_approval_payload = self.mock_appraisal_payload_input(experiences=experiences)

        # Create distinct mocks for each experience
        experience_objects = {
            "Golang": self.mock_experience_object(name="Golang"),
            "Python": self.mock_experience_object(name="Python"),
        }

        # Return appropriate mock objects for each experience
        def get_experience_mock(name):
            return experience_objects[name]

        self.experience_repository_mock.get_or_create.side_effect = lambda name: get_experience_mock(name)

        # Mock add_experience calls
        expected_calls = []
        for experience in experiences:
            expected_calls.append(call(
                appraisal_object=mock_appraisal_object,
                experience_object=experience_objects[experience.name],
                data=experience,
                ))
        # ========================== ACT =========================
        self.appraisal_service.create_use_case(
            user_object=self.mock_user_object,
            process_object=mock_process_object,
            data=mock_approval_payload)

        # ========================== ASSERT ======================
        self.appraisal_repository_mock.add_experience.assert_has_calls(expected_calls, any_order=False)

        self.assertEqual(self.appraisal_repository_mock.add_experience.call_count, 2)

    def test_user_qualification_create(self, mock_atomic):
        # ========================= ARRANGE ========================

        # mock process object
        mock_process_object = self.mock_process_object

        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object(process_object=mock_process_object)
        self.appraisal_repository_mock.create.return_value = mock_appraisal_object

        # mock qualifications payload
        qualification_1 = QualificationsType(name="AWS", file=None)
        qualification_2 = QualificationsType(name="AWS", file=None)

        qualifications = [qualification_1, qualification_2]
        mock_payload = self.mock_appraisal_payload_input(qualifications=qualifications)

        # mock qualification create repo
        for _ in qualifications:
            self.qualification_repository_mock.create.return_value = None

        # ========================= ACT ============================
        self.appraisal_service.create_use_case(
            user_object=self.mock_user_object,
            process_object=mock_process_object,
            data=mock_payload)

        # ========================= ASSERT =========================
        expected_calls = [
            call(user_object=self.mock_user_object, name=qualification_1.name, file=None),
            call(user_object=self.mock_user_object, name=qualification_2.name, file=None)
        ]

        self.qualification_repository_mock.create.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.qualification_repository_mock.create.call_count, 2)
