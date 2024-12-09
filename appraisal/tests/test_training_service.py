from unittest import TestCase
from unittest.mock import patch, Mock

from appraisal.models.appraisal import Appraisal
from appraisal.models.training import TrainingAndDevelopment
from ..repository.training import TrainingAndDevelopmentRepository
from ..services.training import TrainingAndDevelopmentService, TrainingAndDevelopmentServiceErr


class TestTrainingService(TestCase):
    def setUp(self) -> None:
        self.mock_training_dev_repo = Mock(spec=TrainingAndDevelopmentRepository)
        self.mock_training_dev_service = TrainingAndDevelopmentService(
            training_dev_repo = self.mock_training_dev_repo
        )

    def mock_training_dev_object(self):
        mock = Mock(spec=TrainingAndDevelopment)
        return mock

    def test_create_training_object_success(self):
        # =========== ARRANGE ==============

        mock_appraisal_object = Mock(spec=Appraisal)
        quarter = 1

        mock_training_dev_object = self.mock_training_dev_repo()

        self.mock_training_dev_repo.create.return_value = mock_training_dev_object

        # ============= ACT =================
        result = self.mock_training_dev_service.create_use_case(appraisal_object=mock_appraisal_object, quarter=quarter)

        # ============= ASSERT ===============
        self.mock_training_dev_repo.create.assert_called_once_with(appraisal_object=mock_appraisal_object, quarter=quarter)
        self.assertEqual(result, mock_training_dev_object)

    def test_create_training_object_failure(self):
        # =========== ARRANGE ==============

        mock_appraisal_object = Mock(spec=Appraisal)
        quarter = 1
        db_error_str = "Some database error"

        self.mock_training_dev_repo.create.return_value = None

        # ============= ACT =================
        with patch.object(self.mock_training_dev_repo, 'create', side_effect=Exception(db_error_str)):
            try:
                self.mock_training_dev_service.create_use_case(appraisal_object=mock_appraisal_object, quarter=quarter)
                self.fail("Expected Creation error, but not raised")
            except TrainingAndDevelopmentServiceErr as e:
                # ============= ASSERT ===============
                self.assertEqual(str(e), f"Failed to create training and development with error: {db_error_str}")
