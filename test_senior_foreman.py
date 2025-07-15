#!/usr/bin/env python
"""
Test script to verify Senior Foreman views are working
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from it.users.models import UserProfile
from fault_locator.models import *
from fault_locator.senior_foreman_views import *

def test_senior_foreman_dashboard():
    """Test that the Senior Foreman dashboard loads correctly"""
    
    # Create a test user
    user = User.objects.create_user(
        username='test_senior',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create user profile
    user_profile = UserProfile.objects.create(
        user=user,
        first_name='Test',
        last_name='Senior',
        depot='A',
        designation_id=1  # Assuming designation exists
    )
    
    # Create request factory
    factory = RequestFactory()
    
    # Test dashboard view
    request = factory.get('/fault_locator/senior-dashboard/')
    request.user = user
    
    try:
        response = senior_foreman_dashboard(request)
        print("✅ Senior Foreman Dashboard: OK")
        print(f"   Response status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Senior Foreman Dashboard: ERROR - {e}")
        return False

def test_team_depot_management():
    """Test team depot management view"""
    
    # Create a test user
    user = User.objects.create_user(
        username='test_senior2',
        email='test2@example.com',
        password='testpass123'
    )
    
    # Create user profile
    user_profile = UserProfile.objects.create(
        user=user,
        first_name='Test',
        last_name='Senior2',
        depot='A',
        designation_id=1  # Assuming designation exists
    )
    
    # Create request factory
    factory = RequestFactory()
    
    # Test team depot management view
    request = factory.get('/fault_locator/team-depot-management/')
    request.user = user
    
    try:
        response = team_depot_management(request)
        print("✅ Team Depot Management: OK")
        print(f"   Response status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Team Depot Management: ERROR - {e}")
        return False

def test_device_team_management():
    """Test device team management view"""
    
    # Create a test user
    user = User.objects.create_user(
        username='test_senior3',
        email='test3@example.com',
        password='testpass123'
    )
    
    # Create user profile
    user_profile = UserProfile.objects.create(
        user=user,
        first_name='Test',
        last_name='Senior3',
        depot='A',
        designation_id=1  # Assuming designation exists
    )
    
    # Create request factory
    factory = RequestFactory()
    
    # Test device team management view
    request = factory.get('/fault_locator/device-team-management/')
    request.user = user
    
    try:
        response = device_team_management(request)
        print("✅ Device Team Management: OK")
        print(f"   Response status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Device Team Management: ERROR - {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring view"""
    
    # Create a test user
    user = User.objects.create_user(
        username='test_senior4',
        email='test4@example.com',
        password='testpass123'
    )
    
    # Create user profile
    user_profile = UserProfile.objects.create(
        user=user,
        first_name='Test',
        last_name='Senior4',
        depot='A',
        designation_id=1  # Assuming designation exists
    )
    
    # Create request factory
    factory = RequestFactory()
    
    # Test performance monitoring view
    request = factory.get('/fault_locator/performance-monitoring/')
    request.user = user
    
    try:
        response = performance_monitoring(request)
        print("✅ Performance Monitoring: OK")
        print(f"   Response status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Performance Monitoring: ERROR - {e}")
        return False

if __name__ == '__main__':
    print("Testing Senior Foreman Views...")
    print("=" * 50)
    
    results = []
    results.append(test_senior_foreman_dashboard())
    results.append(test_team_depot_management())
    results.append(test_device_team_management())
    results.append(test_performance_monitoring())
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All Senior Foreman views are working correctly!")
    else:
        print("\n⚠️  Some views need attention.")
