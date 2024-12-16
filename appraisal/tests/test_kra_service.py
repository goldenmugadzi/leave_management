from unittest import TestCase
from unittest.mock import Mock, patch


from ..helpers.types.kra import KRAType
from ..models import YearQuarter, KeyResultArea
from it.users.models import UserProfile
from ..services.kra import KRAService, KRAServiceErr
from ..repository.kra import KRARepository

class TestKRAService(TestCase):
    def setUp(self) -> None:
        self.mock_kra_repo = Mock(spec=KRARepository)
        self.kra_servise = KRAService(
            kra_repo = self.mock_kra_repo
        )

    def mock_quarter_obj(self):
        mock = Mock(spec=YearQuarter)
        return mock

    def mock_user_obj(self):
        mock = Mock(spec=UserProfile)
        return mock

    def mock_payload(self):
        mock = Mock(spec=KRAType)
        return mock

    def mock_created_kra_obj(self):
        mock = Mock(spec=KeyResultArea)
        return mock

    def test_create_repo_called_once(self):
        # =========== ARRANGE ==============
        mock_quarter = self.mock_quarter_obj()
        mock_creator = self.mock_user_obj()
        mock_payload = self.mock_payload()

        # =========== ACT ==============
        self.kra_servise.create_use_case(quarter_obj=mock_quarter, creator_obj=mock_creator, data=mock_payload)

        # =========== ASSERT =============
        self.mock_kra_repo.create.assert_called_once_with(
            quarter_obj=mock_quarter,
            creator_obj=mock_creator,
            data=mock_payload
        )



    def test_create_kra_success(self):
        # =========== ARRANGE ==============
        mock_quarter = self.mock_quarter_obj()
        mock_creator = self.mock_user_obj()
        mock_payload = self.mock_payload()
        mock_kra_obj = self.mock_created_kra_obj()

        self.mock_kra_repo.create.return_value = mock_kra_obj

        # =========== ACT ==============
        result = self.kra_servise.create_use_case(quarter_obj=mock_quarter, creator_obj=mock_creator, data=mock_payload)

        # =========== ASSERT =============
        self.assertEqual(result, mock_kra_obj)

    def test_create_kra_failure(self):
        # =========== ARRANGE ==============
        mock_quarter = self.mock_quarter_obj()
        mock_creator = self.mock_user_obj()
        mock_payload = self.mock_payload()
        mock_db_err = "Some database error"

        with patch.object(self.mock_kra_repo, 'create', side_effect=Exception(mock_db_err)):
            try:
                # ============ ACT ===============
                self.kra_servise.create_use_case(quarter_obj=mock_quarter, creator_obj=mock_creator, data=mock_payload)
                self.fail("Expected an error but got none")
            except KRAServiceErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to create kra with error: {mock_db_err}")

    def mock_kra_object(self):
        mock = Mock(spec=KeyResultArea)
        return mock

    def test_update_repo_called_once(self):
        # =========== ARRANGE ==============
        mock_quarter = self.mock_quarter_obj()
        mock_payload = self.mock_payload()
        mock_kra = self.mock_kra_object()

        # =========== ACT ==============
        self.kra_servise.update_use_case(kra_object=mock_kra, quarter_obj=mock_quarter, data=mock_payload)

        # =========== ASSERT =============
        self.mock_kra_repo.update.assert_called_once_with(
            quarter_obj=mock_quarter,
            kra_object=mock_kra,
            data=mock_payload
        )



    def test_update_kra_success(self):
        # =========== ARRANGE ==============
        mock_quarter = self.mock_quarter_obj()
        mock_payload = self.mock_payload()
        mock_kra = self.mock_kra_object()
        mock_kra_obj = self.mock_kra_object()

        self.mock_kra_repo.update.return_value = mock_kra_obj

        # =========== ACT ==============
        result = self.kra_servise.update_use_case(kra_object=mock_kra, quarter_obj=mock_quarter, data=mock_payload)

        # =========== ASSERT =============
        self.assertEqual(result, mock_kra_obj)

    def test_update_kra_failure(self):
        # =========== ARRANGE ==============
        mock_quarter = self.mock_quarter_obj()
        mock_payload = self.mock_payload()
        mock_kra = self.mock_kra_object()
        mock_db_err = "Some database error"

        with patch.object(self.mock_kra_repo, 'update', side_effect=Exception(mock_db_err)):
            try:
                # ============ ACT ===============
                self.kra_servise.update_use_case(kra_object=mock_kra, quarter_obj=mock_quarter, data=mock_payload)
                self.fail("Expected an error but got none")
            except KRAServiceErr as e:
                # ============ ASSERT ===============
                self.assertEqual(str(e), f"Failed to update kra with error: {mock_db_err}")
