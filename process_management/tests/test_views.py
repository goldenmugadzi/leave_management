from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count
from it.users.models import UserProfile, Regions
from process_management.models import ProcessDepartment, Process, ProcessDocument


class ProcessListViewTest(TestCase):
    """Test cases for process_list_view function"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            employee_number='EMP001',
            first_name='Test',
            last_name='User'
        )
        
        # Create test departments
        self.dept1 = ProcessDepartment.objects.create(
            name="GENERAL MANAGER'S OFFICE",
            description="General management processes",
            order=1
        )
        self.dept2 = ProcessDepartment.objects.create(
            name="ENGINEERING MANAGER'S OFFICE",
            description="Engineering processes",
            order=2
        )
        self.dept3 = ProcessDepartment.objects.create(
            name="FINANCE",
            description="Financial processes",
            order=3
        )
        
        # Create test region
        self.region = Regions.objects.create(name="Test Region")
        
        # Create test processes
        self.process1 = Process.objects.create(
            name="Strategic Planning Process",
            description="Annual strategic planning and review",
            department=self.dept1,
            region=self.region,
            process_code="SP001",
            created_by=self.user_profile
        )
        
        self.process2 = Process.objects.create(
            name="Budget Management",
            description="Budget planning and monitoring",
            department=self.dept3,
            process_code="BM001",
            created_by=self.user_profile
        )
        
        self.process3 = Process.objects.create(
            name="Engineering Design Review",
            description="Design review and approval process",
            department=self.dept2,
            created_by=self.user_profile
        )
        
        # Create inactive process (should not appear in counts)
        self.inactive_process = Process.objects.create(
            name="Inactive Process",
            description="This process is inactive",
            department=self.dept1,
            is_active=False,
            created_by=self.user_profile
        )
    
    def test_process_list_view_requires_login(self):
        """Test that process list view requires authentication"""
        url = reverse('process_management:process_list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_process_list_view_displays_departments(self):
        """Test that process list view displays all departments with correct counts"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('process_management:process_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GENERAL MANAGER'S OFFICE")
        self.assertContains(response, "ENGINEERING MANAGER'S OFFICE")
        self.assertContains(response, "FINANCE")
        
        # Check process counts (should exclude inactive processes)
        departments = response.context['departments']
        dept_counts = {dept.name: dept.process_count for dept in departments}
        
        self.assertEqual(dept_counts["GENERAL MANAGER'S OFFICE"], 1)  # Only active process
        self.assertEqual(dept_counts["ENGINEERING MANAGER'S OFFICE"], 1)
        self.assertEqual(dept_counts["FINANCE"], 1)


class ProcessDepartmentViewTest(TestCase):
    """Test cases for process_department_view function"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            employee_number='EMP001',
            first_name='Test',
            last_name='User'
        )
        
        # Create test department
        self.department = ProcessDepartment.objects.create(
            name="FINANCE",
            description="Financial processes",
            order=1
        )
        
        # Create test regions
        self.region1 = Regions.objects.create(name="Region 1")
        self.region2 = Regions.objects.create(name="Region 2")
        
        # Create test processes
        self.process1 = Process.objects.create(
            name="Budget Planning",
            description="Annual budget planning process",
            department=self.department,
            region=self.region1,
            process_code="BP001",
            created_by=self.user_profile
        )
        
        self.process2 = Process.objects.create(
            name="Financial Reporting",
            description="Monthly financial reporting",
            department=self.department,
            region=self.region2,
            process_code="FR001",
            created_by=self.user_profile
        )
        
        self.process3 = Process.objects.create(
            name="Audit Process",
            description="Internal audit procedures",
            department=self.department,
            region=self.region1,
            created_by=self.user_profile
        )
        
        # Create inactive process
        self.inactive_process = Process.objects.create(
            name="Inactive Process",
            description="This process is inactive",
            department=self.department,
            is_active=False,
            created_by=self.user_profile
        )
    
    def test_department_view_requires_login(self):
        """Test that department view requires authentication"""
        url = reverse('process_management:department_processes', args=[self.department.id])
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_department_view_displays_processes(self):
        """Test that department view displays processes for the department"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('process_management:department_processes', args=[self.department.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Budget Planning')
        self.assertContains(response, 'Financial Reporting')
        self.assertContains(response, 'Audit Process')
        self.assertNotContains(response, 'Inactive Process')


class ProcessDetailViewTest(TestCase):
    """Test cases for process_detail_view function"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            employee_number='EMP001',
            first_name='Test',
            last_name='User'
        )
        
        # Create test department
        self.department = ProcessDepartment.objects.create(
            name="FINANCE",
            description="Financial processes",
            order=1
        )
        
        # Create test region
        self.region = Regions.objects.create(name="Test Region")
        
        # Create test process
        self.process = Process.objects.create(
            name="Budget Planning",
            description="Annual budget planning process",
            department=self.department,
            region=self.region,
            process_code="BP001",
            created_by=self.user_profile
        )
        
        # Create test documents
        self.process_map = ProcessDocument.objects.create(
            process=self.process,
            document_type='process_map',
            filename='budget_process_map.pdf',
            version='1.0',
            uploaded_by=self.user_profile
        )
        
        self.procedure = ProcessDocument.objects.create(
            process=self.process,
            document_type='procedure',
            filename='budget_procedure.pdf',
            version='2.0',
            uploaded_by=self.user_profile
        )
        
        # Create inactive process
        self.inactive_process = Process.objects.create(
            name="Inactive Process",
            description="This process is inactive",
            department=self.department,
            is_active=False,
            created_by=self.user_profile
        )
    
    def test_process_detail_view_requires_login(self):
        """Test that process detail view requires authentication"""
        url = reverse('process_management:process_detail', args=[self.process.id])
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_process_detail_view_displays_process(self):
        """Test that process detail view displays process information"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('process_management:process_detail', args=[self.process.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Budget Planning')
        self.assertContains(response, 'Annual budget planning process')
        self.assertContains(response, 'BP001')
        self.assertContains(response, 'FINANCE')
        self.assertContains(response, 'Test Region')