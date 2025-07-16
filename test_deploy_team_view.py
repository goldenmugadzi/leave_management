#!/usr/bin/env python
"""
Test script to verify that the deploy_team view works correctly for senior foreperson.
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
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages import get_messages
from it.users.models import UserProfile, Roles, Application
from fault_locator.central_roles import FaultLocatorRoleManager
from fault_locator.views import deploy_team

def test_deploy_team_view():
    """Test that deploy_team view works for senior foreperson"""
    
    print("Testing deploy_team view for senior foreperson...")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Get a user profile with senior foreperson role
    user_profile = UserProfile.objects.first()
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    # Ensure user has senior foreperson role
    FaultLocatorRoleManager.assign_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass')
    
    # Create GET request
    request = factory.get('/fault_locator/deploy_team/')
    request.user = user
    
    # Add session and messages middleware
    SessionMiddleware(lambda x: None).process_request(request)
    MessageMiddleware(lambda x: None).process_request(request)
    
    # Set the user profile
    request.user.userprofile = user_profile
    
    try:
        # Call the view
        response = deploy_team(request)
        
        if response.status_code == 200:
            print("✅ deploy_team view returned 200 OK")
            return True
        else:
            print(f"❌ deploy_team view returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error calling deploy_team view: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing deploy_team view for senior foreperson...")
    print("=" * 60)
    
    # Test deploy_team view
    view_ok = test_deploy_team_view()
    
    print("\n" + "=" * 60)
    if view_ok:
        print("✅ deploy_team view tests passed!")
    else:
        print("❌ deploy_team view tests failed.")
    
    print("=" * 60)
