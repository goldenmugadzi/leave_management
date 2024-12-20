from unittest import TestCase
from unittest.mock import Mock, patch

from ..models.kra import Activity, Target

from ..repository.kra import ActivityTargetRepository
from ..services.kra import KRAErr, TargetService
from ..helpers.types.kra import TargetType

class TestTargeServiceCreate(TestCase):
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
