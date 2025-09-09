from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from process_management.models import ProcessDepartment, Process, ProcessDocument
from it.users.models import UserProfile, Regions


class ProcessManagementTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            employee_number='EMP001'
        )
        
        # Create test department
        self.department = ProcessDepartment.objects.create(
            name='Test Department',
            description='Test department description',
            order=1
        )
        
        # Create test process
        self.process = Process.objects.create(
            name='Test Process',
            description='Test process description',
            department=self.department,
            created_by=self.user_profile
        )
        
        self.client.login(username='testuser', password='testpass123')

    def test_process_management_template_renders(self):
        """Test that the process management template renders correctly"""
        response = self.client.get(reverse('process_management:process_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Process Management')
        self.assertContains(response, 'Add New Process')

    def test_process_form_template_renders(self):
        """Test that the process form template renders correctly"""
        response = self.client.get(reverse('process_management:create_process'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Process')
        self.assertContains(response, 'Process Name')
        self.assertContains(response, 'Department')

    def test_process_form_edit_template_renders(self):
        """Test that the process edit form template renders correctly"""
        response = self.client.get(
            reverse('process_management:edit_process', args=[self.process.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Process')
        self.assertContains(response, self.process.name)

    def test_document_upload_template_renders(self):
        """Test that the document upload template renders correctly"""
        response = self.client.get(
            reverse('process_management:manage_documents', args=[self.process.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Documents')
        self.assertContains(response, 'Process Map')
        self.assertContains(response, 'Procedure')
        self.assertContains(response, 'Risk and Opportunity Register')

    def test_template_context_variables(self):
        """Test that templates receive correct context variables"""
        response = self.client.get(
            reverse('process_management:manage_documents', args=[self.process.id])
        )
        self.assertEqual(response.context['process'], self.process)
        self.assertIn('process_map_documents', response.context)
        self.assertIn('procedure_documents', response.context)
        self.assertIn('risk_register_documents', response.context)

    def test_template_inheritance(self):
        """Test that templates properly extend admin_layout.html"""
        response = self.client.get(reverse('process_management:process_list'))
        self.assertContains(response, 'admin_layout.html')

    def test_csrf_token_in_forms(self):
        """Test that CSRF tokens are present in forms"""
        response = self.client.get(reverse('process_management:create_process'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        response = self.client.get(
            reverse('process_management:manage_documents', args=[self.process.id])
        )
        self.assertContains(response, 'csrf_token')

    def test_responsive_design_classes(self):
        """Test that templates include responsive design classes"""
        response = self.client.get(reverse('process_management:process_list'))
        self.assertContains(response, 'container mx-auto')
        self.assertContains(response, 'grid')

    def test_javascript_functionality(self):
        """Test that templates include necessary JavaScript"""
        response = self.client.get(reverse('process_management:process_list'))
        self.assertContains(response, 'DataTable')
        self.assertContains(response, 'jquery')
        
        response = self.client.get(
            reverse('process_management:manage_documents', args=[self.process.id])
        )
        self.assertContains(response, 'handleDrop')
        self.assertContains(response, 'uploadFile')

    def test_error_handling_in_templates(self):
        """Test that templates handle errors gracefully"""
        response = self.client.get(reverse('process_management:create_process'))
        self.assertContains(response, 'error-message')
        
    def test_success_message_display(self):
        """Test that templates display success messages"""
        response = self.client.get(reverse('process_management:create_process'))
        self.assertContains(response, 'success-message')