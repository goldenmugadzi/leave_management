#!/usr/bin/env python
"""
Test script to verify fault reporter depot restrictions are working correctly.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'it.settings')
django.setup()

from it.users.models import UserProfile, Depots
from fault_locator.central_roles import (
    is_fault_reporter,
    can_report_faults,
    assign_fault_locator_role,
    FaultLocatorRoleManager
)

def test_depot_restrictions():
    print("Testing Fault Reporter Depot Restrictions")
    print("=" * 50)
    
    # Get a test user (replace with actual username)
    test_username = input("Enter a test username to check (or press Enter to skip): ").strip()
    
    if not test_username:
        print("No username provided. Creating test scenario...")
        return
    
    try:
        user_profile = UserProfile.objects.get(username=test_username)
        print(f"Testing user: {user_profile.get_full_name()} ({user_profile.username})")
        
        # Check current depot assignment
        if hasattr(user_profile, 'depot') and user_profile.depot:
            print(f"User's assigned depot: {user_profile.depot.depot}")
        else:
            print("User has no depot assigned")
        
        # Check if user is fault reporter
        is_fault_rep = is_fault_reporter(user_profile)
        print(f"Is fault reporter: {is_fault_rep}")
        
        if is_fault_rep:
            # Test depot-specific permissions
            print("\nTesting depot-specific permissions:")
            
            # Test with user's own depot
            if hasattr(user_profile, 'depot') and user_profile.depot:
                can_report_own = can_report_faults(user_profile, user_profile.depot)
                print(f"Can report faults for own depot ({user_profile.depot.depot}): {can_report_own}")
            
            # Test with other depots
            other_depots = Depots.objects.exclude(id=user_profile.depot.id if user_profile.depot else None)[:3]
            for depot in other_depots:
                can_report_other = can_report_faults(user_profile, depot)
                print(f"Can report faults for {depot.depot}: {can_report_other}")
        
        print("\nFault reporter role requirements:")
        print("- Must be assigned a depot")
        print("- Can only report faults for their assigned depot")
        print("- Cannot report faults for other depots")
        
    except UserProfile.DoesNotExist:
        print(f"User '{test_username}' not found")
    except Exception as e:
        print(f"Error: {e}")

def show_fault_reporter_info():
    print("\nFault Reporter Role Information")
    print("=" * 40)
    
    # Show fault reporters and their depots
    fault_reporters = FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.FAULT_REPORTER)
    
    if fault_reporters.exists():
        print("Current fault reporters:")
        for user in fault_reporters:
            depot_info = user.depot.depot if (hasattr(user, 'depot') and user.depot) else "No depot assigned"
            print(f"- {user.get_full_name()} ({user.username}) - Depot: {depot_info}")
    else:
        print("No fault reporters found")

if __name__ == '__main__':
    print("Fault Reporter Depot Restriction Test")
    print("=====================================\n")
    
    show_fault_reporter_info()
    print()
    test_depot_restrictions()
    
    print("\nTest completed!")
