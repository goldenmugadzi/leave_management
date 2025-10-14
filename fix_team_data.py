#!/usr/bin/env python3
"""
Fix Team Overview Data Issues
This script fixes timezone issues and cleans up team data.
"""

import os
import django
import sys
from datetime import datetime

# Add the project directory to the Python path
sys.path.append('d:\\b')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorTeam, FaultAssignment, Fault
from it.users.models import UserProfile
from django.utils import timezone
from django.db import transaction

def fix_team_data():
    print("=== FIXING TEAM OVERVIEW DATA ===")
    print()
    
    # 1. Fix timezone issues in FaultAssignment
    print("1. Fixing timezone issues...")
    fault_assignments = FaultAssignment.objects.filter(located_at__isnull=False)
    
    for assignment in fault_assignments:
        if assignment.located_at and assignment.located_at.tzinfo is None:
            # Convert naive datetime to timezone-aware
            assignment.located_at = timezone.make_aware(assignment.located_at)
            assignment.save()
            print(f"  Fixed timezone for assignment {assignment.id}")
    
    # 2. Clean up user profiles with empty names
    print("\n2. Cleaning up user profiles...")
    users = UserProfile.objects.all()
    
    for user in users:
        if not user.first_name and not user.last_name:
            # Try to extract name from email or username
            if user.email and '@' in user.email:
                username_part = user.email.split('@')[0]
                if '.' in username_part:
                    parts = username_part.split('.')
                    user.first_name = parts[0].title()
                    user.last_name = parts[1].title() if len(parts) > 1 else ''
                else:
                    user.first_name = username_part.title()
                user.save()
                print(f"  Fixed name for user {user.id}: {user.get_full_name()}")
            elif user.username:
                user.first_name = user.username.title()
                user.save()
                print(f"  Fixed name for user {user.id}: {user.get_full_name()}")
    
    # 3. Assign team leaders (first member becomes leader if no leader exists)
    print("\n3. Assigning team leaders...")
    teams = FaultLocatorTeam.objects.filter(team_leader__isnull=True)
    
    for team in teams:
        members = team.members.all()
        if members.exists():
            # Make the first member the team leader
            team.team_leader = members.first()
            team.save()
            print(f"  Assigned {team.team_leader.get_full_name()} as leader of team '{team.name}'")
    
    # 4. Check for duplicate team members
    print("\n4. Checking for duplicate team members...")
    teams = FaultLocatorTeam.objects.all()
    
    for team in teams:
        members = team.members.all()
        member_ids = [member.id for member in members]
        unique_member_ids = set(member_ids)
        
        if len(member_ids) != len(unique_member_ids):
            print(f"  Found duplicates in team '{team.name}' - cleaning up...")
            # Remove all members and re-add unique ones
            unique_members = list(set(members))
            team.members.clear()
            team.members.add(*unique_members)
            print(f"  Fixed duplicates for team '{team.name}' - now has {len(unique_members)} members")
    
    # 5. Update fault statuses
    print("\n5. Updating fault statuses...")
    # Check for faults that should be marked as located
    active_assignments = FaultAssignment.objects.filter(located_at__isnull=False)
    
    for assignment in active_assignments:
        if assignment.fault.status != 'located':
            assignment.fault.status = 'located'
            assignment.fault.save()
            print(f"  Updated fault {assignment.fault.id} status to 'located'")
    
    print("\n=== DATA CLEANUP COMPLETE ===")
    print()
    
    # 6. Verify fixes
    print("6. Verifying fixes...")
    teams = FaultLocatorTeam.objects.all()
    
    for team in teams:
        print(f"\nTeam: {team.name}")
        print(f"  Members: {team.members.count()}")
        print(f"  Leader: {team.team_leader.get_full_name() if team.team_leader else 'None'}")
        print(f"  Device: {'Yes' if team.faultlocatordeviceassignment_set.exists() else 'No'}")
        print(f"  Deployed: {'Yes' if team.current_depot else 'No'}")
        
        # Check active assignments
        active = FaultAssignment.objects.filter(team=team, located_at__isnull=True).count()
        print(f"  Active assignments: {active}")

if __name__ == "__main__":
    with transaction.atomic():
        fix_team_data()
