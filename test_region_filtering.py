#!/usr/bin/env python
"""
Test script to verify that senior forepersons only see depots in their region.
"""

import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

import django
django.setup()

# Now import Django modules
from it.users.models import UserProfile, Depots, Regions
from fault_locator.senior_foreman_views import get_depot_deployment_status, get_depot_performance_data
from fault_locator.central_roles import FaultLocatorRoleManager
from datetime import datetime, timedelta

def test_region_filtering():
    """Test that depot filtering by region works correctly"""
    
    print("🔍 Testing region filtering for senior forepersons...")
    
    # Get a user profile with senior foreperson role
    user_profile = UserProfile.objects.first()
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    # Ensure user has senior foreperson role
    FaultLocatorRoleManager.assign_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)
    
    print(f"✅ Testing with user profile: {user_profile.get_full_name()}")
    
    # Check user's region
    if user_profile.region:
        print(f"✅ User's region: {user_profile.region}")
    else:
        print("⚠️ User has no region assigned. This may affect filtering.")
    
    # Test get_depot_deployment_status with region filtering
    print("\n1. Testing get_depot_deployment_status with region filtering...")
    try:
        # Without region filtering (should return all depots)
        all_depots = get_depot_deployment_status()
        print(f"✅ Total depots (no filtering): {all_depots.count()}")
        
        # With region filtering
        regional_depots = get_depot_deployment_status(user_profile)
        print(f"✅ Regional depots (with filtering): {regional_depots.count()}")
        
        # Show depot details
        print("\n📍 Depots in user's region:")
        for depot in regional_depots:
            print(f"   - {depot.depot} (Region: {depot.region})")
        
        if user_profile.region:
            # Verify all returned depots are in the user's region
            wrong_region_depots = regional_depots.exclude(region=user_profile.region)
            if wrong_region_depots.exists():
                print(f"❌ Found {wrong_region_depots.count()} depots NOT in user's region!")
                return False
            else:
                print("✅ All depots are correctly filtered by region")
        
    except Exception as e:
        print(f"❌ Error testing get_depot_deployment_status: {e}")
        return False
    
    # Test get_depot_performance_data with region filtering
    print("\n2. Testing get_depot_performance_data with region filtering...")
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Without region filtering
        all_performance = get_depot_performance_data(start_date, end_date)
        print(f"✅ Total depots in performance data (no filtering): {all_performance.count()}")
        
        # With region filtering
        regional_performance = get_depot_performance_data(start_date, end_date, user_profile)
        print(f"✅ Regional depots in performance data (with filtering): {regional_performance.count()}")
        
        if user_profile.region:
            # Verify all returned depots are in the user's region
            wrong_region_performance = regional_performance.exclude(region=user_profile.region)
            if wrong_region_performance.exists():
                print(f"❌ Found {wrong_region_performance.count()} performance depots NOT in user's region!")
                return False
            else:
                print("✅ All performance depots are correctly filtered by region")
        
    except Exception as e:
        print(f"❌ Error testing get_depot_performance_data: {e}")
        return False
    
    # Test region data consistency
    print("\n3. Testing region data consistency...")
    try:
        # Check if regions exist
        regions = Regions.objects.all()
        print(f"✅ Total regions in system: {regions.count()}")
        
        # Check depot distribution by region
        for region in regions:
            depot_count = Depots.objects.filter(region=region).count()
            print(f"   - {region.region}: {depot_count} depots")
        
        # Check users by region
        if user_profile.region:
            users_in_region = UserProfile.objects.filter(region=user_profile.region).count()
            print(f"✅ Users in {user_profile.region}: {users_in_region}")
        
    except Exception as e:
        print(f"❌ Error checking region data: {e}")
        return False
    
    print("\n✅ All region filtering tests passed!")
    return True


def test_form_filtering():
    """Test that forms properly filter by region"""
    
    print("\n🔍 Testing form region filtering...")
    
    user_profile = UserProfile.objects.first()
    if not user_profile or not user_profile.region:
        print("⚠️ Skipping form test - no user profile or region available")
        return True
    
    try:
        from fault_locator.forms import TeamDeploymentForm
        
        # Test form with user region
        form = TeamDeploymentForm(user_region=user_profile.region)
        depot_queryset = form.fields['depot'].queryset
        
        print(f"✅ Form depot choices (with region): {depot_queryset.count()}")
        
        # Verify all depots are in the user's region
        wrong_region_depots = depot_queryset.exclude(region=user_profile.region)
        if wrong_region_depots.exists():
            print(f"❌ Form has {wrong_region_depots.count()} depots NOT in user's region!")
            return False
        else:
            print("✅ Form correctly filters depots by region")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing form filtering: {e}")
        return False


if __name__ == "__main__":
    print("🚀 TESTING REGION FILTERING FOR SENIOR FOREPERSONS")
    print("=" * 80)
    
    # Test region filtering
    filtering_ok = test_region_filtering()
    
    # Test form filtering
    form_ok = test_form_filtering()
    
    print("\n" + "=" * 80)
    if filtering_ok and form_ok:
        print("🎉 SUCCESS: All region filtering tests passed!")
        print("Senior forepersons will only see depots in their region.")
    else:
        print("❌ FAILURE: Some region filtering tests failed.")
        print("Please review the errors above.")
    
    print("=" * 80)
