"""
Unit tests for change_requests views and helper functions
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from it.change_requests.models import ChangeRequest, NewProfile, CRApproval
from it.change_requests.views import (
    validate_change_request_data, validate_new_profile_data, sanitize_input,
    check_change_request_permissions, get_change_requests_optimized,
    apply_filters, get_cached_user_data, prepare_change_request_data,
    get_approval_status
)
from it.users.models import UserProfile, Regions, CostCenter, Designations, Application, Roles


class ValidationFunctionsTestCase(TestCase):
    """Test cases for validation functions"""
    
    def test_validate_change_request_data_valid(self):
        """Test validation with valid data"""
        valid_data = {
            'change_reason': 'Valid reason',
            'change_description': 'Valid description'
        }
        errors = validate_change_request_data(valid_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_change_request_data_missing_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {
            'change_reason': '',
            'change_description': ''
        }
        errors = validate_change_request_data(invalid_data)
        self.assertEqual(len(errors), 2)
        self.assertIn("Change reason is required", errors)
        self.assertIn("Change description is required", errors)
    
    def test_validate_change_request_data_too_long(self):
        """Test validation with fields that are too long"""
        long_data = {
            'change_reason': 'x' * 501,  # Exceeds MAX_REASON_LENGTH
            'change_description': 'Valid description'
        }
        errors = validate_change_request_data(long_data)
        self.assertEqual(len(errors), 1)
        self.assertIn("Change reason too long", errors[0])
    
    def test_validate_new_profile_data_valid(self):
        """Test validation with valid profile data"""
        valid_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com'
        }
        errors = validate_new_profile_data(valid_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_new_profile_data_missing_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {
            'username': '',
            'first_name': '',
            'last_name': '',
            'email': ''
        }
        errors = validate_new_profile_data(invalid_data)
        self.assertEqual(len(errors), 4)
    
    @patch('it.change_requests.views.NewProfile.objects.filter')
    def test_validate_new_profile_data_duplicate_username(self, mock_filter):
        """Test validation with duplicate username"""
        mock_filter.return_value.exists.return_value = True
        
        data = {
            'username': 'existinguser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com'
        }
        errors = validate_new_profile_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("Username already exists", errors[0])


class SanitizationFunctionsTestCase(TestCase):
    """Test cases for input sanitization functions"""
    
    def test_sanitize_input_xss_prevention(self):
        """Test XSS prevention in input sanitization"""
        malicious_input = {
            'change_reason': '<script>alert("XSS")</script>',
            'change_description': 'Normal description',
            'username': 'user<script>alert("hack")</script>'
        }
        
        sanitized = sanitize_input(malicious_input)
        
        # Check that script tags are escaped
        self.assertIn('&lt;script&gt;', sanitized['change_reason'])
        self.assertIn('&lt;script&gt;', sanitized['username'])
        self.assertEqual(sanitized['change_description'], 'Normal description')
    
    def test_sanitize_input_whitespace_trimming(self):
        """Test whitespace trimming in input sanitization"""
        input_with_whitespace = {
            'change_reason': '  Reason with spaces  ',
            'change_description': '\tDescription with tabs\t'
        }
        
        sanitized = sanitize_input(input_with_whitespace)
        
        self.assertEqual(sanitized['change_reason'], 'Reason with spaces')
        self.assertEqual(sanitized['change_description'], 'Description with tabs')
    
    def test_sanitize_input_non_string_values(self):
        """Test that non-string values are preserved"""
        mixed_input = {
            'change_reason': 'String value',
            'numeric_value': 123,
            'boolean_value': True,
            'list_value': [1, 2, 3]
        }
        
        sanitized = sanitize_input(mixed_input)
        
        self.assertEqual(sanitized['change_reason'], 'String value')
        self.assertEqual(sanitized['numeric_value'], 123)
        self.assertEqual(sanitized['boolean_value'], True)
        self.assertEqual(sanitized['list_value'], [1, 2, 3])


class PermissionFunctionsTestCase(TestCase):
    """Test cases for permission checking functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        self.designation = Designations.objects.create(description='Test Designation')
        
        self.change_request = ChangeRequest.objects.create(
            cr_id='CR001',
            change_type='NEW_PROFILE',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
    
    def test_check_change_request_permissions_creator(self):
        """Test permission check for creator"""
        has_permission, message = check_change_request_permissions(self.user_profile, self.change_request)
        self.assertTrue(has_permission)
        self.assertEqual(message, "User is the creator")
    
    def test_check_change_request_permissions_non_creator(self):
        """Test permission check for non-creator"""
        other_user = UserProfile.objects.create(
            username='otheruser',
            first_name='Other',
            last_name='User',
            email='other@example.com'
        )
        
        has_permission, message = check_change_request_permissions(other_user, self.change_request)
        self.assertFalse(has_permission)
        self.assertEqual(message, "Insufficient permissions")
    
    def test_check_change_request_permissions_nonexistent(self):
        """Test permission check for nonexistent change request"""
        has_permission, message = check_change_request_permissions(self.user_profile, None)
        self.assertFalse(has_permission)
        self.assertEqual(message, "Change request not found")


class HelperFunctionsTestCase(TestCase):
    """Test cases for helper functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        self.designation = Designations.objects.create(description='Test Designation')
        
        self.new_profile = NewProfile.objects.create(
            username='newuser',
            first_name='New',
            last_name='User',
            email='newuser@example.com',
            region=self.region,
            cost_center=self.cost_center
        )
        
        self.change_request = ChangeRequest.objects.create(
            cr_id='CR001',
            change_type='NEW_PROFILE',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center,
            new_profile=self.new_profile
        )
    
    def test_prepare_change_request_data(self):
        """Test change request data preparation"""
        data = prepare_change_request_data(self.change_request)
        
        self.assertEqual(data['cr_id'], 'CR001')
        self.assertEqual(data['change_type'], 'NEW_PROFILE')
        self.assertEqual(data['change_reason'], 'Test reason')
        self.assertEqual(data['change_description'], 'Test description')
        self.assertEqual(data['created_by'], self.user_profile)
        self.assertFalse(data['is_deleted'])
        self.assertIn('new_profile', data)
        self.assertEqual(data['new_profile']['username'], 'newuser')
    
    def test_get_approval_status_no_approvals(self):
        """Test approval status with no approvals"""
        status = get_approval_status(self.change_request)
        self.assertEqual(status, 'Pending SH')
    
    def test_get_approval_status_section_head_approved(self):
        """Test approval status with section head approval"""
        # Mock the CRApproval query
        with patch('it.change_requests.views.CRApproval.objects.filter') as mock_filter:
            mock_approval = MagicMock()
            mock_approval.approval_status = True
            mock_filter.return_value.first.return_value = mock_approval
            
            status = get_approval_status(self.change_request)
            self.assertEqual(status, 'Pending IT')
    
    def test_get_approval_status_complete(self):
        """Test approval status when complete"""
        # Mock the CRApproval query for complete status
        with patch('it.change_requests.views.CRApproval.objects.filter') as mock_filter:
            mock_approval = MagicMock()
            mock_approval.approval_status = True
            
            # First call returns section head approval, second call returns IT approval
            mock_filter.return_value.first.side_effect = [mock_approval, mock_approval]
            
            status = get_approval_status(self.change_request)
            self.assertEqual(status, 'Complete')


class QueryOptimizationTestCase(TestCase):
    """Test cases for query optimization functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        self.designation = Designations.objects.create(description='Test Designation')
    
    @patch('it.change_requests.views.ChangeRequest.objects')
    def test_get_change_requests_optimized(self, mock_objects):
        """Test optimized query function"""
        # Mock the queryset chain
        mock_queryset = MagicMock()
        mock_objects.select_related.return_value.prefetch_related.return_value.filter.return_value = mock_queryset
        
        result = get_change_requests_optimized(self.user_profile)
        
        # Verify that select_related and prefetch_related were called
        mock_objects.select_related.assert_called_once()
        mock_queryset.prefetch_related.assert_called_once()
        mock_queryset.filter.assert_called_once()
    
    def test_apply_filters(self):
        """Test filter application"""
        # Mock queryset
        mock_queryset = MagicMock()
        
        filters = {
            'change_type': 'NEW_PROFILE',
            'application': 'Test App',
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        }
        
        result = apply_filters(mock_queryset, filters)
        
        # Verify that filter was called for each filter
        self.assertEqual(mock_queryset.filter.call_count, 4)


class CachingTestCase(TestCase):
    """Test cases for caching functions"""
    
    @patch('it.change_requests.views.cache')
    @patch('it.change_requests.views.UserProfile.objects')
    @patch('it.change_requests.views.Application.objects')
    @patch('it.change_requests.views.Roles.objects')
    def test_get_cached_user_data_cache_hit(self, mock_roles, mock_apps, mock_users, mock_cache):
        """Test cached user data retrieval when cache hit"""
        # Mock cache hit
        cached_data = {
            "applications": [{'id': 1, 'name': 'test_app'}],
            "userData": {'test_app': []},
            "active_roles": {}
        }
        mock_cache.get.return_value = cached_data
        
        result = get_cached_user_data('testuser')
        
        self.assertEqual(result, cached_data)
        mock_cache.get.assert_called_once_with('user_data_testuser')
        # Should not query database on cache hit
        mock_users.filter.assert_not_called()
    
    @patch('it.change_requests.views.cache')
    @patch('it.change_requests.views.UserProfile.objects')
    @patch('it.change_requests.views.Application.objects')
    @patch('it.change_requests.views.Roles.objects')
    def test_get_cached_user_data_cache_miss(self, mock_roles, mock_apps, mock_users, mock_cache):
        """Test cached user data retrieval when cache miss"""
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock user data
        mock_user = MagicMock()
        mock_user.roles.all.return_value = []
        mock_users.filter.return_value.first.return_value = mock_user
        
        # Mock applications and roles
        mock_apps.all.return_value = []
        mock_roles.filter.return_value.all.return_value = []
        
        result = get_cached_user_data('testuser')
        
        # Should query database on cache miss
        mock_users.filter.assert_called_once_with(username='testuser')
        # Should set cache
        mock_cache.set.assert_called_once()
    
    @patch('it.change_requests.views.cache')
    @patch('it.change_requests.views.UserProfile.objects')
    def test_get_cached_user_data_user_not_found(self, mock_users, mock_cache):
        """Test cached user data when user not found"""
        # Mock cache miss and user not found
        mock_cache.get.return_value = None
        mock_users.filter.return_value.first.return_value = None
        
        result = get_cached_user_data('nonexistentuser')
        
        self.assertIsNone(result)
        mock_cache.set.assert_not_called()
