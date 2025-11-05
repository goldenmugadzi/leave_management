"""
Unit tests for change_requests service layer

Tests the refactored service layer components including:
- ChangeRequestService
- ApprovalService
- NotificationService
- CRTypeHandlers
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
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
        self.region = Regions.objects.create(name="Test Region")
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


class ApprovalServiceTestCase(TestCase):
    """Test cases for ApprovalService"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(name="Test Region")
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
        self.region = Regions.objects.create(name="Test Region")
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
        self.region = Regions.objects.create(name="Test Region")
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
        self.region = Regions.objects.create(name="Test Region")
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
        self.region = Regions.objects.create(name="Test Region")
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

