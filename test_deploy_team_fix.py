#!/usr/bin/env python
"""
Test script to verify that the deploy team functionality works without RelatedManager errors.
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
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore

from it.users.models import UserProfile
from fault_locator.views import deploy_team
from fault_locator.central_roles import is_senior_foreman, can_manage_devices

def test_deploy_team_permissions():
    """Test that deploy team permissions work without RelatedManager errors"""
    
    print("Testing deploy team permissions...")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Get a user profile (any user will do for testing)
    user_profile = UserProfile.objects.first()
    
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    print(f"✅ Testing with user profile: {user_profile.get_full_name()}")
    
    # Test permission functions directly
    try:
        print("Testing is_senior_foreman...")
        senior_result = is_senior_foreman(user_profile)
        print(f"✅ is_senior_foreman result: {senior_result}")
        
        print("Testing can_manage_devices...")
        devices_result = can_manage_devices(user_profile)
        print(f"✅ can_manage_devices result: {devices_result}")
        
        # Test with None user profile (should handle gracefully)
        print("Testing with None user profile...")
        none_senior = is_senior_foreman(None)
        none_devices = can_manage_devices(None)
        print(f"✅ None user profile handled: senior={none_senior}, devices={none_devices}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing permissions: {e}")
        return False

def test_deploy_team_view():
    """Test that deploy team view works without RelatedManager errors"""
    
    print("\nTesting deploy team view...")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Get a user profile
    user_profile = UserProfile.objects.first()
    
    if not user_profile:
        print("❌ No user profiles found.")
        return False
    
    try:
        # Create a mock request
        request = factory.get('/fault_locator/teams/deploy/')
        
        # Create a mock Django user object
        class MockUser:
            def __init__(self, user_profile):
                self.id = user_profile.id
                self.is_authenticated = True
                self.username = user_profile.username
        
        request.user = MockUser(user_profile)
        
        # Set up session and messages
        request.session = SessionStore()
        request.session.create()
        
        # Set up messages framework
        messages = FallbackStorage(request)
        request._messages = messages
        
        # Test the view
        print("Calling deploy_team view...")
        response = deploy_team(request)
        
        print(f"✅ Deploy team view executed successfully")
        print(f"Response status: {response.status_code if hasattr(response, 'status_code') else 'redirect'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing deploy team view: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing deploy team fixes...")
    print("=" * 50)
    
    # Test permission functions
    permissions_ok = test_deploy_team_permissions()
    
    # Test the view
    view_ok = test_deploy_team_view()
    
    print("\n" + "=" * 50)
    if permissions_ok and view_ok:
        print("✅ All tests passed! Deploy team functionality should work correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 50)
