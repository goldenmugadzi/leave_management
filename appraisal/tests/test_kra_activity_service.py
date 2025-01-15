from unittest import TestCase
from unittest.mock import Mock, patch


from ..helpers.types.kra import KRAType
from ..models import Activity, KeyResultArea, TargetScore
from it.users.models import UserProfile
from ..services.kra import ActivityService, KRAErr, TargetScoreService
from ..repository.kra import KraActivityRepository, TargetScoreRepository

class TestActivityService(TestCase):
    def setUp(self):
        self.mock_activity_repo = Mock(spec=KraActivityRepository)
        self.activity_service = ActivityService(activity_repo=self.mock_activity_repo)

    def mock_kra_object(self):
        mock = Mock(spec=KeyResultArea)
        return mock

    def mock_user_object(self):
        mock = Mock(spec=UserProfile)
        return mock

    def mock_payload(self):
        mock = Mock(spec=KRAType)
        return mock

    def mock_activity_obj(self):
        mock = Mock(spec=Activity)
        return mock

    def test_create_repo_called_once(self):
        # ================ ARRANGE ===================
        mock_kra_obj = self.mock_kra_object()
        mock_assigned_user = self.mock_user_object()
        mock_payload = self.mock_payload()

        # ================ Act ======================
        self.activity_service.create_use_case(kra_object=mock_kra_obj, assigned_user=mock_assigned_user, data=mock_payload)

        # =============== ASSERT ==================
        self.mock_activity_repo.create.assert_called_once_with(
            kra_obj=mock_kra_obj,
            assigned_user=mock_assigned_user,
            data=mock_payload
        )

    def test_activity_created_success(self):
        # =============== ARRANGE =========================
        mock_kra_obj = self.mock_kra_object()
        mock_assigned_user = self.mock_user_object()
        mock_payload = self.mock_payload()
        mock_activity_obj = self.mock_activity_obj()

        self.mock_activity_repo.create.return_value = mock_activity_obj

        # ================ Act ======================
        result = self.activity_service.create_use_case(kra_object=mock_kra_obj, assigned_user=mock_assigned_user, data=mock_payload)

        # ================ ASSERT ===================
        self.assertEqual(result, mock_activity_obj)


    def test_activity_created_failure(self):
        # =============== ARRANGE =========================
        mock_kra_obj = self.mock_kra_object()
        mock_assigned_user = self.mock_user_object()
        mock_payload = self.mock_payload()
        db_err = "Database error"

        with patch.object(self.mock_activity_repo, 'create', side_effect=Exception(db_err)):
            try:
                # ===================== ACT ====================
                self.activity_service.create_use_case(kra_object=mock_kra_obj, assigned_user=mock_assigned_user, data=mock_payload)
                self.fail("Expected an error but got none")
            except KRAErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to create kra activity with error: {db_err}")

class TestActivityWeightedScore(TestCase):
    def setUp(self):
        self.mock_target_score_repo = Mock(spec=TargetScoreRepository)
        self.target_score_service = TargetScoreService(target_score_repository=self.mock_target_score_repo)

    def mock_target_score_obj(self):
        mock = Mock(spec=TargetScore)
        return mock

    def test_repo_handler_error(self):
        # ARRANGE
        activity_id = 4
        db_err = "some database error"

        with patch.object(self.mock_target_score_repo, 'fetch_by_activity_id', side_effect=Exception(db_err)):
            with self.assertRaises(KRAErr) as context:
                # ACT
                self.target_score_service.calculate_activity_weight_score(activity_id=activity_id)

            # ASSERT
            self.assertEqual(str(context.exception), f"Failed to calculate activity score with error: {db_err}")

    def test_total_weight_zero_error(self):
        # ARRANGE
        activity_id = 4
        tagets_objs_list = []
        zero_err = "Total weight for activity cannot be zero."

        # Mock the repository to return an empty list
        self.mock_target_score_repo.fetch_by_activity_id.return_value = tagets_objs_list

        # ACT and ASSERT
        with self.assertRaises(KRAErr) as context:
            self.target_score_service.calculate_activity_weight_score(activity_id=activity_id)

        # Verify the exception message matches the expected error
        self.assertEqual(
            str(context.exception),
            f"Failed to calculate activity score with error: {zero_err}"
        )

    def test_success_weighted_score(self):
        # ARRANGE
        activity_id = 4
        target_score_score_1 = 90
        target_score__weight_1 = 50
        target_score_score_2 = 80
        target_score__weight_2 = 30
        target_score_score_3 = 70
        target_score__weight_3 = 20

        mock_target_score_obj_1 = self.mock_target_score_obj()
        mock_target_score_obj_1.score = target_score_score_1
        mock_target_score_obj_1.target.weight = target_score__weight_1

        mock_target_score_obj_2 = self.mock_target_score_obj()
        mock_target_score_obj_2.score = target_score_score_2
        mock_target_score_obj_2.target.weight = target_score__weight_2

        mock_target_score_obj_3 = self.mock_target_score_obj()
        mock_target_score_obj_3.score = target_score_score_3
        mock_target_score_obj_3.target.weight = target_score__weight_3

        tagets_objs_list = [mock_target_score_obj_1, mock_target_score_obj_2, mock_target_score_obj_3]

        self.mock_target_score_repo.fetch_by_activity_id.return_value = tagets_objs_list
        want = 83
        # ACT
        got = self.target_score_service.calculate_activity_weight_score(activity_id=activity_id)

        # ASSERT
        self.assertEqual(got, want)
