#!/usr/bin/env python3
"""
Test script to verify that the assignment acceptance endpoint now works correctly
without requiring officer_id in the request body.
"""

import os
import django
import sys
from django.conf import settings

# Setup Django environment
sys.path.append('/var/www/beii_v1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from inspections.models import ClientApplication, ApplicationAssignment, Customer, Contractor
from inspections.mobile_api_views import accept_assignment

User = get_user_model()
import json
from datetime import datetime, timedelta
from django.utils import timezone


def test_assignment_acceptance():
    """Test that assignment acceptance works without officer_id in request body"""
    print("🧪 Testing assignment acceptance fix...")
    
    # Create test data
    try:
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='test_inspector',
            defaults={
                'first_name': 'Test',
                'last_name': 'Inspector',
                'email': 'test@example.com'
            }
        )
        print(f"✅ Test user: {user.username} (ID: {user.id})")

        # Create or get test customer
        customer, created = Customer.objects.get_or_create(
            customer_id='TEST001',
            defaults={
                'full_name': 'Test Customer',
                'phone': '0771234567',
                'email': 'customer@test.com',
                'stand_plot_number': '123',
                'farm_street_name': 'Test Street',
                'suburb_township': 'Test Township',
                'district': 'Test District'
            }
        )
        print(f"✅ Test customer: {customer.full_name}")

        # Create or get test contractor
        contractor, created = Contractor.objects.get_or_create(
            contractor_id='CONT001',
            defaults={
                'business_name': 'Test Contractor Ltd',
                'contact_person': 'John Doe',
                'phone': '0779876543',
                'email': 'contractor@test.com',
                'address': 'Test Address',
                'license_number': 'LIC001',
                'business_registration': 'REG001'
            }
        )
        print(f"✅ Test contractor: {contractor.business_name}")

        # Create test application
        application = ClientApplication.objects.create(
            application_number='APP-TEST-001',
            application_type='new_connection',
            priority='medium',
            customer=customer,
            contractor=contractor,
            purpose='Residential connection',
            supply_type='domestic',
            status='assigned',
            notes='Test application for acceptance'
        )
        print(f"✅ Test application: {application.application_number}")

        # Create assignment
        assignment = ApplicationAssignment.objects.create(
            application=application,
            assigned_to=user,
            due_date=timezone.now() + timedelta(days=7),
            status='assigned'
        )
        print(f"✅ Test assignment: {assignment.id} (Status: {assignment.status})")

        # Test the API endpoint
        factory = APIRequestFactory()
        
        # Test with empty request body (like the mobile app was sending)
        request = factory.post(
            f'/inspections/api/v1/applications/{application.id}/accept/',
            data={},  # Empty body like in the error log
            format='json'
        )
        force_authenticate(request, user=user)

        # Call the view function
        response = accept_assignment(request, application.id)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {json.dumps(response.data, indent=2)}")

        # Check results
        assignment.refresh_from_db()
        application.refresh_from_db()
        
        if response.status_code == 200:
            print("✅ SUCCESS: Assignment acceptance worked!")
            print(f"✅ Assignment status: {assignment.status}")
            print(f"✅ Application status: {application.status}")
            print(f"✅ Accepted date: {assignment.accepted_date}")
            
            if assignment.status == 'accepted':
                print("🎉 Assignment was properly accepted!")
                return True
            else:
                print("❌ Assignment status was not updated to 'accepted'")
                return False
        else:
            print(f"❌ FAILED: {response.data}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_assignment_acceptance_with_data():
    """Test assignment acceptance with some optional data"""
    print("\n🧪 Testing assignment acceptance with optional data...")
    
    try:
        # Get existing test data
        user = User.objects.get(username='test_inspector')
        customer = Customer.objects.get(customer_id='TEST001')
        contractor = Contractor.objects.get(contractor_id='CONT001')

        # Create another test application
        application = ClientApplication.objects.create(
            application_number='APP-TEST-002',
            application_type='new_connection',
            priority='high',
            customer=customer,
            contractor=contractor,
            purpose='Commercial connection',
            supply_type='commercial',
            status='assigned',
            notes='Test application with data'
        )

        # Create assignment
        assignment = ApplicationAssignment.objects.create(
            application=application,
            assigned_to=user,
            due_date=timezone.now() + timedelta(days=5),
            status='assigned'
        )

        # Test with some optional data
        factory = APIRequestFactory()
        request_data = {
            'notes': 'Accepted for inspection',
            'estimated_completion': (timezone.now() + timedelta(days=3)).isoformat()
        }
        
        request = factory.post(
            f'/inspections/api/v1/applications/{application.id}/accept/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=user)

        # Call the view function
        response = accept_assignment(request, application.id)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {json.dumps(response.data, indent=2)}")

        if response.status_code == 200:
            print("✅ SUCCESS: Assignment acceptance with data worked!")
            return True
        else:
            print(f"❌ FAILED: {response.data}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("🚀 Starting assignment acceptance tests...\n")
    
    test1_passed = test_assignment_acceptance()
    test2_passed = test_assignment_acceptance_with_data()
    
    print(f"\n📋 Test Results:")
    print(f"   Test 1 (Empty request body): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Test 2 (With optional data): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The assignment acceptance fix is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
