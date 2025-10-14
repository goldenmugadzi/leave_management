from django.test import TestCase

from it.users.models import (
    UserProfile, Application, Roles
)
from fault_locator.central_roles import (
    FaultLocatorRoleManager,
    is_transport_manager,
    is_crane_operator,
)


class FaultLocatorRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up the application record for fault locator
        cls.app = Application.objects.create(name='fault_locator', fullname='Fault Locator System')

        # Ensure the new roles exist
        cls.tm_role, _ = Roles.objects.get_or_create(
            role=FaultLocatorRoleManager.TRANSPORT_MANAGER,
            application='fault_locator',
            app_id=cls.app,
            defaults={'name': 'Transport Manager', 'description': 'Transport Manager'}
        )
        cls.op_role, _ = Roles.objects.get_or_create(
            role=FaultLocatorRoleManager.CRANE_OPERATOR,
            application='fault_locator',
            app_id=cls.app,
            defaults={'name': 'Crane Operator', 'description': 'Crane Operator'}
        )

        # Users
        cls.tm = UserProfile.objects.create_user(username='tm_role', password='Passw0rd!')
        cls.op = UserProfile.objects.create_user(username='op_role', password='Passw0rd!')
        cls.none = UserProfile.objects.create_user(username='no_role', password='Passw0rd!')

        # Assign roles
        assert FaultLocatorRoleManager.assign_role(cls.tm, FaultLocatorRoleManager.TRANSPORT_MANAGER)
        assert FaultLocatorRoleManager.assign_role(cls.op, FaultLocatorRoleManager.CRANE_OPERATOR)

    def test_has_role_checks(self):
        # Positive checks
        self.assertTrue(FaultLocatorRoleManager.has_role(self.tm, FaultLocatorRoleManager.TRANSPORT_MANAGER))
        self.assertTrue(FaultLocatorRoleManager.has_role(self.op, FaultLocatorRoleManager.CRANE_OPERATOR))

        # Negative checks
        self.assertFalse(FaultLocatorRoleManager.has_role(self.tm, FaultLocatorRoleManager.CRANE_OPERATOR))
        self.assertFalse(FaultLocatorRoleManager.has_role(self.op, FaultLocatorRoleManager.TRANSPORT_MANAGER))
        self.assertFalse(FaultLocatorRoleManager.has_role(self.none, FaultLocatorRoleManager.TRANSPORT_MANAGER))
        self.assertFalse(FaultLocatorRoleManager.has_role(self.none, FaultLocatorRoleManager.CRANE_OPERATOR))

    def test_helper_functions(self):
        self.assertTrue(is_transport_manager(self.tm))
        self.assertFalse(is_transport_manager(self.op))
        self.assertFalse(is_transport_manager(self.none))

        self.assertTrue(is_crane_operator(self.op))
        self.assertFalse(is_crane_operator(self.tm))
        self.assertFalse(is_crane_operator(self.none))

    def test_get_user_role_and_display(self):
        # Transport Manager
        self.assertEqual(FaultLocatorRoleManager.get_user_role(self.tm), FaultLocatorRoleManager.TRANSPORT_MANAGER)
        self.assertIn('Transport', FaultLocatorRoleManager.get_user_role_display(self.tm) or '')

        # Crane Operator
        self.assertEqual(FaultLocatorRoleManager.get_user_role(self.op), FaultLocatorRoleManager.CRANE_OPERATOR)
        self.assertIn('Crane', FaultLocatorRoleManager.get_user_role_display(self.op) or '')

        # None
        self.assertIsNone(FaultLocatorRoleManager.get_user_role(self.none))
        self.assertIsNone(FaultLocatorRoleManager.get_user_role_display(self.none))

    def test_has_any_role(self):
        self.assertTrue(FaultLocatorRoleManager.has_any_role(self.tm))
        self.assertTrue(FaultLocatorRoleManager.has_any_role(self.op))
        self.assertFalse(FaultLocatorRoleManager.has_any_role(self.none))
