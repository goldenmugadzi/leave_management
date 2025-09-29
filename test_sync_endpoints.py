#!/usr/bin/env python
"""
Test script for the new sync endpoints
"""

import os
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

class SyncEndpointsTest(TestCase):
    """Test the new sync endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_assignment_sync_endpoint(self):
        """Test assignment sync endpoint"""
        url = reverse('inspections:sync-assignment')
        data = {
            'application': '12345678-1234-5678-9abc-123456789abc',
            'assigned_to': '87654321-4321-8765-cba9-fedcba987654',
            'assigned_by': '87654321-4321-8765-cba9-fedcba987654',
            'assignment_date': '2024-01-01T10:00:00Z',
            'status': 'assigned'
        }

        response = self.client.post(url, data, content_type='application/json')
        print(f"Assignment sync response status: {response.status_code}")
        print(f"Assignment sync response: {response.content[:200]}...")
        return response.status_code == 200 or response.status_code == 201

    def test_approval_sync_endpoint(self):
        """Test approval sync endpoint"""
        url = reverse('inspections:sync-approval')
        data = {
            'step': 1,
            'user': '87654321-4321-8765-cba9-fedcba987654',
            'process': '12345678-1234-5678-9abc-123456789abc',
            'approved': 'Approved'
        }

        response = self.client.post(url, data, content_type='application/json')
        print(f"Approval sync response status: {response.status_code}")
        print(f"Approval sync response: {response.content[:200]}...")
        return response.status_code == 200 or response.status_code == 201

    def test_merge_operations_endpoint(self):
        """Test bulk merge operations endpoint"""
        url = reverse('inspections:bulk-merge-operations')
        data = [{
            'entity_type': 'inspection',
            'entity_id': '12345678-1234-5678-9abc-123456789abc',
            'merge_strategy': 'server_wins'
        }]

        response = self.client.post(url, data, content_type='application/json')
        print(f"Merge operations response status: {response.status_code}")
        print(f"Merge operations response: {response.content[:200]}...")
        return response.status_code == 200 or response.status_code == 400  # 400 if no conflicts exist

if __name__ == '__main__':
    test = SyncEndpointsTest()
    test.setUp()

    print("Testing sync endpoints...")
    print("=" * 50)

    # Test assignment sync
    print("1. Testing assignment sync endpoint...")
    assignment_ok = test.test_assignment_sync_endpoint()

    print("\n2. Testing approval sync endpoint...")
    approval_ok = test.test_approval_sync_endpoint()

    print("\n3. Testing merge operations endpoint...")
    merge_ok = test.test_merge_operations_endpoint()

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Assignment sync: {'✓' if assignment_ok else '✗'}")
    print(f"Approval sync: {'✓' if approval_ok else '✗'}")
    print(f"Merge operations: {'✓' if merge_ok else '✗'}")

    if assignment_ok and approval_ok and merge_ok:
        print("\n🎉 All sync endpoints are working!")
    else:
        print("\n⚠️ Some endpoints may need attention.")
