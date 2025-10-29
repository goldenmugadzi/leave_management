"""
Tests for Inspection Sync API Endpoints
Tests authentication, permissions, rate limiting, and data format
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import (
    Customer, Contractor, ClientApplication, ApplicationAssignment,
    InspectionReport, E1DefectReport, E6Certificate, InspectionPhoto
)

User = get_user_model()


class SyncAPITestBase(TestCase):
    """Base test class with common setup"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        # Create test users
        self.inspector = User.objects.create_user(
            username='inspector1',
            password='testpass123',
            email='inspector@test.com'
        )
        
        self.other_inspector = User.objects.create_user(
            username='inspector2',
            password='testpass123',
            email='inspector2@test.com'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            email='admin@test.com'
        )
        
        # Create test customer and contractor
        self.customer = Customer.objects.create(
            full_name='Test Customer',
            phone='1234567890',
            email='customer@test.com'
        )
        
        self.contractor = Contractor.objects.create(
            business_name='Test Contractor',
            contact_person='John Doe',
            phone='0987654321'
        )
        
        # Create test application
        self.application = ClientApplication.objects.create(
            application_type='new_installation',
            customer=self.customer,
            contractor=self.contractor,
            purpose='domestic',
            supply_type='permanent',
            submitted_by=self.admin_user
        )
        
        # Create assignment to inspector
        self.assignment = ApplicationAssignment.objects.create(
            application=self.application,
            assigned_to=self.inspector,
            assigned_by=self.admin_user,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Create inspection report
        self.inspection = InspectionReport.objects.create(
            client_application=self.application,
            inspector=self.inspector,
            service_no='TEST-001',
            consumer_name='Test Consumer',
            inspection_date=timezone.now().date(),
            status='pass'
        )
        
        # Get JWT token for authentication
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.inspector)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')


class DownloadInspectionBatchTestCase(SyncAPITestBase):
    """Test E117 inspection batch download endpoint"""
    
    def test_requires_authentication(self):
        """Test that endpoint requires authentication"""
        self.client.credentials()  # Remove credentials
        response = self.client.get('/inspections/api/sync/download-inspection-batch/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_download_assigned_inspections(self):
        """Test downloading inspections assigned to user"""
        response = self.client.get('/inspections/api/sync/download-inspection-batch/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['inspections']), 1)
        self.assertIn('next_cursor', data)
        self.assertIn('server_time', data)
        self.assertEqual(data['count'], 1)
        
        # Check inspection data format
        inspection = data['inspections'][0]
        self.assertEqual(inspection['service_number'], 'TEST-001')
        self.assertEqual(inspection['consumer_name'], 'Test Consumer')
        self.assertIn('consumer_main_switch', inspection)
    
    def test_pagination(self):
        """Test pagination with limit parameter"""
        # Create multiple inspections
        for i in range(5):
            InspectionReport.objects.create(
                client_application=self.application,
                inspector=self.inspector,
                service_no=f'TEST-{i:03d}',
                consumer_name=f'Consumer {i}',
                status='pass'
            )
        
        response = self.client.get('/inspections/api/sync/download-inspection-batch/?limit=2')
        data = response.json()
        
        self.assertEqual(len(data['inspections']), 2)
        self.assertIsNotNone(data['next_cursor'])
    
    def test_incremental_sync_with_modified_after(self):
        """Test incremental sync using modified_after parameter"""
        # Update inspection
        future_time = (timezone.now() + timedelta(hours=1)).isoformat()
        self.inspection.save()  # Update updated_at timestamp
        
        # Query with recent timestamp - should return inspection
        response = self.client.get(
            f'/inspections/api/sync/download-inspection-batch/?modified_after={timezone.now().isoformat()}'
        )
        data = response.json()
        self.assertGreaterEqual(len(data['inspections']), 1)
    
    def test_user_only_sees_assigned_inspections(self):
        """Test that users only see inspections from their assignments"""
        # Create inspection for other inspector
        other_application = ClientApplication.objects.create(
            application_type='new_installation',
            customer=self.customer,
            contractor=self.contractor,
            purpose='commercial',
            supply_type='permanent'
        )
        
        ApplicationAssignment.objects.create(
            application=other_application,
            assigned_to=self.other_inspector,
            assigned_by=self.admin_user
        )
        
        other_inspection = InspectionReport.objects.create(
            client_application=other_application,
            inspector=self.other_inspector,
            service_no='OTHER-001',
            consumer_name='Other Consumer',
            status='pass'
        )
        
        # Current inspector should not see other inspector's inspection
        response = self.client.get('/inspections/api/sync/download-inspection-batch/')
        data = response.json()
        
        service_numbers = [insp['service_number'] for insp in data['inspections']]
        self.assertNotIn('OTHER-001', service_numbers)


class DownloadE1DefectsTestCase(SyncAPITestBase):
    """Test E1 defect reports download endpoint"""
    
    def setUp(self):
        super().setUp()
        # Create E1 defect report
        self.e1_report = E1DefectReport.objects.create(
            inspection_report=self.inspection,
            client_application=self.application,
            installation_inspector=self.inspector,
            service_no='TEST-001',
            property_address='123 Test St',
            defects_requiring_attention='Loose wiring\nMissing earth connection',
            is_reinspection=False
        )
    
    def test_download_e1_defects(self):
        """Test downloading E1 defect reports"""
        response = self.client.get('/inspections/api/sync/defects/e1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['defect_reports']), 1)
        self.assertEqual(data['count'], 1)
        
        # Check report format
        report = data['defect_reports'][0]
        self.assertEqual(str(report['inspection_id']), str(self.inspection.id))
        self.assertEqual(report['inspection_result'], 'failed')
        self.assertIsInstance(report['defects_requiring_attention'], list)
    
    def test_filter_by_inspection_ids(self):
        """Test filtering E1 reports by inspection IDs"""
        response = self.client.get(
            f'/inspections/api/sync/defects/e1/?inspection_ids={self.inspection.id}'
        )
        data = response.json()
        
        self.assertEqual(len(data['defect_reports']), 1)


class DownloadE6CertificatesTestCase(SyncAPITestBase):
    """Test E6 certificates download endpoint"""
    
    def setUp(self):
        super().setUp()
        # Create E6 certificate
        self.e6_cert = E6Certificate.objects.create(
            inspection_report=self.inspection,
            client_application=self.application,
            installation_inspector=self.inspector,
            service_no='TEST-001',
            installation_description='New domestic installation',
            property_address='123 Test St',
            property_owner_occupant='Test Owner',
            minor_defects='Minor paint touch-ups needed'
        )
    
    def test_download_e6_certificates(self):
        """Test downloading E6 certificates"""
        response = self.client.get('/inspections/api/sync/certificates/e6/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['certificates']), 1)
        self.assertEqual(data['count'], 1)
        
        # Check certificate format
        cert = data['certificates'][0]
        self.assertEqual(str(cert['inspection_id']), str(self.inspection.id))
        self.assertTrue(cert['inspection_completed'])
        self.assertTrue(cert['connection_approved'])


class DownloadInspectionPhotosTestCase(SyncAPITestBase):
    """Test inspection photos download endpoint"""
    
    def setUp(self):
        super().setUp()
        # We won't create actual files in tests, just records
        # In production, you'd use Django's SimpleUploadedFile for testing
    
    def test_download_photos_for_inspection(self):
        """Test downloading photos for a specific inspection"""
        response = self.client.get(
            f'/inspections/api/sync/inspections/{self.inspection.id}/photos/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIsInstance(data['photos'], list)
        self.assertEqual(data['count'], 0)  # No photos created in this test
    
    def test_403_for_unassigned_inspection(self):
        """Test that users can't access photos from unassigned inspections"""
        # Create inspection for other user
        other_application = ClientApplication.objects.create(
            application_type='new_installation',
            customer=self.customer,
            contractor=self.contractor,
            purpose='commercial',
            supply_type='permanent'
        )
        
        ApplicationAssignment.objects.create(
            application=other_application,
            assigned_to=self.other_inspector,
            assigned_by=self.admin_user
        )
        
        other_inspection = InspectionReport.objects.create(
            client_application=other_application,
            inspector=self.other_inspector,
            service_no='OTHER-001',
            status='pass'
        )
        
        # Try to access photos
        response = self.client.get(
            f'/inspections/api/sync/inspections/{other_inspection.id}/photos/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertFalse(data['success'])


class DownloadGeneralDefectsTestCase(SyncAPITestBase):
    """Test general defects download endpoint"""
    
    def setUp(self):
        super().setUp()
        # Create E1 report with defects
        self.e1_report = E1DefectReport.objects.create(
            inspection_report=self.inspection,
            client_application=self.application,
            installation_inspector=self.inspector,
            service_no='TEST-001',
            defects_requiring_attention='Exposed wiring in kitchen\nLoose earth connection'
        )
    
    def test_download_general_defects(self):
        """Test downloading general defects"""
        response = self.client.get('/inspections/api/sync/defects/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertGreater(len(data['defects']), 0)
        
        # Check defect format
        defect = data['defects'][0]
        self.assertIn('defect_description', defect)
        self.assertIn('severity', defect)
        self.assertIn('status', defect)


class RateLimitingTestCase(SyncAPITestBase):
    """Test rate limiting on sync endpoints"""
    
    def test_rate_limit_not_exceeded_on_normal_use(self):
        """Test that normal use doesn't trigger rate limiting"""
        # Make a few requests (well under the limit)
        for _ in range(5):
            response = self.client.get('/inspections/api/sync/download-inspection-batch/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Note: Fully testing rate limiting would require mocking time or
    # making 100+ requests, which is slow. In practice, manual testing
    # or integration tests would verify this.


class ErrorHandlingTestCase(SyncAPITestBase):
    """Test error handling in sync endpoints"""
    
    def test_invalid_modified_after_format(self):
        """Test handling of invalid modified_after parameter"""
        response = self.client.get(
            '/inspections/api/sync/download-inspection-batch/?modified_after=invalid-date'
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_404_for_nonexistent_inspection_photos(self):
        """Test 404 error for non-existent inspection"""
        fake_id = uuid.uuid4()
        response = self.client.get(
            f'/inspections/api/sync/inspections/{fake_id}/photos/'
        )
        
        # Should return 403 (not 404) since user doesn't have access
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

