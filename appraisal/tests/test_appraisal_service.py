from unittest import TestCase
from unittest.mock import Mock, patch
from ..repository import UserQualificationRepository, AppraisalExperienceRepository
from ..services import AppraisalService

class TestAppraisalService(TestCase):
    def setUp(self) -> None:
        self.qualification_repository_mock = Mock(spec=UserQualificationRepository)
        self.appraisal_experience_repository_mock = Mock(spec=AppraisalExperienceRepository)
        self.appraisal_service_mock = AppraisalService(qualification_repository=self.qualification_repository_mock, appraisal_experience_repository=self.appraisal_experience_repository_mock)
    
    def test_appraisal_creation_success(self):
        pass