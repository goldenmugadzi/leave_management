#!/usr/bin/env python
"""
Test script to simulate the actual deploy_team web request that causes the RelatedManager error.
"""

import os
import sys
import requests

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

import django
django.setup()

# Now import Django modules
from django.test import Client
from django.contrib.auth import login
from it.users.models import UserProfile
from fault_locator.central_roles import FaultLocatorRoleManager

def test_deploy_team_web_request():
    """Test the actual deploy_team web request"""
    
    print("🔍 Testing deploy_team web request...")
    
    # Get a user profile with senior foreperson role
    user_profile = UserProfile.objects.first()
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    # Ensure user has senior foreperson role
    FaultLocatorRoleManager.assign_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)
    
    print(f"✅ Testing with user profile: {user_profile.get_full_name()}")
    
    # Create a client
    client = Client()
    
    # Try to force login the user
    client.force_login(user_profile)
    
    # Make the actual request
    try:
        print("📡 Making GET request to /fault_locator/deploy_team/")
        response = client.get('/fault_locator/deploy_team/')
        
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            return True
        elif response.status_code == 302:
            print("⚠️ Request redirected (likely authentication or permission issue)")
            print(f"Redirect location: {response.get('Location', 'Unknown')}")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error making request: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing deploy_team Web Request")
    print("=" * 60)
    
    # Test the web request
    success = test_deploy_team_web_request()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Web request test passed!")
    else:
        print("❌ Web request test failed.")
        print("Check the Django server console for error messages.")
    
    print("=" * 60)
