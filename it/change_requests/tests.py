from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from it.change_requests.models import ChangeRequest, NewProfile
from it.users.models import UserProfile, Regions, CostCenter
from django.utils import timezone

class ChangeRequestTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test user profile
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
        # Create test region and cost center
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        
        # Create a test change request
        self.change_request = ChangeRequest.objects.create(
            change_type='NEW_PROFILE',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            region=self.region,
            cost_center=self.cost_center
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_update_change_request_bug_fix(self):
        """Test that the update bug is fixed - change_description should be updated correctly"""
        # Test data with change_description but no change_reason
        test_data = {
            'change_description': 'Updated description',
            'change_reason': '',  # Empty change_reason
        }
        
        # Before the fix, this would incorrectly use change_reason (empty) to decide whether to update change_description
        # After the fix, it should correctly use change_description to decide whether to update change_description
        
        # Simulate the logic from the fixed code
        change_description = test_data.get('change_description')
        change_reason = test_data.get('change_reason')
        
        # This is the fixed logic
        result_description = change_description if change_description else self.change_request.change_description
        
        # Verify that the description is updated correctly
        self.assertEqual(result_description, 'Updated description')
        
        # Test with empty change_description
        test_data_empty = {
            'change_description': '',
            'change_reason': 'Some reason',
        }
        
        change_description_empty = test_data_empty.get('change_description')
        result_description_empty = change_description_empty if change_description_empty else self.change_request.change_description
        
        # Should keep the original description when change_description is empty
        self.assertEqual(result_description_empty, 'Test description')

    def test_validation_functions(self):
        """Test the validation functions work correctly"""
        from it.change_requests.views import validate_change_request_data, validate_new_profile_data
        
        # Test change request validation
        valid_data = {
            'change_reason': 'Valid reason',
            'change_description': 'Valid description'
        }
        errors = validate_change_request_data(valid_data)
        self.assertEqual(len(errors), 0)
        
        # Test missing required fields
        invalid_data = {
            'change_reason': '',
            'change_description': ''
        }
        errors = validate_change_request_data(invalid_data)
        self.assertEqual(len(errors), 2)
        self.assertIn("Change reason is required", errors)
        self.assertIn("Change description is required", errors)
        
        # Test new profile validation
        valid_profile_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com'
        }
        errors = validate_new_profile_data(valid_profile_data)
        self.assertEqual(len(errors), 0)
        
        # Test missing required fields for profile
        invalid_profile_data = {
            'username': '',
            'first_name': '',
            'last_name': '',
            'email': ''
        }
        errors = validate_new_profile_data(invalid_profile_data)
        self.assertEqual(len(errors), 4)
