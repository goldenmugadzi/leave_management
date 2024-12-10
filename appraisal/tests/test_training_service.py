from typing import List
from unittest import TestCase
from unittest.mock import patch, Mock

from appraisal.models.appraisal import Appraisal
from appraisal.models.training import TrainingAndDevelopment
from appraisal.helpers.types.training import CompetencyType, InterventionStrategyType, TrainingAndDevelopmentCreateUpdateType
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

    def mock_appraisal_object(self):
        mock = Mock(spec=Appraisal)
        return mock

    def test_create_training_object_success(self):
        # =========== ARRANGE ==============

        mock_appraisal_object = self.mock_appraisal_object()
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

        mock_appraisal_object = self.mock_appraisal_object()
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

    def mock_training_dev_payload(self, required_competency: List[CompetencyType]=[], competency_gaps: List[CompetencyType]=[], intervention_strategies: List[InterventionStrategyType]=[], action_recommended: str='', action_taken: str=''):
        mock = Mock(spec=TrainingAndDevelopmentCreateUpdateType)
        mock.required_competencies = required_competency
        mock.competency_gaps = competency_gaps
        mock.intervention_strategies = intervention_strategies
        mock.action_recommended = action_recommended
        mock.action_taken = action_taken
        return mock

    def mock_training_development_object(self):
        mock =Mock(spec=TrainingAndDevelopment)
        return mock

    def test_update_training_dev_repo_called_once(self):
        # ============ ARRANGE ===============
        mock_training_development_object = self.mock_training_development_object()

        mock_payload = self.mock_training_dev_payload()
        # ============ ACT ===============
        self.mock_training_dev_service.update_use_case(training_development_object=mock_training_development_object, payload=mock_payload)

        # ============ ASSERT ===============
        self.mock_training_dev_repo.update.assert_called_once_with(
            training_development_object=mock_training_development_object,
            data=mock_payload
        )

    def test_update_training_dev_create_success(self):
        # ============ ARRANGE ===============
        mock_training_development_object = self.mock_training_development_object()

        mock_payload = self.mock_training_dev_payload()
        self.mock_training_dev_repo.update.return_value = mock_training_development_object

        # ============ ACT ===============
        result = self.mock_training_dev_service.update_use_case(training_development_object=mock_training_development_object, payload=mock_payload)

        # ============ ASSERT ===============
        self.assertEqual(result, mock_training_development_object)

    def test_update_training_dev_create_failure(self):
        # ============ ARRANGE ===============
        mock_training_development_object = self.mock_training_development_object()

        mock_payload = self.mock_training_dev_payload()
        mock_db_err = "Some database error"

        with patch.object(self.mock_training_dev_repo, 'update', side_effect=Exception(mock_db_err)):
            try:
                # ============ ACT ===============
                self.mock_training_dev_service.update_use_case(training_development_object=mock_training_development_object, payload=mock_payload)
                self.fail("Expected an error but got none")
            except TrainingAndDevelopmentServiceErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to update training and development with error: {mock_db_err}")
