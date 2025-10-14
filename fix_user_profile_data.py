#!/usr/bin/env python3
import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorTeam, FaultLocatorDeviceAssignment, FaultAssignment, Fault
from it.users.models import UserProfile, Depots
from django.db.models import Count, Q

def fix_user_profile_data():
    """Fix any data issues in UserProfile that might affect team overview"""
    print("=== FIXING USER PROFILE DATA ===")
    
    # Check all users involved in fault locator teams
    team_members = UserProfile.objects.filter(
        fault_locator_teams__isnull=False
    ).distinct()
    
    team_leaders = UserProfile.objects.filter(
        led_teams__isnull=False
    ).distinct()
    
    all_users = (team_members | team_leaders).distinct()
    
    print(f"Found {all_users.count()} users involved in fault locator teams")
    print()
    
    fixed_count = 0
    
    for user in all_users:
        print(f"Checking user: {user.username}")
        
        # Check name fields
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        
        print(f"  First name: '{first_name}'")
        print(f"  Last name: '{last_name}'")
        print(f"  Email: '{user.email}'")
        print(f"  get_full_name(): '{user.get_full_name()}'")
        print(f"  __str__(): '{str(user)}'")
        
        # Check if names are empty or problematic
        needs_fix = False
        
        # Fix empty names by trying to extract from username or email
        if not first_name.strip() and not last_name.strip():
            print(f"  ⚠️  User has no name data")
            
            # Try to extract name from email
            if user.email and '@' in user.email:
                email_name = user.email.split('@')[0]
                if '.' in email_name:
                    parts = email_name.split('.')
                    if len(parts) >= 2:
                        user.first_name = parts[0].title()
                        user.last_name = parts[1].title()
                        needs_fix = True
                        print(f"  ✓ Extracted name from email: {user.first_name} {user.last_name}")
                elif email_name:
                    user.first_name = email_name.title()
                    needs_fix = True
                    print(f"  ✓ Extracted first name from email: {user.first_name}")
        
        # Fix email issues
        if user.email:
            email_str = str(user.email).strip()
            if email_str.lower() == 'nan' or email_str == 'None':
                user.email = ""
                needs_fix = True
                print(f"  ✓ Fixed problematic email value")
        
        # Save if needed
        if needs_fix:
            user.save()
            fixed_count += 1
            print(f"  ✅ Fixed user data")
        else:
            print(f"  ✓ User data is OK")
        
        print()
    
    print(f"Fixed {fixed_count} users")
    
    # Now test the team overview logic again
    print("\n=== TESTING TEAM OVERVIEW AFTER FIXES ===")
    teams = FaultLocatorTeam.objects.all()
    
    for team in teams:
        print(f"Team: {team.name}")
        
        # Team leader
        if team.team_leader:
            leader_name = team.team_leader.get_full_name()
            if leader_name and leader_name.strip():
                display_name = leader_name.strip()
            else:
                display_name = team.team_leader.username or f"User {team.team_leader.id}"
            print(f"  Leader: {display_name}")
        else:
            print(f"  Leader: None")
        
        # Members
        print(f"  Members:")
        for member in team.members.all():
            member_name = member.get_full_name()
            if not member_name or member_name.strip() == '':
                member_name = member.username or f"User {member.id}"
            else:
                member_name = member_name.strip()
            
            # Handle member email
            member_email = 'No email'
            if member.email:
                email_str = str(member.email).strip()
                if email_str and email_str.lower() != 'nan' and email_str != 'None':
                    member_email = email_str
            
            print(f"    - {member_name} ({member_email})")
        
        print()

if __name__ == "__main__":
    fix_user_profile_data()
