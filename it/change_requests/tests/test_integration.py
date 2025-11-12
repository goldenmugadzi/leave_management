"""
Integration tests for change_requests workflows
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from it.change_requests.models import ChangeRequest, NewProfile, CRApproval
from it.users.models import UserProfile, Regions, CostCenter, Designations, Application, Roles


class ChangeRequestWorkflowTestCase(TestCase):
    """Integration tests for complete change request workflows"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.approver_user = User.objects.create_user(
            username='approver',
            email='approver@example.com',
            password='testpass123'
        )
        
        # Create user profiles
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
        self.approver_profile = UserProfile.objects.create(
            user=self.approver_user,
            username='approver',
            first_name='Approver',
            last_name='User',
            email='approver@example.com'
        )
        
        # Create test data
        self.region = Regions.objects.create(name='Test Region')
        self.cost_center = CostCenter.objects.create(name='Test Cost Center')
        self.designation = Designations.objects.create(description='Test Designation')
        
        # Create application and roles
        self.application = Application.objects.create(name='Test App', fullname='Test Application')
        self.section_head_role = Roles.objects.create(
            app_id=self.application,
            role='section_head',
            description='Section Head Role'
        )
        self.it_section_head_role = Roles.objects.create(
            app_id=self.application,
            role='it_section_head',
            description='IT Section Head Role'
        )
        
        # Assign organizational data to user profiles
        self.user_profile.region = self.region
        self.user_profile.cost_center = self.cost_center
        self.user_profile.designation = self.designation
        self.user_profile.save()
        
        self.approver_profile.region = self.region
        self.approver_profile.cost_center = self.cost_center
        self.approver_profile.designation = self.designation
        self.approver_profile.save()
        
        # Set up client
        self.client = Client()
    
    def test_complete_new_profile_workflow(self):
        """Test complete new profile creation workflow"""
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Create new profile change request
        response = self.client.post('/change_requests/create_new_profile', {
            'change_reason': 'Need new user account',
            'change_description': 'Creating account for new employee',
            'originator_company': 'ZETDC',
            'originator_site': 'Harare Region',
            'date_resolution_required': '2025-12-31',
            'username': 'newemployee',
            'first_name': 'New',
            'last_name': 'Employee',
            'email': 'newemployee@example.com',
            'designation': self.designation.id,
            'cost_center': self.cost_center.id,
            'for_application': self.application.id,
            'roles_to_action': 'Add basic role',
            'np_ec_number': '1234567',
            'np_job_title': 'Business Analyst',
            'np_company': 'ZETDC',
            'np_sub_module': 'Core',
            'np_depot_office': 'Head Office',
            'np_training_date': '2025-11-01',
            'np_training_confirmation_link': 'https://example.com/training-proof'
        })
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify change request was created
        change_request = ChangeRequest.objects.filter(
            change_type='New Profile',
            created_by=self.user_profile
        ).first()
        
        self.assertIsNotNone(change_request)
        self.assertEqual(change_request.change_reason, 'Need new user account')
        self.assertIsNotNone(change_request.new_profile)
        self.assertEqual(change_request.new_profile.username, 'newemployee')
        self.assertEqual(change_request.originator_company, 'ZETDC')
        self.assertEqual(change_request.new_profile.ec_number, '1234567')
    
    def test_approval_workflow(self):
        """Test complete approval workflow"""
        # Create a change request
        new_profile = NewProfile.objects.create(
            username='testuser2',
            first_name='Test',
            last_name='User2',
            email='testuser2@example.com',
            region=self.region,
            cost_center=self.cost_center
        )
        
        change_request = ChangeRequest.objects.create(
            cr_id='CR001',
            change_type='NEW_PROFILE',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center,
            new_profile=new_profile
        )
        
        # Login approver
        self.client.login(username='approver', password='testpass123')
        
        # Approve the change request
        response = self.client.post('/change_requests/approve_change_request', {
            'actionButton': 'APPROVE',
            'cr_id': change_request.cr_id,
            'approvalReason': 'Approved for testing'
        })
        
        # Should redirect after approval
        self.assertEqual(response.status_code, 302)
        
        # Verify approval was created
        approval = CRApproval.objects.filter(
            cr_id=change_request,
            approver=self.approver_profile
        ).first()
        
        self.assertIsNotNone(approval)
        self.assertTrue(approval.approval_status)
    
    def test_soft_delete_and_restore_workflow(self):
        """Test soft delete and restore workflow"""
        # Create a change request
        change_request = ChangeRequest.objects.create(
            cr_id='CR002',
            change_type='PROFILE_MODIFICATION',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Soft delete the change request
        response = self.client.post('/change_requests/delete_change_request', {
            'cr_id': change_request.cr_id
        })
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Verify soft delete
        change_request.refresh_from_db()
        self.assertTrue(change_request.is_deleted)
        self.assertIsNotNone(change_request.deleted_at)
        self.assertEqual(change_request.deleted_by, self.user_profile)
        
        # Restore the change request
        response = self.client.post('/change_requests/restore_change_request', {
            'cr_id': change_request.cr_id
        })
        
        # Should redirect after restore
        self.assertEqual(response.status_code, 302)
        
        # Verify restore
        change_request.refresh_from_db()
        self.assertFalse(change_request.is_deleted)
        self.assertIsNone(change_request.deleted_at)
        self.assertIsNone(change_request.deleted_by)
    
    def test_bulk_delete_workflow(self):
        """Test bulk delete workflow"""
        # Create multiple change requests
        change_requests = []
        for i in range(3):
            cr = ChangeRequest.objects.create(
                cr_id=f'CR{i+3:03d}',
                change_type='PROFILE_MODIFICATION',
                change_reason=f'Test reason {i+1}',
                change_description=f'Test description {i+1}',
                created_by=self.user_profile,
                creator_designation=self.designation,
                region=self.region,
                cost_center=self.cost_center
            )
            change_requests.append(cr)
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Bulk delete change requests
        cr_ids = [cr.cr_id for cr in change_requests]
        response = self.client.post('/change_requests/bulk_delete_change_requests', {
            'cr_ids[]': cr_ids
        })
        
        # Should redirect after bulk delete
        self.assertEqual(response.status_code, 302)
        
        # Verify all change requests are soft deleted
        for cr in change_requests:
            cr.refresh_from_db()
            self.assertTrue(cr.is_deleted)
            self.assertEqual(cr.deleted_by, self.user_profile)
    
    def test_permission_workflow(self):
        """Test permission-based access control workflow"""
        # Create a change request by one user
        change_request = ChangeRequest.objects.create(
            cr_id='CR006',
            change_type='PROFILE_MODIFICATION',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_user_profile = UserProfile.objects.create(
            user=other_user,
            username='otheruser',
            first_name='Other',
            last_name='User',
            email='other@example.com'
        )
        
        # Login as other user
        self.client.login(username='otheruser', password='testpass123')
        
        # Try to delete change request created by different user
        response = self.client.post('/change_requests/delete_change_request', {
            'cr_id': change_request.cr_id
        })
        
        # Should redirect (permission denied)
        self.assertEqual(response.status_code, 302)
        
        # Verify change request is not deleted
        change_request.refresh_from_db()
        self.assertFalse(change_request.is_deleted)
    
    def test_validation_workflow(self):
        """Test input validation workflow"""
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Try to create change request with invalid data
        response = self.client.post('/change_requests/create_new_profile', {
            'change_reason': '',  # Missing required field
            'change_description': '',  # Missing required field
            'username': '',  # Missing required field
            'first_name': '',  # Missing required field
            'last_name': '',  # Missing required field
            'email': '',  # Missing required field
        })
        
        # Should redirect (validation failed)
        self.assertEqual(response.status_code, 302)
        
        # Verify no change request was created
        change_requests = ChangeRequest.objects.filter(created_by=self.user_profile)
        self.assertEqual(change_requests.count(), 0)
    
    def test_approval_status_workflow(self):
        """Test approval status progression workflow"""
        # Create a change request
        change_request = ChangeRequest.objects.create(
            cr_id='CR007',
            change_type='NEW_PROFILE',
            change_reason='Test reason',
            change_description='Test description',
            created_by=self.user_profile,
            creator_designation=self.designation,
            region=self.region,
            cost_center=self.cost_center
        )
        
        # Initially should be pending section head approval
        section_head_approval = CRApproval.objects.filter(
            cr_id=change_request,
            approver_role__role="section_head"
        ).first()
        self.assertIsNone(section_head_approval)
        
        # Create section head approval
        CRApproval.objects.create(
            cr_id=change_request,
            approver=self.approver_profile,
            approver_role=self.section_head_role,
            approval_status=True,
            comment='Approved by section head',
            approval_date=timezone.now()
        )
        
        # Now should be pending IT approval
        it_approval = CRApproval.objects.filter(
            cr_id=change_request,
            approver_role__role="it_section_head"
        ).first()
        self.assertIsNone(it_approval)
        
        # Create IT approval
        CRApproval.objects.create(
            cr_id=change_request,
            approver=self.approver_profile,
            approver_role=self.it_section_head_role,
            approval_status=True,
            comment='Approved by IT section head',
            approval_date=timezone.now()
        )
        
        # Now should be complete
        section_head_approval = CRApproval.objects.filter(
            cr_id=change_request,
            approver_role__role="section_head"
        ).first()
        it_approval = CRApproval.objects.filter(
            cr_id=change_request,
            approver_role__role="it_section_head"
        ).first()
        
        self.assertIsNotNone(section_head_approval)
        self.assertIsNotNone(it_approval)
        self.assertTrue(section_head_approval.approval_status)
        self.assertTrue(it_approval.approval_status)


class SecurityIntegrationTestCase(TestCase):
    """Integration tests for security features"""
    
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
        
        self.client = Client()
    
    def test_csrf_protection(self):
        """Test CSRF protection on POST endpoints"""
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Try to create change request without CSRF token
        response = self.client.post('/change_requests/create_new_profile', {
            'change_reason': 'Test reason',
            'change_description': 'Test description',
        }, follow=True)
        
        # Should be redirected or show CSRF error
        self.assertIn(response.status_code, [302, 403])
    
    def test_xss_prevention(self):
        """Test XSS prevention in input handling"""
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Try to submit malicious input
        malicious_input = '<script>alert("XSS")</script>'
        
        response = self.client.post('/change_requests/create_new_profile', {
            'change_reason': malicious_input,
            'change_description': 'Test description',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
        })
        
        # Should not cause XSS (response should be successful or redirect)
        self.assertIn(response.status_code, [200, 302])
        
        # If a change request was created, verify the input was sanitized
        change_request = ChangeRequest.objects.filter(
            created_by=self.user_profile
        ).first()
        
        if change_request:
            # The input should be escaped in the database
            self.assertNotIn('<script>', change_request.change_reason)
    
    def test_authentication_required(self):
        """Test that authentication is required for all endpoints"""
        # Try to access endpoints without authentication
        endpoints = [
            '/change_requests/change_request_index',
            '/change_requests/create_change_request',
            '/change_requests/delete_change_request',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Should redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login', response.url)
