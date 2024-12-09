from unittest import TestCase
from unittest.mock import patch, Mock
from ..repository.performance import PerformanceReviewRepository
from ..services import PerformanceReviewService
from ..services.performance import PerformanceReviewServiceError
from ..helpers.types import PerformanceReviewType, StrengthAndWeaknessTypes
from ..models import Appraisal, PerformanceProgressReview, PerformanceProgressStrength, PerformanceProgressWeakness

def mock_performance_payload_input():
    mock = Mock(spec=PerformanceReviewType)
    return mock

def mock_performance_review_object():
        mock = Mock(spec=PerformanceProgressReview)
        return mock

class TestPerformanceReviewCreateUseCase(TestCase):
    def setUp(self) -> None:
        self.performance_repo_mock = Mock(spec=PerformanceReviewRepository)
        self.performance_service = PerformanceReviewService(
            performance_repo=self.performance_repo_mock
        )


    def mock_appraisal_object(self):
        mock = Mock(spec=Appraisal)
        return mock

    def test_performance_created_success(self):
        # ================== ARRANGE =========================

        # mock payload
        mock_payload = mock_performance_payload_input()
        mock_payload.quarter = 1

        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object()

        # mock perform review object
        mocked_performance_review_object = mock_performance_review_object()

        # mock performance_create repo
        self.performance_repo_mock.create.return_value = mocked_performance_review_object

        # ================== ACT    ==========================
        got_performance_review_object = self.performance_service.create_use_case(appraisal_object=mock_appraisal_object, data=mock_payload)


        # ================== ASSERT ==========================

        self.performance_repo_mock.create.assert_called_once_with(appraisal_object=mock_appraisal_object, data=mock_payload)
        self.assertEqual(got_performance_review_object, mocked_performance_review_object)

    def test_performance_created_failure(self):
        # ================== ARRANGE =========================

        # mock payload
        mock_payload = mock_performance_payload_input()
        mock_payload.quarter = 1

        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object()

        # mock db error
        db_error_string = "Database Error"

        with patch.object(self.performance_repo_mock, 'create', side_effect=Exception(db_error_string)):
            try:
                # ================== ACT    ==========================
                self.performance_service.create_use_case(appraisal_object=mock_appraisal_object, data=mock_payload)
                self.fail("Expected PerformanceReviewCreationError not raised")
            except PerformanceReviewServiceError as e:
                # ================== ASSERT ==========================
                self.performance_repo_mock.create.assert_called_once_with(appraisal_object=mock_appraisal_object, data=mock_payload)
                self.assertEqual(str(e), f"Failed to create performance review with error: {db_error_string}")


class TestAddStrengthUseCases(TestCase):
    def setUp(self) -> None:
        self.performance_repo_mock = Mock(spec=PerformanceReviewRepository)
        self.performance_service = PerformanceReviewService(
            performance_repo=self.performance_repo_mock
        )

    def get_strength_payload_objects(self):
        # mock strengths payload
        strengths_1 = StrengthAndWeaknessTypes(name="Problem solver")
        strengths_2 = StrengthAndWeaknessTypes(name="Details Oriented")
        mock_strengths_payload = [strengths_1, strengths_2]

        # mock strengths objects
        strengths_object_1 = PerformanceProgressStrength(name=strengths_1.name)
        strengths_object_2 = PerformanceProgressStrength(name=strengths_2.name)
        mock_strengths_objects = [strengths_object_1, strengths_object_2]

        return mock_strengths_payload, mock_strengths_objects

    def test_add_strengths_success(self):
        # ================ ARRANGE =============

        # mock performance_review_object
        mock_performance_object = mock_performance_review_object()

        # mock strengths payloads and objects
        _, mock_strengths_objects = self.get_strength_payload_objects()

        # mock add_strengths repo
        self.performance_repo_mock.add_strengths.return_value = None

        # ================ ACT =============
        self.performance_service.add_strengths_use_case(performance_review_object=mock_performance_object, strengths=mock_strengths_objects)

        # =============== ASSERT ================
        self.performance_repo_mock.add_strengths.assert_called_once_with(performance_review_object=mock_performance_object, strengths=mock_strengths_objects)

    def test_add_strengths_error_handling(self):
        # ================ ARRANGE =============

        # Mock performance_review_object
        mock_performance_object = mock_performance_review_object()

        # Mock strengths payloads
        _, mock_strengths_object = self.get_strength_payload_objects()

        # Mock map_performance_strengths to raise an exception
        self.performance_repo_mock.add_strengths.side_effect = Exception("Mocked mapping error")

        # ================ ACT & ASSERT =============
        with self.assertRaises(PerformanceReviewServiceError) as context:
            self.performance_service.add_strengths_use_case(performance_review_object=mock_performance_object, strengths=mock_strengths_object)

        # Verify the exception message
        self.assertIn("Failed to add performance strengths with error: Mocked mapping error", str(context.exception))

class TestAddWeaknessUseCases(TestCase):
    def setUp(self) -> None:
        self.performance_repo_mock = Mock(spec=PerformanceReviewRepository)
        self.performance_service = PerformanceReviewService(
            performance_repo=self.performance_repo_mock
        )

    def get_strength_payload_objects(self):
        # mock weakness payload
        weakness_1 = StrengthAndWeaknessTypes(name="Overthinker")
        weakness_2 = StrengthAndWeaknessTypes(name="Slow")
        mock_weakness_payload = [weakness_1, weakness_2]

        # mock weakness objects
        weakness_object_1 = PerformanceProgressWeakness(name=weakness_1.name)
        weakness_object_2 = PerformanceProgressWeakness(name=weakness_2.name)
        mock_weakness_objects = [weakness_object_1, weakness_object_2]

        return mock_weakness_payload, mock_weakness_objects

    def test_add_weakness_success(self):
        # ================ ARRANGE =============

        # mock performance_review_object
        mock_performance_object = mock_performance_review_object()

        # mock weakness payloads and objects
        mock_weakness_payload, mock_weakness_objects = self.get_strength_payload_objects()

        # mock add_weakness repo
        self.performance_repo_mock.add_weaknesses.return_value = None

        # ================ ACT =============
        self.performance_service.add_weakness_use_case(performance_review_object=mock_performance_object, weaknesses=mock_weakness_objects)

        # =============== ASSERT ================
        self.performance_repo_mock.add_weaknesses.assert_called_once_with(performance_review_object=mock_performance_object, weaknesses=mock_weakness_objects)

    def test_add_strengths_error_handling(self):
        # ================ ARRANGE =============

        # Mock performance_review_object
        mock_performance_object = mock_performance_review_object()

        # Mock weakness payloads
        _, mock_weakness_objects = self.get_strength_payload_objects()

        # Mock map_performance_weaknesses to raise an exception
        self.performance_repo_mock.add_weaknesses.side_effect = Exception("Mocked mapping error")

        # ================ ACT & ASSERT =============
        with self.assertRaises(PerformanceReviewServiceError) as context:
            self.performance_service.add_weakness_use_case(performance_review_object=mock_performance_object, weaknesses=mock_weakness_objects)

        # Verify the exception message
        self.assertIn("Failed to add performance weaknesses with error: Mocked mapping error", str(context.exception))
