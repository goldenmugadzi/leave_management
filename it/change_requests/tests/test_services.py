"""
Unit tests for change_requests service layer

Tests the refactored service layer components including:
- ChangeRequestService
- ApprovalService
- NotificationService
- CRTypeHandlers
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock, Mock
from it.change_requests.models import ChangeRequest, NewProfile, ProfileChange, ProfileDeactivation, CRApproval
from it.users.models import UserProfile, Regions, CostCenter, Designations, Application, Roles, Sections, Districts

from it.change_requests.services import (
    ChangeRequestService,
    CRTypeHandler,
    ApprovalService,
    ApprovalWorkflow,
    NotificationService,
    ContextBuilder,
    NewProfileHandler,
    ProfileModificationHandler,
    ProfileDeactivationHandler
)


class ChangeRequestServiceTestCase(TestCase):
    """Test cases for ChangeRequestService"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(id="CC100", code="CC100", name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
    
    def test_validate_cr_data_valid(self):
        """Test validation with valid CR data"""
        valid_data = {
            'change_reason': 'Valid reason for change',
            'change_description': 'Detailed description of the change'
        }
        errors = ChangeRequestService.validate_cr_data('NEW_PROFILE', valid_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_cr_data_missing_reason(self):
        """Test validation with missing change reason"""
        invalid_data = {
            'change_reason': '',
            'change_description': 'Valid description'
        }
        errors = ChangeRequestService.validate_cr_data('NEW_PROFILE', invalid_data)
        self.assertGreater(len(errors), 0)
    
    def test_validate_new_profile_data_valid(self):
        """Test validation with valid new profile data"""
        valid_data = {
            'username': 'newuser123',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com'
        }
        errors = ChangeRequestService.validate_new_profile_data(valid_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_new_profile_data_invalid_email(self):
        """Test validation with invalid email"""
        invalid_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'invalid-email'
        }
        errors = ChangeRequestService.validate_new_profile_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('email' in error.lower() for error in errors))
    
    def test_create_new_profile_cr(self):
        """Test creating a new profile change request"""
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'designation': self.designation.id,
            'for_application': 'BUSINESS EXCELLENCE',
            'change_reason': 'Need new user account',
            'change_description': 'Creating account for new employee',
            'roles_to_action': 'Assign basic user role'
        }
        
        cr = ChangeRequestService.create_new_profile_cr(data, self.user)
        
        self.assertIsNotNone(cr)
        self.assertEqual(cr.change_type, 'New Profile')
        self.assertIsNotNone(cr.new_profile)
        self.assertEqual(cr.new_profile.username, 'newuser')
        self.assertEqual(cr.created_by, self.user)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_new_profile_request(self, suffix: str = "001") -> ChangeRequest:
        profile = NewProfile.objects.create(
            username=f"np{suffix}",
            first_name="First",
            last_name="Last",
            email="np@example.com",
            company="Legacy Company",
        )
        return ChangeRequest.objects.create(
            cr_id=f"CR-NP-{suffix}",
            application="BUSINESS EXCELLENCE",
            change_type="New Profile",
            new_profile=profile,
            change_reason="Initial reason",
            change_description="Initial description",
            originator_company="OrigCo",
            originator_site="OrigSite",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )

    def _create_profile_modification_request(self, suffix: str = "001", change_type="Profile Modification") -> ChangeRequest:
        delegatee = UserProfile.objects.create(
            username=f"delegatee{suffix}",
            first_name="Delegatee",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        profile_change = ProfileChange.objects.create(
            user=delegatee,
            current_user_id=f"current-{suffix}",
            ec_number=f"EC-{suffix}",
            application="BUSINESS EXCELLENCE",
            roles_to_action="",
            roles_actions="",
            change_date=timezone.now(),
            changed_by=self.user,
            status='PENDING'
        )
        return ChangeRequest.objects.create(
            cr_id=f"CR-PM-{suffix}",
            application="BUSINESS EXCELLENCE",
            change_type=change_type,
            profile_change=profile_change,
            change_reason="Initial reason",
            change_description="Initial description",
            originator_company="OrigCo",
            originator_site="OrigSite",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )

    def _create_profile_deactivation_request(self, suffix: str = "001") -> ChangeRequest:
        target = UserProfile.objects.create(
            username=f"deactivate{suffix}",
            first_name="Deactivate",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        profile_deactivation = ProfileDeactivation.objects.create(
            user=target,
            application="BUSINESS EXCELLENCE",
            deactivation_date=timezone.now(),
            deactivated_by=self.user
        )
        return ChangeRequest.objects.create(
            cr_id=f"CR-PD-{suffix}",
            application="BUSINESS EXCELLENCE",
            change_type="Profile Deactivation",
            profile_deactivation=profile_deactivation,
            change_reason="Initial reason",
            change_description="Initial description",
            originator_company="OrigCo",
            originator_site="OrigSite",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )

    # ------------------------------------------------------------------
    # Update flow tests
    # ------------------------------------------------------------------

    def test_update_new_profile_cr_updates_core_fields(self):
        company_cc = CostCenter.objects.create(id="CC200", code="CC200", name="Company HQ")
        cr = self._create_new_profile_request("010")
        data = {
            'cr_id': cr.cr_id,
            'change_reason': 'Updated reason',
            'change_description': 'Updated description',
            'originator_company': 'UpdatedCo',
            'originator_site': 'UpdatedSite',
            'date_resolution_required': '2025-01-10',
            'firstname': 'Updated',
            'lastname': 'Person',
            'username': 'updateduser',
            'email': 'updated@example.com',
            'np_ec_number': 'EC123',
            'np_company': company_cc.id,
            'np_training_date': '2025-01-15',
            'np_training_confirmation_link': 'https://example.com/evidence',
            'np_training_confirmation_notes': 'Provided during audit',
            'np_job_title': '',
            'roles_to_action': 'Assign base role'
        }

        ChangeRequestService.update_new_profile_cr(cr, data, files=None, selected_role_ids=[])
        cr.refresh_from_db()

        self.assertEqual(cr.change_reason, 'Updated reason')
        self.assertEqual(cr.change_description, 'Updated description')
        self.assertEqual(cr.new_profile.first_name, 'Updated')
        self.assertEqual(cr.new_profile.company, company_cc.name)
        self.assertEqual(cr.new_profile.training_confirmation_link, 'https://example.com/evidence')

    def test_update_new_profile_cr_invalid_training_date_raises(self):
        cr = self._create_new_profile_request("011")
        data = {
            'cr_id': cr.cr_id,
            'change_reason': 'Reason',
            'change_description': 'Description',
            'originator_company': 'Company',
            'originator_site': 'Site',
            'date_resolution_required': '2025-02-10',
            'firstname': 'Updated',
            'lastname': 'Person',
            'username': 'updateduser',
            'email': 'updated@example.com',
            'np_ec_number': 'EC123',
            'np_company': self.cost_center.id,
            'np_training_date': 'invalid-date'
        }

        with self.assertRaises(ValidationError):
            ChangeRequestService.update_new_profile_cr(cr, data)

    def test_update_profile_modification_cr_permanent_paths(self):
        cr = self._create_profile_modification_request("020")
        data = {
            'cr_id': cr.cr_id,
            'change_reason': 'Need changes',
            'change_description': 'Assign/remove roles',
            'originator_company': 'Company',
            'originator_site': 'Site',
            'date_resolution_required': '2025-03-01',
            'application': 'BUSINESS EXCELLENCE',
            'mod_include_assign': 'assign',
            'mod_roles_to_assign': 'Grant access to BE',
            'mod_reason_assign': 'New duties',
            'mod_include_remove': 'remove',
            'mod_roles_to_remove': 'Remove SAP access',
            'mod_reason_remove': 'No longer needed',
        }

        ChangeRequestService.update_profile_modification_cr(cr, data)
        cr.refresh_from_db()

        self.assertIn("Grant access", cr.profile_change.roles_to_assign_notes)
        self.assertIn("Remove SAP", cr.profile_change.roles_to_remove_notes)
        self.assertEqual(cr.change_type, "Profile Modification")

    def test_update_profile_modification_cr_delegation_paths(self):
        application = Application.objects.create(name="BUSINESS EXCELLENCE")
        role = Roles.objects.create(
            role="BE_USER",
            name="BE User",
            description="Business Excellence User",
            application="BUSINESS EXCELLENCE",
            app_id=application
        )
        cr = self._create_profile_modification_request("021", change_type="Temporary Role Delegation")
        data = {
            'cr_id': cr.cr_id,
            'change_reason': 'Delegate temporarily',
            'change_description': 'User on leave',
            'originator_company': 'Company',
            'originator_site': 'Site',
            'date_resolution_required': '2025-03-10',
            'change_type': 'TEMPORARY_DELEGATION',
            'roles_to_action': 'TEMPORARY_DELEGATION',
            'delegation_start_date': '2025-03-15T08:00',
            'delegation_end_date': '2025-03-20T17:00',
            'delegation_reason': 'Leave cover',
        }

        ChangeRequestService.update_profile_modification_cr(cr, data, selected_role_ids=[role.id])
        cr.refresh_from_db()

        assigned_roles = list(cr.profile_change.role_to_assign.all())
        self.assertEqual(len(assigned_roles), 1)
        delegation_data = json.loads(cr.profile_change.roles_actions)
        self.assertEqual(delegation_data['reason'], 'Leave cover')
        self.assertEqual(cr.change_type, "Temporary Role Delegation")

    def test_update_profile_deactivation_cr_updates_dates(self):
        cr = self._create_profile_deactivation_request("030")
        data = {
            'cr_id': cr.cr_id,
            'change_reason': 'Update deactivation',
            'change_description': 'Adjust dates',
            'originator_company': 'Company',
            'originator_site': 'Site',
            'date_resolution_required': '2025-04-01',
            'application': 'BUSINESS EXCELLENCE',
            'deactivation_effective_start': '2025-04-05T09:00',
            'deactivation_reactivation_date': '2025-04-10T17:00',
            'deactivation_reason': 'Contract end'
        }

        ChangeRequestService.update_profile_deactivation_cr(cr, data)
        cr.refresh_from_db()

        self.assertIsNotNone(cr.profile_deactivation.effective_start_date)
        self.assertEqual(cr.profile_deactivation.deactivation_reason, 'Contract end')


class ApprovalServiceTestCase(TestCase):
    """Test cases for ApprovalService"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.new_profile = NewProfile.objects.create(
            username="newuser",
            first_name="New",
            last_name="User",
            email="new@example.com"
        )
        
        self.change_request = ChangeRequest.objects.create(
            cr_id="CR-TEST-001",
            change_type="New Profile",
            new_profile=self.new_profile,
            change_reason="Test reason",
            change_description="Test description",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
    
    def test_get_approval_status_pending(self):
        """Test getting approval status for pending CR"""
        status = ApprovalService.get_approval_status(self.change_request)
        
        self.assertIn('cr_approvals', status)
        self.assertIn('section_head_awaiting_action', status)
        self.assertIn('it_section_head_awaiting_action', status)
        self.assertTrue(status['section_head_awaiting_action'])
        self.assertTrue(status['it_section_head_awaiting_action'])
    
    def test_get_user_permissions(self):
        """Test getting user permissions for CR"""
        permissions = ApprovalService.get_user_permissions(self.user, self.change_request)
        
        self.assertIn('section_head_allowed', permissions)
        self.assertIn('it_section_head_allowed', permissions)
        self.assertIn('can_delete', permissions)
        self.assertIn('can_edit', permissions)
        
        # Creator should have delete/edit permissions
        self.assertTrue(permissions['can_delete'])
        self.assertTrue(permissions['can_edit'])


class ApprovalWorkflowTestCase(TestCase):
    """Test cases for ApprovalWorkflow"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.new_profile = NewProfile.objects.create(
            username="newuser",
            first_name="New",
            last_name="User"
        )
        
        self.change_request = ChangeRequest.objects.create(
            cr_id="CR-TEST-002",
            change_type="New Profile",
            new_profile=self.new_profile,
            change_reason="Test",
            change_description="Test",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
    
    def test_get_current_step_pending(self):
        """Test getting current step for pending CR"""
        step = ApprovalWorkflow.get_current_step(self.change_request)
        self.assertEqual(step, 'section_head')
    
    def test_workflow_steps_defined(self):
        """Test that workflow steps are properly defined"""
        self.assertEqual(ApprovalWorkflow.WORKFLOW_STEPS, ['section_head', 'it_section_head'])


class CRTypeHandlerTestCase(TestCase):
    """Test cases for CR type handlers"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.new_profile = NewProfile.objects.create(
            username="newuser",
            first_name="New",
            last_name="User",
            email="new@example.com",
            designation=self.designation
        )
        
        self.change_request = ChangeRequest.objects.create(
            cr_id="CR-TEST-003",
            change_type="New Profile",
            new_profile=self.new_profile,
            change_reason="Test",
            change_description="Test",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
    
    def test_get_handler_new_profile(self):
        """Test getting handler for new profile CR"""
        handler = CRTypeHandler.get_handler('New Profile')
        self.assertIsInstance(handler, NewProfileHandler)
    
    def test_get_handler_profile_modification(self):
        """Test getting handler for profile modification CR"""
        handler = CRTypeHandler.get_handler('Profile Modification')
        self.assertIsInstance(handler, ProfileModificationHandler)
    
    def test_get_handler_profile_deactivation(self):
        """Test getting handler for profile deactivation CR"""
        handler = CRTypeHandler.get_handler('Profile Deactivation')
        self.assertIsInstance(handler, ProfileDeactivationHandler)
    
    def test_get_handler_invalid_type(self):
        """Test getting handler for invalid CR type"""
        with self.assertRaises(ValueError):
            CRTypeHandler.get_handler('Invalid Type')
    
    def test_new_profile_handler_get_profile_data(self):
        """Test NewProfileHandler.get_profile_data()"""
        handler = NewProfileHandler()
        profile_data = handler.get_profile_data(self.change_request)
        
        self.assertIn('username', profile_data)
        self.assertIn('first_name', profile_data)
        self.assertIn('email', profile_data)
        self.assertEqual(profile_data['username'], 'newuser')


class ContextBuilderTestCase(TestCase):
    """Test cases for ContextBuilder"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.new_profile = NewProfile.objects.create(
            username="newuser",
            first_name="New",
            last_name="User"
        )
        
        self.change_request = ChangeRequest.objects.create(
            cr_id="CR-TEST-004",
            change_type="New Profile",
            new_profile=self.new_profile,
            change_reason="Test",
            change_description="Test",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
    
    def test_get_base_template_context(self):
        """Test building base template context"""
        context = ContextBuilder.get_base_template_context(self.user, self.change_request)
        
        self.assertIn('user_title', context)
        self.assertIn('user_groups', context)
        self.assertIn('change_request', context)
        self.assertEqual(context['change_request'], self.change_request)
    
    def test_build_cr_context(self):
        """Test building CR context"""
        profile_data = {'username': 'test'}
        cr_context = ContextBuilder.build_cr_context(self.change_request, profile_data)
        
        self.assertIn('cr_id', cr_context)
        self.assertIn('change_reason', cr_context)
        self.assertIn('change_description', cr_context)
        self.assertIn('user', cr_context)
        self.assertEqual(cr_context['cr_id'], 'CR-TEST-004')


class NotificationServiceTestCase(TestCase):
    """Test cases for NotificationService"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.user = UserProfile.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.new_profile = NewProfile.objects.create(
            username="newuser",
            first_name="New",
            last_name="User"
        )
        
        self.change_request = ChangeRequest.objects.create(
            cr_id="CR-TEST-005",
            change_type="New Profile",
            new_profile=self.new_profile,
            change_reason="Test",
            change_description="Test",
            created_by=self.user,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
    
    def test_get_cr_type_url(self):
        """Test getting CR type URL segment"""
        url = NotificationService._get_cr_type_url(self.change_request)
        self.assertEqual(url, 'new_profile_request')
    
    @patch('it.change_requests.services.notification_service.ms_exhange_reset_password_html')
    @patch('it.change_requests.services.notification_service.NotificationService._get_section_head_approver')
    def test_send_creation_notification(self, mock_get_approver, mock_send_email):
        """Test sending creation notification"""
        mock_approver = Mock()
        mock_approver.email = 'approver@example.com'
        mock_get_approver.return_value = mock_approver
        
        result = NotificationService.send_creation_notification(self.change_request)
        
        # Should succeed if approver found
        self.assertTrue(result)
        mock_send_email.assert_called_once()


class DelegationApprovalTestCase(TestCase):
    """Test cases for delegation approval and activation"""
    
    def setUp(self):
        """Set up test data for delegation tests"""
        from it.users.models import RoleDelegation, DelegationNotification
        from datetime import datetime, timedelta
        
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        self.app = Application.objects.create(name="change_requests")
        
        # Create roles
        self.test_role = Roles.objects.create(
            role="test_role",
            name="Test Role",
            app_id=self.app.id
        )
        
        # Create delegator
        self.delegator = UserProfile.objects.create(
            username="delegator",
            first_name="Delegator",
            last_name="User",
            email="delegator@example.com",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        # Create delegatee
        self.delegatee = UserProfile.objects.create(
            username="delegatee",
            first_name="Delegatee",
            last_name="User",
            email="delegatee@example.com",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        # Create IT section head
        self.it_user = UserProfile.objects.create(
            username="it_head",
            first_name="IT",
            last_name="Head",
            email="it@example.com",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.it_role = Roles.objects.create(
            role="it_section_head",
            name="IT Section Head",
            app_id=self.app.id
        )
        self.it_user.roles.add(self.it_role)
        
        # Create delegation metadata
        now = timezone.now()
        self.delegation_metadata = {
            'delegator_id': self.delegator.id,
            'start_date': (now + timedelta(hours=1)).isoformat(),
            'end_date': (now + timedelta(days=7)).isoformat(),
            'reason': 'Going on leave'
        }
    
    def test_apply_delegation_creates_approved_status(self):
        """Test that applying delegation creates record with APPROVED status"""
        from it.users.models import RoleDelegation
        import json
        
        # Create profile change for delegation
        profile_change = ProfileChange.objects.create(
            user=self.delegatee,
            changed_by=self.delegator,
            roles_to_action="TEMPORARY_DELEGATION",
            roles_actions=json.dumps(self.delegation_metadata)
        )
        profile_change.role_to_assign.add(self.test_role)
        
        # Create change request
        cr = ChangeRequest.objects.create(
            cr_id="CR-DEL-001",
            change_type="Temporary Role Delegation",
            profile_change=profile_change,
            change_reason="Test delegation",
            change_description="Testing delegation approval",
            created_by=self.delegator,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center,
            application="BUSINESS EXCELLENCE"
        )
        
        # Apply delegation
        from it.change_requests.services.approval_service import ApprovalApplicationService
        success, message = ApprovalApplicationService.apply_delegation(cr)
        
        # Verify success
        self.assertTrue(success)
        
        # Verify delegation was created with APPROVED status
        delegation = RoleDelegation.objects.filter(
            delegator=self.delegator,
            delegatee=self.delegatee
        ).first()
        
        self.assertIsNotNone(delegation)
        self.assertEqual(delegation.status, 'APPROVED')
        self.assertEqual(delegation.reason, 'Going on leave')
        
        # Verify roles were assigned
        self.assertIn(self.test_role, delegation.roles.all())
    
    def test_apply_delegation_validates_metadata(self):
        """Test that applying delegation validates metadata properly"""
        import json
        
        # Create profile change with invalid metadata (missing required fields)
        invalid_metadata = {
            'delegator_id': self.delegator.id,
            'start_date': timezone.now().isoformat()
            # Missing end_date and reason
        }
        
        profile_change = ProfileChange.objects.create(
            user=self.delegatee,
            changed_by=self.delegator,
            roles_to_action="TEMPORARY_DELEGATION",
            roles_actions=json.dumps(invalid_metadata)
        )
        
        cr = ChangeRequest.objects.create(
            cr_id="CR-DEL-002",
            change_type="Temporary Role Delegation",
            profile_change=profile_change,
            change_reason="Test",
            change_description="Test",
            created_by=self.delegator,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Apply delegation should fail
        from it.change_requests.services.approval_service import ApprovalApplicationService
        success, message = ApprovalApplicationService.apply_delegation(cr)
        
        self.assertFalse(success)
        self.assertIn('Missing required delegation fields', message)
    
    def test_apply_delegation_validates_dates(self):
        """Test that applying delegation validates date logic"""
        import json
        
        # Create metadata with end_date before start_date
        now = timezone.now()
        invalid_metadata = {
            'delegator_id': self.delegator.id,
            'start_date': (now + timedelta(days=7)).isoformat(),
            'end_date': (now + timedelta(days=1)).isoformat(),  # Before start!
            'reason': 'Test'
        }
        
        profile_change = ProfileChange.objects.create(
            user=self.delegatee,
            changed_by=self.delegator,
            roles_to_action="TEMPORARY_DELEGATION",
            roles_actions=json.dumps(invalid_metadata)
        )
        
        cr = ChangeRequest.objects.create(
            cr_id="CR-DEL-003",
            change_type="Temporary Role Delegation",
            profile_change=profile_change,
            change_reason="Test",
            change_description="Test",
            created_by=self.delegator,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Apply delegation should fail
        from it.change_requests.services.approval_service import ApprovalApplicationService
        success, message = ApprovalApplicationService.apply_delegation(cr)
        
        self.assertFalse(success)
        self.assertIn('End date must be after start date', message)
    
    def test_status_transition_to_implemented(self):
        """Test that applying CR sets status to IMPLEMENTED"""
        import json
        
        # Create profile change for delegation
        profile_change = ProfileChange.objects.create(
            user=self.delegatee,
            changed_by=self.delegator,
            roles_to_action="TEMPORARY_DELEGATION",
            roles_actions=json.dumps(self.delegation_metadata)
        )
        profile_change.role_to_assign.add(self.test_role)
        
        # Create change request
        cr = ChangeRequest.objects.create(
            cr_id="CR-DEL-004",
            change_type="Temporary Role Delegation",
            profile_change=profile_change,
            change_reason="Test delegation",
            change_description="Testing status transition",
            created_by=self.delegator,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center,
            application="BUSINESS EXCELLENCE",
            status='APPROVED'  # Already approved by section head
        )
        
        # Create section head approval
        sh_role = Roles.objects.create(
            role="section_head",
            name="Section Head",
            app_id=self.app.id
        )
        CRApproval.objects.create(
            cr_id=cr,
            approver=self.delegator,
            approver_role=sh_role,
            approval_status=True,
            approval_date=timezone.now()
        )
        
        # Apply CR
        from it.change_requests.services.approval_service import ApprovalService
        success, message = ApprovalService.apply_cr(cr, self.it_user, "Delegation approved")
        
        # Verify status is IMPLEMENTED
        cr.refresh_from_db()
        self.assertTrue(success)
        self.assertEqual(cr.status, 'IMPLEMENTED')


class DelegationActivationCommandTestCase(TestCase):
    """Test cases for the delegation activation management command"""
    
    def setUp(self):
        """Set up test data"""
        from datetime import timedelta
        
        self.region = Regions.objects.create(region="Test Region", code="TR")
        self.cost_center = CostCenter.objects.create(name="Test Cost Center")
        self.designation = Designations.objects.create(description="Test Designation")
        
        self.delegator = UserProfile.objects.create(
            username="delegator",
            first_name="Delegator",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
        
        self.delegatee = UserProfile.objects.create(
            username="delegatee",
            first_name="Delegatee",
            last_name="User",
            region=self.region,
            cost_center=self.cost_center,
            designation=self.designation
        )
    
    def test_activate_delegations_ready(self):
        """Test that delegations are activated when start_date arrives"""
        from it.users.models import RoleDelegation
        from datetime import timedelta
        from django.core.management import call_command
        from io import StringIO
        
        now = timezone.now()
        
        # Create delegation that should be activated
        delegation = RoleDelegation.objects.create(
            delegator=self.delegator,
            delegatee=self.delegatee,
            start_date=now - timedelta(hours=1),  # Already started
            end_date=now + timedelta(days=7),
            reason='Test',
            status='APPROVED'
        )
        
        # Run command
        out = StringIO()
        call_command('activate_delegations', stdout=out)
        
        # Verify delegation was activated
        delegation.refresh_from_db()
        self.assertEqual(delegation.status, 'ACTIVE')
        
        # Verify output
        output = out.getvalue()
        self.assertIn('Successfully activated', output)
    
    def test_expire_delegations_past_end_date(self):
        """Test that active delegations are expired when end_date passes"""
        from it.users.models import RoleDelegation
        from datetime import timedelta
        from django.core.management import call_command
        from io import StringIO
        
        now = timezone.now()
        
        # Create delegation that should be expired
        delegation = RoleDelegation.objects.create(
            delegator=self.delegator,
            delegatee=self.delegatee,
            start_date=now - timedelta(days=7),
            end_date=now - timedelta(hours=1),  # Already ended
            reason='Test',
            status='ACTIVE'
        )
        
        # Run command
        out = StringIO()
        call_command('activate_delegations', stdout=out)
        
        # Verify delegation was expired
        delegation.refresh_from_db()
        self.assertEqual(delegation.status, 'EXPIRED')
        
        # Verify output
        output = out.getvalue()
        self.assertIn('Successfully expired', output)
    
    def test_dry_run_mode(self):
        """Test that dry-run mode doesn't make changes"""
        from it.users.models import RoleDelegation
        from datetime import timedelta
        from django.core.management import call_command
        from io import StringIO
        
        now = timezone.now()
        
        # Create delegation that should be activated
        delegation = RoleDelegation.objects.create(
            delegator=self.delegator,
            delegatee=self.delegatee,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=7),
            reason='Test',
            status='APPROVED'
        )
        
        # Run command in dry-run mode
        out = StringIO()
        call_command('activate_delegations', '--dry-run', stdout=out)
        
        # Verify delegation was NOT activated
        delegation.refresh_from_db()
        self.assertEqual(delegation.status, 'APPROVED')
        
        # Verify dry-run message in output
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('Would activate', output)
