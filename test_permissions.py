#!/usr/bin/env python
"""
Test script to check user permissions for fault locator system
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile
from django.db import models
from fault_locator.views import is_senior_foreman, can_manage_devices, can_deploy_teams

def test_user_permissions(username):
    """Test permissions for a specific user"""
    print(f"\n=== Testing permissions for user: {username} ===")
    
    try:
        user_profile = UserProfile.objects.get(username=username)
        print(f"User found: {user_profile.get_full_name()}")
        
        if hasattr(user_profile, 'designation') and user_profile.designation:
            print(f"Designation: {user_profile.designation.description}")
        else:
            print("Designation: Not set")
        
        if hasattr(user_profile, 'section') and user_profile.section:
            print(f"Section: {user_profile.section.section}")
        else:
            print("Section: Not set")
        
        # Test permission functions
        print(f"\nPermission checks:")
        print(f"- is_senior_foreman: {is_senior_foreman(user_profile)}")
        print(f"- can_manage_devices: {can_manage_devices(user_profile)}")
        print(f"- can_deploy_teams: {can_deploy_teams(user_profile)}")
        
        # Check if user can recall teams
        can_recall = is_senior_foreman(user_profile) or can_manage_devices(user_profile)
        print(f"- can_recall_teams: {can_recall}")
        
    except UserProfile.DoesNotExist:
        print(f"User '{username}' not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # List all users first
    print("=== All users in system ===")
    users = UserProfile.objects.all()[:10]  # First 10 users
    for user in users:
        print(f"Username: {user.username}, Name: {user.get_full_name()}")
    
    print("\n=== Looking for Ashley ===")
    ashley_users = UserProfile.objects.filter(
        models.Q(username__icontains='ashley') | 
        models.Q(first_name__icontains='ashley') |
        models.Q(last_name__icontains='mugwambi')
    )
    for user in ashley_users:
        print(f"Found: {user.username} - {user.get_full_name()}")
        test_user_permissions(user.username)
