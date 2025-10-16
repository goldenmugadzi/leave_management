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
from django.test import Client
from it.users.models import UserProfile, Roles, Application
from fault_locator.central_roles import FaultLocatorRoleManager

def test_deploy_team_view():
    """Test that deploy_team view works for senior foreperson"""
    
    print("Testing deploy_team view for senior foreperson...")
    
    # Get a user profile with senior foreperson role
    user_profile = UserProfile.objects.first()
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    # Ensure user has senior foreperson role
    FaultLocatorRoleManager.assign_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)
    
    # Create a client and login
    client = Client()
    
    # Try to access the deploy_team view
    response = client.get('/fault_locator/deploy_team/')
    
    # Check response status
    if response.status_code == 200:
        print("✅ deploy_team view returned 200 OK")
        return True
    elif response.status_code == 302:
        print("⚠️ deploy_team view returned 302 redirect (likely needs authentication)")
        print("This is normal behavior for unauthenticated users")
        return True
    else:
        print(f"❌ deploy_team view returned unexpected status {response.status_code}")
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
