"""
Unit tests for change_requests models
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from it.change_requests.models import ChangeRequest, NewProfile, ProfileChange, ProfileDeactivation, CRApproval
from it.users.models import UserProfile, Regions, CostCenter, Designations, Sections, Districts, Roles, Application


class ChangeRequestModelTestCase(TestCase):
    """Test cases for ChangeRequest model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test user profile
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
        self.designation = Designations.objects.create(description='Test Designation')
        
        # Create test change request
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

    def test_change_request_creation(self):
        """Test change request creation"""
        self.assertEqual(self.change_request.cr_id, 'CR001')
        self.assertEqual(self.change_request.change_type, 'NEW_PROFILE')
        self.assertEqual(self.change_request.change_reason, 'Test reason')
        self.assertEqual(self.change_request.change_description, 'Test description')
        self.assertEqual(self.change_request.created_by, self.user_profile)
        self.assertFalse(self.change_request.is_deleted)

    def test_soft_delete_functionality(self):
        """Test soft delete functionality"""
        # Test soft delete
        self.change_request.soft_delete(self.user_profile)
        
        self.assertTrue(self.change_request.is_deleted)
        self.assertIsNotNone(self.change_request.deleted_at)
        self.assertEqual(self.change_request.deleted_by, self.user_profile)
        
        # Test restore
        self.change_request.restore()
        
        self.assertFalse(self.change_request.is_deleted)
        self.assertIsNone(self.change_request.deleted_at)
        self.assertIsNone(self.change_request.deleted_by)

    def test_change_request_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.change_request), 'CR001')

    def test_change_request_meta_ordering(self):
        """Test default ordering"""
        # Create another change request
        change_request2 = ChangeRequest.objects.create(
            cr_id='CR002',
            change_type='PROFILE_MODIFICATION',
            change_reason='Test reason 2',
            change_description='Test description 2',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Test ordering (should be by created_at descending)
        change_requests = ChangeRequest.objects.all()
        self.assertEqual(change_requests[0], change_request2)  # Most recent first
        self.assertEqual(change_requests[1], self.change_request)


class NewProfileModelTestCase(TestCase):
    """Test cases for NewProfile model"""
    
    def setUp(self):
        """Set up test data"""
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        self.designation = Designations.objects.create(description='Test Designation')
        self.section = Sections.objects.create(code='SEC001', name='Test Section')
        self.district = Districts.objects.create(name='Test District')
        
        self.new_profile = NewProfile.objects.create(
            username='newuser',
            first_name='New',
            last_name='User',
            email='newuser@example.com',
            designation=self.designation,
            section=self.section,
            cost_center=self.cost_center,
            district=self.district,
            region=self.region
        )

    def test_new_profile_creation(self):
        """Test new profile creation"""
        self.assertEqual(self.new_profile.username, 'newuser')
        self.assertEqual(self.new_profile.first_name, 'New')
        self.assertEqual(self.new_profile.last_name, 'User')
        self.assertEqual(self.new_profile.email, 'newuser@example.com')
        self.assertEqual(self.new_profile.designation, self.designation)
        self.assertEqual(self.new_profile.region, self.region)

    def test_new_profile_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.new_profile), 'New User')
        
        # Test with only username
        profile_username_only = NewProfile.objects.create(username='usernameonly')
        self.assertEqual(str(profile_username_only), 'usernameonly')


class CRApprovalModelTestCase(TestCase):
    """Test cases for CRApproval model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='approver',
            email='approver@example.com',
            password='testpass123'
        )
        
        self.approver = UserProfile.objects.create(
            user=self.user,
            username='approver',
            first_name='Approver',
            last_name='User',
            email='approver@example.com'
        )
        
        # Create test region and cost center
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        self.designation = Designations.objects.create(description='Test Designation')
        
        # Create test change request
        self.change_request = ChangeRequest.objects.create(
            cr_id='CR001',
            change_type='NEW_PROFILE',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.approver,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Create test application and role
        self.application = Application.objects.create(name='Test App', fullname='Test Application')
        self.role = Roles.objects.create(
            app_id=self.application,
            role='section_head',
            description='Section Head Role'
        )
        
        # Create test approval
        self.approval = CRApproval.objects.create(
            cr_id=self.change_request,
            approver=self.approver,
            approver_role=self.role,
            approval_status=True,
            comment='Approved for testing',
            approval_date=timezone.now()
        )

    def test_approval_creation(self):
        """Test approval creation"""
        self.assertEqual(self.approval.cr_id, self.change_request)
        self.assertEqual(self.approval.approver, self.approver)
        self.assertEqual(self.approval.approver_role, self.role)
        self.assertTrue(self.approval.approval_status)
        self.assertEqual(self.approval.comment, 'Approved for testing')
        self.assertIsNotNone(self.approval.approval_date)

    def test_approval_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.approval), 'CR001')


class ProfileChangeModelTestCase(TestCase):
    """Test cases for ProfileChange model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
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
        
        # Create test application and role
        self.application = Application.objects.create(name='Test App', fullname='Test Application')
        self.role = Roles.objects.create(
            app_id=self.application,
            role='test_role',
            description='Test Role'
        )
        
        # Create test profile change
        self.profile_change = ProfileChange.objects.create(
            user=self.user_profile,
            application='Test App',
            roles_to_action='Add role',
            roles_actions='Role added',
            change_date=timezone.now(),
            changed_by=self.user_profile
        )
        self.profile_change.role_to_assign.add(self.role)

    def test_profile_change_creation(self):
        """Test profile change creation"""
        self.assertEqual(self.profile_change.user, self.user_profile)
        self.assertEqual(self.profile_change.application, 'Test App')
        self.assertEqual(self.profile_change.roles_to_action, 'Add role')
        self.assertEqual(self.profile_change.roles_actions, 'Role added')
        self.assertEqual(self.profile_change.changed_by, self.user_profile)
        self.assertIn(self.role, self.profile_change.role_to_assign.all())

    def test_profile_change_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.profile_change), str(self.user_profile))


class ProfileDeactivationModelTestCase(TestCase):
    """Test cases for ProfileDeactivation model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
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
        
        # Create test profile deactivation
        self.profile_deactivation = ProfileDeactivation.objects.create(
            user=self.user_profile,
            application='Test App',
            deactivation_date=timezone.now(),
            deactivated_by=self.user_profile
        )

    def test_profile_deactivation_creation(self):
        """Test profile deactivation creation"""
        self.assertEqual(self.profile_deactivation.user, self.user_profile)
        self.assertEqual(self.profile_deactivation.application, 'Test App')
        self.assertEqual(self.profile_deactivation.deactivated_by, self.user_profile)
        self.assertIsNotNone(self.profile_deactivation.deactivation_date)

    def test_profile_deactivation_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.profile_deactivation), str(self.user_profile))
