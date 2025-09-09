from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    Substation, 
    MonthlyInspectionSchedule, 
    MonthlyInspectionReport, 
    InspectionChecklistItem, 
    InspectionItemResponse
)

User = get_user_model()


class SubstationModelTest(TestCase):
    def setUp(self):
        self.substation = Substation.objects.create(
            substation_code='SUB-001',
            name='Test Substation',
            substation_type='primary',
            voltage_level='33kv',
            location='Test Location',
            district='Test District',
            region='Test Region',
            transformers_count=2,
            circuit_breakers_count=4,
            switchgear_count=1
        )

    def test_substation_creation(self):
        self.assertEqual(self.substation.substation_code, 'SUB-001')
        self.assertEqual(self.substation.name, 'Test Substation')
        self.assertEqual(self.substation.substation_type, 'primary')
        self.assertEqual(self.substation.voltage_level, '33kv')
        self.assertTrue(self.substation.is_active)

    def test_substation_str_representation(self):
        expected = 'SUB-001 - Test Substation'
        self.assertEqual(str(self.substation), expected)

    def test_substation_auto_code_generation(self):
        substation = Substation.objects.create(
            name='Auto Code Test',
            substation_type='secondary',
            voltage_level='11kv',
            location='Test Location',
            district='Test District',
            region='Test Region'
        )
        self.assertTrue(substation.substation_code.startswith('SUB-'))


class MonthlyInspectionReportModelTest(TestCase):
    def setUp(self):
        self.substation = Substation.objects.create(
            substation_code='SUB-002',
            name='Test Substation 2',
            substation_type='secondary',
            voltage_level='11kv',
            location='Test Location 2',
            district='Test District 2',
            region='Test Region 2'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report = MonthlyInspectionReport.objects.create(
            substation=self.substation,
            inspection_date=date.today(),
            scheduled_date=date.today(),
            inspector=self.user,
            status='scheduled'
        )

    def test_inspection_report_creation(self):
        self.assertEqual(self.report.substation, self.substation)
        self.assertEqual(self.report.inspector, self.user)
        self.assertEqual(self.report.status, 'scheduled')
        self.assertTrue(self.report.report_number.startswith('RPT-'))

    def test_inspection_report_str_representation(self):
        expected = f'{self.report.report_number} - {self.substation.substation_code} - {self.report.inspection_date}'
        self.assertEqual(str(self.report), expected)


class InspectionChecklistItemModelTest(TestCase):
    def setUp(self):
        self.checklist_item = InspectionChecklistItem.objects.create(
            item_code='SAF-001',
            title='Test Safety Check',
            description='Test safety check description',
            category='safety',
            severity='high',
            is_mandatory=True
        )

    def test_checklist_item_creation(self):
        self.assertEqual(self.checklist_item.item_code, 'SAF-001')
        self.assertEqual(self.checklist_item.title, 'Test Safety Check')
        self.assertEqual(self.checklist_item.category, 'safety')
        self.assertEqual(self.checklist_item.severity, 'high')
        self.assertTrue(self.checklist_item.is_mandatory)
        self.assertTrue(self.checklist_item.is_active)

    def test_checklist_item_str_representation(self):
        expected = 'SAF-001 - Test Safety Check'
        self.assertEqual(str(self.checklist_item), expected)

    def test_checklist_item_auto_code_generation(self):
        item = InspectionChecklistItem.objects.create(
            title='Auto Code Test',
            description='Test description',
            category='electrical',
            severity='medium'
        )
        self.assertTrue(item.item_code.startswith('CHK-ELC-'))


class SubstationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.substation = Substation.objects.create(
            substation_code='SUB-003',
            name='Test Substation 3',
            substation_type='primary',
            voltage_level='132kv',
            location='Test Location 3',
            district='Test District 3',
            region='Test Region 3'
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('substation_inspections:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Substation Inspection Administration')

    def test_substation_list_view(self):
        response = self.client.get(reverse('substation_inspections:substation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Substation Management')
        self.assertContains(response, 'Test Substation 3')

    def test_substation_detail_view(self):
        response = self.client.get(reverse('substation_inspections:substation_detail', args=[self.substation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Substation 3')

    def test_substation_create_view_get(self):
        response = self.client.get(reverse('substation_inspections:substation_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Substation')

    def test_substation_create_view_post(self):
        data = {
            'substation_code': 'SUB-004',
            'name': 'New Test Substation',
            'substation_type': 'secondary',
            'voltage_level': '11kv',
            'location': 'New Test Location',
            'district': 'New Test District',
            'region': 'New Test Region',
            'transformers_count': 1,
            'circuit_breakers_count': 2,
            'switchgear_count': 1,
            'is_active': True
        }
        response = self.client.post(reverse('substation_inspections:substation_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Substation.objects.filter(substation_code='SUB-004').exists())

    def test_substation_edit_view_get(self):
        response = self.client.get(reverse('substation_inspections:substation_edit', args=[self.substation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Test Substation 3')

    def test_substation_edit_view_post(self):
        data = {
            'substation_code': 'SUB-003',
            'name': 'Updated Test Substation',
            'substation_type': 'primary',
            'voltage_level': '132kv',
            'location': 'Updated Test Location',
            'district': 'Test District 3',
            'region': 'Test Region 3',
            'transformers_count': 3,
            'circuit_breakers_count': 6,
            'switchgear_count': 2,
            'is_active': True
        }
        response = self.client.post(reverse('substation_inspections:substation_edit', args=[self.substation.pk]), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.substation.refresh_from_db()
        self.assertEqual(self.substation.name, 'Updated Test Substation')
        self.assertEqual(self.substation.transformers_count, 3)


class InspectionReportViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.substation = Substation.objects.create(
            substation_code='SUB-005',
            name='Test Substation 5',
            substation_type='primary',
            voltage_level='33kv',
            location='Test Location 5',
            district='Test District 5',
            region='Test Region 5'
        )

    def test_inspection_report_list_view(self):
        response = self.client.get(reverse('substation_inspections:inspection_report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inspection Reports')

    def test_inspection_report_create_view_get(self):
        response = self.client.get(reverse('substation_inspections:inspection_report_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Inspection Report')

    def test_inspection_report_create_view_post(self):
        data = {
            'substation': self.substation.pk,
            'inspection_date': date.today(),
            'weather_conditions': 'Clear',
            'temperature': 25.5,
            'humidity': 60,
            'overall_condition': 'Good condition',
            'critical_issues': 'None',
            'recommendations': 'Continue regular maintenance'
        }
        response = self.client.post(reverse('substation_inspections:inspection_report_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(MonthlyInspectionReport.objects.filter(substation=self.substation).exists())


class APIViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.substation = Substation.objects.create(
            substation_code='SUB-006',
            name='Test Substation 6',
            substation_type='primary',
            voltage_level='33kv',
            location='Test Location 6',
            district='Test District 6',
            region='Test Region 6'
        )

    def test_get_substation_details_api(self):
        response = self.client.get(reverse('substation_inspections:api_substation_details', args=[self.substation.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['substation_code'], 'SUB-006')
        self.assertEqual(data['name'], 'Test Substation 6')

    def test_get_inspection_stats_api(self):
        response = self.client.get(reverse('substation_inspections:api_inspection_stats'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_substations', data)
        self.assertIn('pending_inspections', data)
        self.assertIn('completed_this_month', data)
        self.assertIn('overdue_inspections', data)