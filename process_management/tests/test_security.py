"""
Tests for process management security and permissions.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

from process_management.models import ProcessDepartment, Process, ProcessDocument
from it.users.models import UserProfile, Roles, Application


class ProcessManagementSecurityTest(TestCase):
    """Test security and permissions for process management."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            email='admin@test.com'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            email='regular@test.com'
        )
        
        # Create test application
        self.app = Application.objects.create(
            name='process_management',
            fullname='Process Management'
        )
        
        # Create test roles
        self.admin_role = Roles.objects.create(
            role='admin',
            name='Administrator',
            description='System administrator',
            application='process_management',
            app_id=self.app
        )
        
        self.manager_role = Roles.objects.create(
            role='manager',
            name='Process Manager',
            description='Process manager',
            application='process_management',
            app_id=self.app
        )
        
        # Create user profiles
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            employee_number='EMP001'
        )
        self.admin_profile.roles.add(self.admin_role)
        
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user,
            employee_number='EMP002'
        )
        
        # Create test department and process
        self.department = ProcessDepartment.objects.create(
            name='TEST DEPARTMENT',
            description='Test department'
        )
        
        self.process = Process.objects.create(
            name='Test Process',
            department=self.department
        )
    
    def test_process_list_requires_login(self):
        """Test that process list requires authentication."""
        response = self.client.get(reverse('process_management:process_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_process_list_allows_authenticated_users(self):
        """Test that authenticated users can access process list."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('process_management:process_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_process_create_requires_permission(self):
        """Test that process creation requires proper permissions."""
        # Regular user should be denied
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('process_management:process_create'))
        self.assertEqual(response.status_code, 302)  # Redirect due to permission denied
        
        # Admin user should be allowed
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('process_management:process_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_process_edit_requires_permission(self):
        """Test that process editing requires proper permissions."""
        # Regular user should be denied
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(
            reverse('process_management:process_edit', args=[self.process.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect due to permission denied
        
        # Admin user should be allowed
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(
            reverse('process_management:process_edit', args=[self.process.id])
        )
        self.assertEqual(response.status_code, 200)
    
    def test_process_delete_requires_admin_permission(self):
        """Test that process deletion requires admin permissions."""
        # Regular user should be denied
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(
            reverse('process_management:process_delete', args=[self.process.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect due to permission denied
        
        # Admin user should be allowed
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(
            reverse('process_management:process_delete', args=[self.process.id])
        )
        self.assertEqual(response.status_code, 200)
    
    @patch('process_management.views.log_process_activity')
    def test_audit_logging_on_process_list_access(self, mock_log):
        """Test that process list access is logged."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('process_management:process_list'))
        
        # Verify logging was called
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        self.assertEqual(args[0], self.regular_user)
        self.assertEqual(args[1], 'view_process_list')
    
    @patch('process_management.views.log_process_activity')
    def test_audit_logging_on_search(self, mock_log):
        """Test that search activities are logged."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(
            reverse('process_management:process_list') + '?search=test'
        )
        
        # Verify logging was called with search details
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        self.assertEqual(args[0], self.regular_user)
        self.assertEqual(args[1], 'view_process_list')
        self.assertIn('Search query', kwargs.get('details', ''))
    
    def test_document_access_control(self):
        """Test document access control."""
        # Create a test document
        document = ProcessDocument.objects.create(
            process=self.process,
            document_type='procedure',
            filename='test_document.pdf',
            version='1.0'
        )
        
        # Unauthenticated user should be denied
        response = self.client.get(
            reverse('process_management:document_download', args=[document.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Authenticated user should be allowed (for now)
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(
            reverse('process_management:document_download', args=[document.id])
        )
        # Note: This will return 404 because the file doesn't actually exist
        # but it shows the user passed authentication
        self.assertEqual(response.status_code, 404)


class AuditLoggingTest(TestCase):
    """Test audit logging functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.department = ProcessDepartment.objects.create(
            name='TEST DEPARTMENT',
            description='Test department'
        )
        
        self.process = Process.objects.create(
            name='Test Process',
            department=self.department
        )
        
        self.document = ProcessDocument.objects.create(
            process=self.process,
            document_type='procedure',
            filename='test_document.pdf',
            version='1.0'
        )
    
    @patch('process_management.views.logger')
    def test_log_process_activity_basic(self, mock_logger):
        """Test basic audit logging functionality."""
        from process_management.views import log_process_activity
        
        log_process_activity(self.user, 'test_action')
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn(self.user.username, log_message)
        self.assertIn('test_action', log_message)
    
    @patch('process_management.views.logger')
    def test_log_process_activity_with_process(self, mock_logger):
        """Test audit logging with process information."""
        from process_management.views import log_process_activity
        
        log_process_activity(self.user, 'test_action', process=self.process)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn(self.process.name, log_message)
        self.assertIn(str(self.process.id), log_message)
    
    @patch('process_management.views.logger')
    def test_log_process_activity_with_document(self, mock_logger):
        """Test audit logging with document information."""
        from process_management.views import log_process_activity
        
        log_process_activity(
            self.user, 
            'test_action', 
            process=self.process,
            document=self.document
        )
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn(self.document.filename, log_message)
        self.assertIn(str(self.document.id), log_message)
    
    @patch('process_management.views.logger')
    def test_log_process_activity_with_details(self, mock_logger):
        """Test audit logging with additional details."""
        from process_management.views import log_process_activity
        
        details = "Additional context information"
        log_process_activity(self.user, 'test_action', details=details)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn(details, log_message)