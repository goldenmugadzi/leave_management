#!/usr/bin/env python3
"""
Test script for Mobile API endpoints
Run this script to test the mobile API implementation
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/var/www/beii_v1')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from inspections.models import Customer, Contractor, ClientApplication, ApplicationAssignment

User = get_user_model()


class MobileAPITestCase(TestCase):
    """Test case for mobile API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='test_officer',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            full_name='John Doe',
            phone='+263771234567',
            email='john@example.com',
            stand_plot_number='123',
            farm_street_name='Main Street',
            suburb_township='Harare',
            district='Harare'
        )
        
        # Create test contractor
        self.contractor = Contractor.objects.create(
            business_name='ABC Electrical Services',
            contact_person='Peter Smith',
            phone='+263771234568',
            email='peter@abcelectrical.com',
            address='456 Industrial Road, Harare',
            license_number='ELC-2025-001',
            business_registration='BR-2025-001'
        )
        
        # Create test application
        self.application = ClientApplication.objects.create(
            application_number='APP-20250120-001234',
            application_type='new_installation',
            priority='high',
            customer=self.customer,
            contractor=self.contractor,
            purpose='domestic',
            supply_type='permanent',
            status='assigned'
        )
        
        # Create test assignment
        self.assignment = ApplicationAssignment.objects.create(
            application=self.application,
            assigned_to=self.user,
            assigned_by=self.user,
            status='assigned'
        )
        
        # Create API client
        self.client = APIClient()
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_assigned_applications(self):
        """Test GET /api/v1/applications/assigned/"""
        response = self.client.get('/inspections/api/v1/applications/assigned/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('applications', response.data['data'])
        self.assertIn('total_count', response.data['data'])
    
    def test_get_application_details(self):
        """Test GET /api/v1/applications/{id}/"""
        response = self.client.get(f'/inspections/api/v1/applications/{self.application.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('id', response.data['data'])
        self.assertEqual(response.data['data']['id'], str(self.application.id))
    
    def test_accept_assignment(self):
        """Test POST /api/v1/applications/{id}/accept/"""
        data = {
            'officer_id': str(self.user.id),
            'accepted_at': '2025-01-20T11:00:00Z',
            'notes': 'Will inspect on Monday morning'
        }
        response = self.client.post(
            f'/inspections/api/v1/applications/{self.application.id}/accept/',
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['assignment_status'], 'accepted')
    
    def test_update_assignment_status(self):
        """Test PATCH /api/v1/applications/{id}/status/"""
        data = {
            'assignment_status': 'in_progress',
            'status': 'in_progress',
            'officer_id': str(self.user.id),
            'notes': 'Started inspection process'
        }
        response = self.client.patch(
            f'/inspections/api/v1/applications/{self.application.id}/status/',
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['assignment_status'], 'in_progress')
    
    def test_complete_assignment(self):
        """Test POST /api/v1/applications/{id}/complete/"""
        data = {
            'officer_id': str(self.user.id),
            'completed_at': '2025-01-22T15:30:00Z',
            'inspection_result': 'passed',
            'completion_notes': 'Installation meets all safety requirements'
        }
        response = self.client.post(
            f'/inspections/api/v1/applications/{self.application.id}/complete/',
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['assignment_status'], 'completed')
    
    def test_get_application_attachments(self):
        """Test GET /api/v1/applications/{id}/attachments/"""
        response = self.client.get(f'/inspections/api/v1/applications/{self.application.id}/attachments/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('attachments', response.data['data'])
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access endpoints"""
        # Create another user
        other_user = User.objects.create_user(
            username='other_officer',
            email='other@example.com',
            password='testpass123'
        )
        
        # Get token for other user
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Try to access application assigned to different user
        response = self.client.get(f'/inspections/api/v1/applications/{self.application.id}/')
        self.assertEqual(response.status_code, 404)


def run_tests():
    """Run the mobile API tests"""
    print("Running Mobile API Tests...")
    print("=" * 50)
    
    # Create test case instance
    test_case = MobileAPITestCase()
    test_case.setUp()
    
    # Run individual tests
    tests = [
        ('Get Assigned Applications', test_case.test_get_assigned_applications),
        ('Get Application Details', test_case.test_get_application_details),
        ('Accept Assignment', test_case.test_accept_assignment),
        ('Update Assignment Status', test_case.test_update_assignment_status),
        ('Complete Assignment', test_case.test_complete_assignment),
        ('Get Application Attachments', test_case.test_get_application_attachments),
        ('Unauthorized Access', test_case.test_unauthorized_access),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...", end=' ')
            test_func()
            print("✅ PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            failed += 1
    
    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Mobile API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")


if __name__ == '__main__':
    run_tests()
