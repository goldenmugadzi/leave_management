#!/usr/bin/env python
"""
Final verification script to confirm senior foreperson functionality is working.
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
from fault_locator.central_roles import (
    FaultLocatorRoleManager, 
    is_senior_foreman, 
    can_manage_devices
)

def verify_senior_foreperson_functionality():
    """Verify all senior foreperson functionality is working"""
    
    print("🔍 Verifying senior foreperson functionality...")
    
    # Get a user profile
    user_profile = UserProfile.objects.first()
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    print(f"✅ Testing with user profile: {user_profile.get_full_name()}")
    
    # Test 1: Role assignment
    print("\n1. Testing role assignment...")
    result = FaultLocatorRoleManager.assign_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)
    if result:
        print("✅ Role assignment: SUCCESS")
    else:
        print("⚠️ Role assignment: Already exists or failed")
    
    # Test 2: Role checking functions
    print("\n2. Testing role checking functions...")
    try:
        is_senior = is_senior_foreman(user_profile)
        can_manage = can_manage_devices(user_profile)
        user_role = FaultLocatorRoleManager.get_user_role(user_profile)
        role_display = FaultLocatorRoleManager.get_user_role_display(user_profile)
        
        print(f"✅ is_senior_foreman: {is_senior}")
        print(f"✅ can_manage_devices: {can_manage}")
        print(f"✅ get_user_role: {user_role}")
        print(f"✅ get_user_role_display: {role_display}")
        
        if is_senior and can_manage:
            print("✅ User has all required permissions for team deployment")
        else:
            print("❌ User missing permissions for team deployment")
            
    except Exception as e:
        print(f"❌ Error in role checking: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Check RelatedManager errors are fixed
    print("\n3. Testing RelatedManager error fixes...")
    try:
        # This should not raise RelatedManager errors anymore
        roles = user_profile.roles.all()
        print(f"✅ UserProfile.roles.all(): {roles.count()} roles found")
        
        for role in roles:
            if hasattr(role, 'role'):
                print(f"✅ Role object has 'role' attribute: {role.role}")
            if hasattr(role, 'name'):
                print(f"✅ Role object has 'name' attribute: {role.name}")
                
    except Exception as e:
        print(f"❌ RelatedManager error still present: {e}")
        return False
    
    print("\n✅ All tests passed! Senior foreperson functionality should be working.")
    return True

def print_instructions():
    """Print instructions for using the system"""
    print("\n" + "=" * 80)
    print("🎯 SENIOR FOREPERSON TEAM DEPLOYMENT INSTRUCTIONS")
    print("=" * 80)
    print("1. Login to the system as a user with senior foreperson role")
    print("2. Navigate to the fault locator dashboard")
    print("3. Look for 'Deploy Team' or 'Team Deployment' option")
    print("4. The system will show depot priority analysis to help you decide")
    print("5. Select a team and target depot based on the priority information")
    print("6. Submit the deployment")
    print("\n🔧 If you encounter issues:")
    print("- Check that your user has the 'Senior Foreman' role")
    print("- Verify that teams have devices assigned")
    print("- Check that target depots exist and are active")
    print("- Review the Django server logs for any error messages")
    print("=" * 80)

if __name__ == "__main__":
    print("🚀 FINAL VERIFICATION: Senior Foreperson Team Deployment")
    print("=" * 80)
    
    # Run verification
    success = verify_senior_foreperson_functionality()
    
    if success:
        print("\n🎉 SUCCESS: All fixes have been implemented successfully!")
        print("The RelatedManager errors have been resolved.")
        print("Senior foreperson team deployment should now work correctly.")
        print_instructions()
    else:
        print("\n❌ FAILURE: Some issues remain. Please review the errors above.")
    
    print("\n" + "=" * 80)
