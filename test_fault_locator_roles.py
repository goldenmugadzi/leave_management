#!/usr/bin/env python3
"""
Test script to verify fault locator role checking system
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile, Application, Roles
from fault_locator.central_roles import (
    FaultLocatorRoleManager,
    get_user_fault_locator_role,
    has_fault_locator_permissions,
    is_senior_foreman,
    is_depot_foreperson,
    is_team_leader,
    is_team_member
)

def test_role_system():
    """Test the fault locator role system"""
    
    print("=== FAULT LOCATOR ROLE SYSTEM TEST ===")
    print()
    
    # Test 1: Check if fault locator application exists
    print("1. Checking fault locator application...")
    try:
        fault_locator_app = Application.objects.filter(name='fault_locator').first()
        if fault_locator_app:
            print(f"   ✓ Found fault locator application: {fault_locator_app.name} ({fault_locator_app.fullname})")
        else:
            print("   ✗ Fault locator application not found!")
            return False
    except Exception as e:
        print(f"   ✗ Error checking application: {e}")
        return False
    
    # Test 2: Check available roles
    print("\n2. Checking available fault locator roles...")
    try:
        fault_locator_roles = Roles.objects.filter(application='fault_locator')
        if fault_locator_roles.exists():
            print(f"   ✓ Found {fault_locator_roles.count()} fault locator roles:")
            for role in fault_locator_roles:
                print(f"     - {role.role}: {role.name} ({role.description})")
        else:
            print("   ✗ No fault locator roles found!")
            return False
    except Exception as e:
        print(f"   ✗ Error checking roles: {e}")
        return False
    
    # Test 3: Check users with fault locator roles
    print("\n3. Checking users with fault locator roles...")
    try:
        users_with_roles = UserProfile.objects.filter(
            roles__application='fault_locator'
        ).distinct()
        
        if users_with_roles.exists():
            print(f"   ✓ Found {users_with_roles.count()} users with fault locator roles:")
            for user in users_with_roles:
                user_role = get_user_fault_locator_role(user)
                has_permissions = has_fault_locator_permissions(user)
                print(f"     - {user.username} ({user.first_name} {user.last_name}): {user_role} (Permissions: {has_permissions})")
        else:
            print("   ✗ No users found with fault locator roles!")
            return False
    except Exception as e:
        print(f"   ✗ Error checking users: {e}")
        return False
    
    # Test 4: Test role checking functions
    print("\n4. Testing role checking functions...")
    test_user = users_with_roles.first()
    if test_user:
        print(f"   Testing with user: {test_user.username}")
        print(f"   - get_user_fault_locator_role: {get_user_fault_locator_role(test_user)}")
        print(f"   - has_fault_locator_permissions: {has_fault_locator_permissions(test_user)}")
        print(f"   - is_senior_foreman: {is_senior_foreman(test_user)}")
        print(f"   - is_depot_foreperson: {is_depot_foreperson(test_user)}")
        print(f"   - is_team_leader: {is_team_leader(test_user)}")
        print(f"   - is_team_member: {is_team_member(test_user)}")
    
    print("\n=== TEST COMPLETE ===")
    return True

if __name__ == '__main__':
    try:
        success = test_role_system()
        if success:
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Some tests failed!")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
