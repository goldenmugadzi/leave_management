from unittest import TestCase
from unittest.mock import Mock, call, patch
from ..repository.performance import PerformanceReviewRepository
from ..services import PerformanceReviewService
from ..helpers.types import PerformanceReviewType
from ..models import Appraisal, PerformanceProgressReview


class TestPerformanceReviewCreateUseCase(TestCase):
    def setUp(self) -> None:
        self.performance_repo_mock = Mock(spec=PerformanceReviewRepository)
        self.performance_service = PerformanceReviewService(
            performance_repo=self.performance_repo_mock
        )
        
    def mock_performance_payload_input(self):
        mock = Mock(spec=PerformanceReviewType)
        return mock
    
    def mock_appraisal_object(self):
        mock = Mock(spec=Appraisal)
        return mock
    
    def mock_performance_review_object(self):
        mock = Mock(spec=PerformanceProgressReview)
        return mock
    
    def test_performance_created_success(self):
        # ================== ARRANGE =========================
        
        # mock payload
        mock_payload = self.mock_performance_payload_input()
        mock_payload.quarter = 1
        
        # mock appraisal object
        mock_appraisal_object = self.mock_appraisal_object()
        
        # mock perform review object
        mocked_performance_review_object = self.mock_performance_review_object()
        
        # mock performance_create repo
        self.performance_repo_mock.create.return_value = mocked_performance_review_object
        
        # ================== ACT    ==========================
        got_performance_review_object = self.performance_service.create_use_case(appraisal_object=mock_appraisal_object, data=mock_payload)
        
        
        # ================== ASSERT ==========================
        
        self.performance_repo_mock.create.assert_called_once_with(appraisal_object=mock_appraisal_object, data=mock_payload)
        self.assertEqual(got_performance_review_object, mocked_performance_review_object)