from unittest import TestCase
from unittest.mock import Mock, patch

from ..models.kra import Activity, Target, TargetScore

from ..repository.kra import ActivityTargetRepository, TargetScoreRepository
from ..services.kra import KRAErr, TargetService, TargetScoreService
from ..helpers.types.kra import TargetType, TargetScoreType

class TestTargeService(TestCase):
    def setUp(self) -> None:
        self.mock_repo = Mock(spec=ActivityTargetRepository)
        self.service_handler = TargetService(target_repository=self.mock_repo)

    def mock_activity_obj(self):
        mock = Mock(spec=Activity)
        return mock

    def mock_payload(self):
        mock = Mock(spec=TargetType)
        return mock

    def mock_target_obj(self):
        mock = Mock(spec=Target)
        return mock

    def test_create_repo_called_once(self):
        # ========================= ARRANGE =========================
        mock_activity_obj = self.mock_activity_obj()
        mock_payload = self.mock_payload()

        # ================= ACT =====================
        self.service_handler.create_use_case(activity_obj=mock_activity_obj, payload=mock_payload)

        # ================ ASSERT ===================
        self.mock_repo.create.assert_called_once_with(activity_obj=mock_activity_obj, data=mock_payload)


    def test_target_created_success(self):
        # ========================= ARRANGE =========================
        mock_activity_obj = self.mock_activity_obj()
        mock_payload = self.mock_payload()
        mock_target = self.mock_target_obj()

        self.mock_repo.create.return_value = mock_target

        # ==================== ACT ========================
        result = self.service_handler.create_use_case(activity_obj=mock_activity_obj, payload=mock_payload)

        # ================= ASSERT ========================
        self.assertEqual(result, mock_target)

    def test_target_created_failure(self):
        # ========================= ARRANGE =========================
        mock_activity_obj = self.mock_activity_obj()
        mock_payload = self.mock_payload()
        db_err = "Some database error"

        with patch.object(self.mock_repo, 'create', side_effect=Exception(db_err)):
            try:
                # ==================== ACT ========================
                self.service_handler.create_use_case(activity_obj=mock_activity_obj, payload=mock_payload)
                self.fail("Expected an error but got none")
            except KRAErr as e:
                # ================= ASSERT ========================
                self.assertEqual(str(e), f"Create failed with error: {db_err}")

    def test_update_repo_called_once(self):
        # ========================= ARRANGE =========================
        mock_target_obj = self.mock_target_obj()
        mock_payload = self.mock_payload()

        # ================= ACT =====================
        self.service_handler.update_use_case(target_obj=mock_target_obj, payload=mock_payload)

        # ================ ASSERT ===================
        self.mock_repo.update.assert_called_once_with(target_obj=mock_target_obj, payload=mock_payload)

    def test_update_usecase_success(self):
        # ========================= ARRANGE =========================
        mock_target_obj = self.mock_target_obj()
        mock_payload = self.mock_payload()
        self.mock_repo.update.return_value = mock_payload

        # ================= ACT =====================
        result = self.service_handler.update_use_case(target_obj=mock_target_obj, payload=mock_payload)

        # ================ ASSERT ===================
        self.assertEqual(result, mock_payload)

    def test_update_usecase_failure(self):
        # =========== ARRANGE ==============
        mock_target_obj = self.mock_target_obj()
        mock_payload = self.mock_payload()
        mock_db_err = "Some database error"

        with patch.object(self.mock_repo, 'update', side_effect=Exception(mock_db_err)):
            try:
                # ============ ACT ===============
                self.service_handler.update_use_case(target_obj=mock_target_obj, payload=mock_payload)
                self.fail("Expected an error but got none")
            except KRAErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to update target with error: {mock_db_err}")


class TestTargetScoreService(TestCase):
    def setUp(self) -> None:
        self.mock_repo = Mock(spec=TargetScoreRepository)
        self.service = TargetScoreService(target_score_repository=self.mock_repo)

    def mock_target_obj(self):
        mock = Mock(spec=Target)
        return mock

    def mock_payload(self):
        mock = Mock(spec=TargetScoreType)
        return mock

    def mock_target_score_obj(self):
        mock = Mock(spec=TargetScore)
        return mock

    def test_create_repo_called_once(self):
        # ============= ARRANGE =================
        mock_target_object = self.mock_target_obj()
        mock_payload = self.mock_payload()

        # ============ ACT ====================
        self.service.create_use_case(target_obj=mock_target_object, data=mock_payload)

        # ============ ASSERT ===================
        self.mock_repo.create.assert_called_once_with(target_obj=mock_target_object, data=mock_payload)

    def test_create_use_case_success(self):
        # ============= ARRANGE =================
        mock_target_object = self.mock_target_obj()
        mock_payload = self.mock_payload()
        mock_score_obj = self.mock_target_score_obj()

        self.mock_repo.create.return_value = mock_score_obj

        # ============ ACT ====================
        result = self.service.create_use_case(target_obj=mock_target_object, data=mock_payload)

        # ============ ASSERT ===================
        self.assertEqual(result, mock_score_obj)

    def test_create_usecase_failure(self):
        # =========== ARRANGE ==============
        mock_target_object = self.mock_target_obj()
        mock_payload = self.mock_payload()
        mock_db_err = "Some database error"

        with patch.object(self.mock_repo, 'create', side_effect=Exception(mock_db_err)):
            try:
                # ============ ACT ===============
                self.service.create_use_case(target_obj=mock_target_object, data=mock_payload)
                self.fail("Expected an error but got none")
            except KRAErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to create target-score with error: {mock_db_err}")

    def mock_target_score_object(self):
        mock = Mock(spec=TargetScore)
        return mock

    def test_update_repo_called_once(self):
        # ============= ARRANGE =================
        mock_target_score_object = self.mock_target_score_object()
        mock_payload = self.mock_payload()

        # ============ ACT ====================
        self.service.update_use_case(target_score_obj=mock_target_score_object, data=mock_payload)

        # ============ ASSERT ===================
        self.mock_repo.update.assert_called_once_with(target_score_obj=mock_target_score_object, data=mock_payload)

    def test_update_use_case_success(self):
        # ============= ARRANGE =================
        mock_target_score_object = self.mock_target_score_object()
        mock_payload = self.mock_payload()
        self.mock_repo.update.return_value = mock_target_score_object

        # ============ ACT ====================
        result = self.service.update_use_case(target_score_obj=mock_target_score_object, data=mock_payload)

        # ============ ASSERT ===================
        self.assertEqual(result, mock_target_score_object)

    def test_update_usecase_failure(self):
        # =========== ARRANGE ==============
        mock_target_score_object = self.mock_target_score_object()
        mock_payload = self.mock_payload()
        mock_db_err = "Some database error"

        with patch.object(self.mock_repo, 'update', side_effect=Exception(mock_db_err)):
            try:
                # ============ ACT ===============
                self.service.update_use_case(target_score_obj=mock_target_score_object, data=mock_payload)
                self.fail("Expected an error but got none")
            except KRAErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to update target-score with error: {mock_db_err}")
class TestTargetScoreRatingCalculation(TestCase):
    def setUp(self) -> None:
        self.mock_repo = Mock(spec=TargetScoreRepository)
        self.service = TargetScoreService(target_score_repository=self.mock_repo)

    def mock_target_score_object(self):
        mock = Mock(spec=TargetScore)
        return mock

    def test_target_score_repo_called_once(self):
        # ARRANGE
        activity_id = 4
        activity_id = 4
        actual_score = 90
        target_score = 100
        allowable_variance = 15

        mock_target_score = self.mock_target_score_object()
        mock_target_score.score = actual_score
        mock_target_score.target.agreed_target = target_score
        mock_target_score.target.allowable_variance = allowable_variance
        self.mock_repo.fetch_by_activity_id.return_value = mock_target_score

        # ACT
        self.service.calculate_activity_score_use_case(activity_id=activity_id)
        # ASSERT
        self.mock_repo.fetch_by_activity_id.assert_called_once_with(activity_id=activity_id)

    # def test_target_score_get_actual_variance_called_once(self):
    #     # ARRANGE
    #     activity_id = 4
    #     actual_score = 90
    #     target_score = 100

    #     mock_target_score = self.mock_target_score_object()
    #     mock_target_score.score = actual_score
    #     mock_target_score.target.agreed_target = target_score

    #     self.mock_repo.fetch_by_activity_id.return_value = mock_target_score

    #     # ACT AND ASSERT
    #     with patch("appraisal.services.kra.get_actual_variance") as actual_variance_method:
    #         self.service.calculate_activity_score_use_case(activity_id=activity_id)
    #         actual_variance_method.assert_called_once_with(actual_score=actual_score, target_score=target_score)

    # @patch("appraisal.services.kra.get_actual_variance")
    # def test_target_score_get_within_called_once(self, mock_get_actual_variance):
    #     # ARRANGE
    #     activity_id = 4
    #     actual_variance = 3
    #     allowable_variance = 5

    #     mock_get_actual_variance.return_value = actual_variance
    #     mock_target_score = self.mock_target_score_object()
    #     mock_target_score.target.allowable_variance = allowable_variance

    #     self.mock_repo.fetch_by_activity_id.return_value = mock_target_score

    #     # ACT AND ASSERT
    #     with patch("appraisal.services.kra.get_within_condition") as get_within_condition:
    #         self.service.calculate_activity_score_use_case(activity_id=activity_id)
    #         get_within_condition.assert_called_once_with(actual_variance=actual_variance, allowable_variance=allowable_variance)

    # @patch("appraisal.services.kra.get_actual_variance")
    # @patch("appraisal.services.kra.get_within_condition")
    # def test_target_score_get_rating_called_once(self, mock_get_actual_variance, mock_get_within_condition):
    #     # ARRANGE
    #     activity_id = 4
    #     actual_variance = 1
    #     within_condition = 0.8

    #     mock_get_actual_variance.return_value = actual_variance
    #     mock_get_within_condition.return_value = within_condition
    #     mock_target_score = self.mock_target_score_object()

    #     self.mock_repo.fetch_by_activity_id.return_value = mock_target_score

    #     # ACT AND ASSERT
    #     with patch("appraisal.services.kra.get_rating") as get_rating:
    #         self.service.calculate_activity_score_use_case(activity_id=activity_id)
    #         get_rating.assert_called_once_with(actual_variance=actual_variance, within_condition=within_condition)

    def test__success(self):
        # ARRANGE
        activity_id = 4
        actual_score = 90
        target_score = 100
        allowable_variance = 15

        mock_target_score = self.mock_target_score_object()
        mock_target_score.score = actual_score
        mock_target_score.target.agreed_target = target_score
        mock_target_score.target.allowable_variance = allowable_variance
        self.mock_repo.fetch_by_activity_id.return_value = mock_target_score

        want = 5

        # ACT
        got = self.service.calculate_activity_score_use_case(activity_id=activity_id)

        # ASSERT
        self.assertEqual(got, want)

    def test_calculate_activity_score_failure(self):
        # ARRANGE
        activity_id = 4
        db_err = "some db error"

        with patch.object(self.mock_repo, 'fetch_by_activity_id', side_effect=Exception(db_err)):
            with self.assertRaises(KRAErr) as context:
                # ACT
                self.service.calculate_activity_score_use_case(activity_id=activity_id)

            # ASSERT
            self.assertEqual(str(context.exception), f"Activity Score calculation failed with error: {db_err}")
