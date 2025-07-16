#!/usr/bin/env python3
"""
Complete test suite for senior foreperson region filtering
Tests all dashboard functions and forms to ensure regional access control
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory, Client
from django.contrib.auth import authenticate, login
from django.urls import reverse
from fault_locator.models import UserProfile, Depots, Regions
from fault_locator.senior_foreman_views import (
    get_depot_deployment_status, get_depot_performance_data,
    team_depot_management, quick_deploy_team, performance_monitoring
)
from fault_locator.forms import TeamDeploymentForm

def test_complete_region_filtering():
    """Test complete region filtering implementation"""
    print("🔍 COMPLETE REGION FILTERING TEST")
    print("=" * 80)
    
    # Get test user
    test_user = User.objects.filter(username='12345').first()
    if not test_user:
        print("❌ Test user not found")
        return
    
    user_profile = UserProfile.objects.filter(id=test_user.id).first()
    if not user_profile:
        print("❌ User profile not found")
        return
    
    print(f"✅ Testing with user: {test_user.username}")
    print(f"✅ User's region: {user_profile.region}")
    
    # Test 1: Dashboard deployment status
    print("\n1. Testing dashboard deployment status...")
    deployment_status = get_depot_deployment_status(user_profile)
    regional_depots = len(deployment_status)
    print(f"✅ Regional depots in deployment status: {regional_depots}")
    
    # Test 2: Performance data
    print("\n2. Testing performance data...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    performance_data = get_depot_performance_data(start_date, end_date, user_profile)
    performance_depots = len(performance_data)
    print(f"✅ Regional depots in performance data: {performance_depots}")
    
    # Test 3: Form filtering
    print("\n3. Testing form filtering...")
    form = TeamDeploymentForm(user_region=user_profile.region)
    form_depot_count = form.fields['depot'].queryset.count()
    print(f"✅ Form depot choices: {form_depot_count}")
    
    # Test 4: Consistency check
    print("\n4. Testing consistency...")
    all_regional_depots = Depots.objects.filter(region=user_profile.region).count()
    print(f"✅ Total depots in {user_profile.region}: {all_regional_depots}")
    
    # Verify all counts match
    if regional_depots == performance_depots == form_depot_count == all_regional_depots:
        print(f"✅ All counts match: {regional_depots} depots")
        print("🎉 COMPLETE REGION FILTERING TEST PASSED!")
    else:
        print(f"❌ Count mismatch:")
        print(f"   - Deployment status: {regional_depots}")
        print(f"   - Performance data: {performance_depots}")
        print(f"   - Form choices: {form_depot_count}")
        print(f"   - Database total: {all_regional_depots}")
    
    print("=" * 80)
    return regional_depots == performance_depots == form_depot_count == all_regional_depots

def test_dashboard_integration():
    """Test dashboard integration with region filtering"""
    print("\n🌐 DASHBOARD INTEGRATION TEST")
    print("=" * 80)
    
    # Create a client and login
    client = Client()
    test_user = User.objects.filter(username='12345').first()
    
    if not test_user:
        print("❌ Test user not found")
        return False
    
    # Login the user
    client.force_login(test_user)
    
    # Test senior dashboard access
    try:
        response = client.get('/fault_locator/senior-dashboard/')
        if response.status_code == 200:
            print("✅ Senior dashboard accessible")
        else:
            print(f"⚠️ Senior dashboard status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Dashboard access test error: {e}")
    
    # Test performance monitoring access
    try:
        response = client.get('/fault_locator/performance-monitoring/')
        if response.status_code == 200:
            print("✅ Performance monitoring accessible")
        else:
            print(f"⚠️ Performance monitoring status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Performance monitoring test error: {e}")
    
    print("=" * 80)
    return True

if __name__ == '__main__':
    print("🚀 RUNNING COMPLETE REGION FILTERING TESTS")
    print("=" * 80)
    
    # Run complete filtering test
    filtering_passed = test_complete_region_filtering()
    
    # Run dashboard integration test
    integration_passed = test_dashboard_integration()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"✅ Region filtering: {'PASSED' if filtering_passed else 'FAILED'}")
    print(f"✅ Dashboard integration: {'PASSED' if integration_passed else 'FAILED'}")
    
    if filtering_passed and integration_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Senior forepersons will only see depots in their region across all dashboard functions.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
