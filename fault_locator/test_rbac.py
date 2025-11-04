"""
Test script to verify role-based access control implementation.
Run this script to check if the central roles integration is working correctly.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from it.users.models import UserProfile, Application, Roles
from fault_locator.central_roles import FaultLocatorRoleManager
from fault_locator.models import FaultLocatorTeam, Fault

def test_role_based_access():
    """Test role-based access control functionality."""
    
    print("Testing Fault Locator Role-Based Access Control")
    print("=" * 50)
    
    # Test 1: Check if fault locator application exists
    try:
        app = Application.objects.get(name='Fault Locator')
        print(f"✓ Fault Locator application found: {app}")
    except Application.DoesNotExist:
        print("✗ Fault Locator application not found. Run setup_fault_locator_roles command first.")
        return False
    
    # Test 2: Check if roles exist
    expected_roles = ['senior_foreman', 'depot_foreperson', 'team_leader', 'team_member']
    for role_name in expected_roles:
        try:
            role = Roles.objects.get(application=app, role=role_name)
            print(f"✓ Role '{role_name}' found: {role.name}")
        except Roles.DoesNotExist:
            print(f"✗ Role '{role_name}' not found")
            return False
    
    # Test 3: Test role manager functionality
    print("\nTesting FaultLocatorRoleManager:")
    
    # Create test user
    test_user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    user_profile = UserProfile.objects.create(
        user=test_user,
        staff_id='TEST001',
        first_name='Test',
        last_name='User'
    )
    
    # Test role assignment
    senior_role = Roles.objects.get(application=app, role='senior_foreman')
    FaultLocatorRoleManager.assign_role(user_profile, 'senior_foreman')
    
    # Test role checking
    user_role = FaultLocatorRoleManager.get_user_role(user_profile)
    print(f"✓ User role detected: {user_role}")
    
    # Test permissions
    from fault_locator.central_roles import (
        is_senior_foreman, can_assign_faults, can_manage_devices
    )
    
    if is_senior_foreman(user_profile):
        print("✓ Senior foreman permission check passed")
    else:
        print("✗ Senior foreman permission check failed")
    
    if can_assign_faults(user_profile):
        print("✓ Assign faults permission check passed")
    else:
        print("✗ Assign faults permission check failed")
    
    if can_manage_devices(user_profile):
        print("✓ Manage devices permission check passed")
    else:
        print("✗ Manage devices permission check failed")
    
    # Test 4: Test dashboard access
    print("\nTesting Dashboard Access:")
    
    client = Client()
    client.login(username='testuser', password='testpass123')
    
    try:
        response = client.get('/fault_locator/dashboard/')
        if response.status_code == 200:
            print("✓ Dashboard accessible with role-based authentication")
        else:
            print(f"✗ Dashboard access failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Dashboard access error: {e}")
    
    # Cleanup
    test_user.delete()
    
    print("\n" + "=" * 50)
    print("Role-based access control test completed!")
    
    return True

if __name__ == '__main__':
    # This would need to be run in Django shell or as a management command
    print("This test script should be run in Django shell:")
    print("python manage.py shell")
    print("exec(open('fault_locator/test_rbac.py').read())")
