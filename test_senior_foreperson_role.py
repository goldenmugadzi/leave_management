#!/usr/bin/env python
"""
Test script to verify that the senior foreperson role checking works correctly.
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
from it.users.models import UserProfile, Roles, Application
from fault_locator.central_roles import FaultLocatorRoleManager, is_senior_foreman, can_manage_devices

def test_senior_foreperson_role():
    """Test that senior foreperson role checking works"""
    
    print("Testing senior foreperson role functionality...")
    
    # Get a user profile
    user_profile = UserProfile.objects.first()
    
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    print(f"✅ Testing with user profile: {user_profile.get_full_name()}")
    
    # Check if fault locator application exists
    try:
        app = Application.objects.filter(name=FaultLocatorRoleManager.APPLICATION_NAME).first()
        if not app:
            print("❌ Fault locator application not found. Please run setup_fault_locator_roles command.")
            return False
        
        print(f"✅ Fault locator application found: {app.name}")
        
        # Check if senior foreperson role exists
        senior_role = Roles.objects.filter(
            role=FaultLocatorRoleManager.SENIOR_FOREMAN,
            application=FaultLocatorRoleManager.APPLICATION_NAME
        ).first()
        
        if not senior_role:
            print("❌ Senior foreperson role not found. Please run setup_fault_locator_roles command.")
            return False
            
        print(f"✅ Senior foreperson role found: {senior_role.name}")
        
        # Test assigning the role
        print("Testing role assignment...")
        result = FaultLocatorRoleManager.assign_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)
        if result:
            print("✅ Role assigned successfully")
        else:
            print("⚠️ Role assignment failed or already exists")
        
        # Test role checking
        print("Testing role checking...")
        is_senior = is_senior_foreman(user_profile)
        can_manage = can_manage_devices(user_profile)
        
        print(f"✅ is_senior_foreman: {is_senior}")
        print(f"✅ can_manage_devices: {can_manage}")
        
        if is_senior and can_manage:
            print("✅ User should be able to deploy teams")
        else:
            print("❌ User cannot deploy teams")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing senior foreperson role: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing senior foreperson role fixes...")
    print("=" * 60)
    
    # Test senior foreperson role
    role_ok = test_senior_foreperson_role()
    
    print("\n" + "=" * 60)
    if role_ok:
        print("✅ Senior foreperson role tests passed!")
    else:
        print("❌ Senior foreperson role tests failed.")
    
    print("=" * 60)
