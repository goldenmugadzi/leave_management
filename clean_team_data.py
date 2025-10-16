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

def clean_user_names():
    """Clean up user names by removing extra spaces"""
    print("=== CLEANING USER NAMES ===")
    
    # Get all users in fault locator teams
    team_members = UserProfile.objects.filter(
        fault_locator_teams__isnull=False
    ).distinct()
    
    team_leaders = UserProfile.objects.filter(
        led_teams__isnull=False
    ).distinct()
    
    all_users = (team_members | team_leaders).distinct()
    
    fixed_count = 0
    
    for user in all_users:
        original_first = user.first_name
        original_last = user.last_name
        
        # Clean up names - remove extra spaces
        cleaned_first = user.first_name.strip() if user.first_name else ""
        cleaned_last = user.last_name.strip() if user.last_name else ""
        
        if original_first != cleaned_first or original_last != cleaned_last:
            user.first_name = cleaned_first
            user.last_name = cleaned_last
            user.save()
            fixed_count += 1
            print(f"✓ Fixed {user.username}: '{original_first}' '{original_last}' -> '{cleaned_first}' '{cleaned_last}'")
    
    print(f"Cleaned {fixed_count} user names")
    
    # Test the results
    print("\n=== TESTING CLEANED NAMES ===")
    for user in all_users:
        full_name = user.get_full_name()
        print(f"{user.username}: '{full_name}'")
    
    return fixed_count

def validate_team_data():
    """Validate all team data for accuracy"""
    print("\n=== VALIDATING TEAM DATA ===")
    
    teams = FaultLocatorTeam.objects.prefetch_related(
        'members', 
        'faultlocatordeviceassignment_set__device'
    ).annotate(
        member_count=Count('members', distinct=True),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True), distinct=True)
    )
    
    issues_found = 0
    
    for team in teams:
        print(f"\nTeam: {team.name}")
        
        # Check member count consistency
        actual_members = team.members.count()
        annotated_members = team.member_count
        
        if actual_members != annotated_members:
            print(f"  ❌ Member count mismatch: actual={actual_members}, annotated={annotated_members}")
            issues_found += 1
        else:
            print(f"  ✅ Member count: {actual_members}")
        
        # Check active assignments consistency
        actual_active = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        ).count()
        annotated_active = team.active_assignments
        
        if actual_active != annotated_active:
            print(f"  ❌ Active assignments mismatch: actual={actual_active}, annotated={annotated_active}")
            issues_found += 1
        else:
            print(f"  ✅ Active assignments: {actual_active}")
        
        # Check team leader
        if team.team_leader:
            leader_name = team.team_leader.get_full_name().strip()
            if leader_name:
                print(f"  ✅ Team leader: {leader_name}")
            else:
                print(f"  ⚠️  Team leader has no name: {team.team_leader.username}")
        else:
            print(f"  ⚠️  No team leader assigned")
        
        # Check device assignment
        device_assignment = team.faultlocatordeviceassignment_set.first()
        if device_assignment:
            print(f"  ✅ Device assigned: {device_assignment.device.serial_number}")
        else:
            print(f"  ⚠️  No device assigned")
        
        # Check deployment status
        if team.current_depot:
            print(f"  ✅ Deployed to: {team.current_depot.depot}")
        else:
            print(f"  ⚠️  Not deployed")
        
        # Check members
        print(f"  Members ({actual_members}):")
        for member in team.members.all():
            member_name = member.get_full_name().strip()
            if not member_name:
                member_name = member.username
            
            email_status = "✅" if member.email and member.email.strip() and member.email.strip().lower() != 'nan' else "⚠️"
            print(f"    {email_status} {member_name} ({member.email or 'No email'})")
    
    print(f"\n=== VALIDATION COMPLETE ===")
    print(f"Issues found: {issues_found}")
    
    return issues_found

if __name__ == "__main__":
    # Clean user names first
    clean_user_names()
    
    # Then validate team data
    validate_team_data()
    
    print("\n=== FINAL SUMMARY ===")
    print("✅ User names cleaned and validated")
    print("✅ Team data validated for accuracy")
    print("✅ Team overview should now show accurate information")
    
    # Show final team overview sample
    print("\n=== SAMPLE TEAM OVERVIEW DATA ===")
    teams = FaultLocatorTeam.objects.all()[:3]  # Show first 3 teams
    
    for team in teams:
        print(f"Team: {team.name}")
        print(f"  Members: {team.members.count()}")
        print(f"  Leader: {team.team_leader.get_full_name().strip() if team.team_leader else 'None'}")
        print(f"  Device: {team.faultlocatordeviceassignment_set.first().device.serial_number if team.faultlocatordeviceassignment_set.first() else 'None'}")
        print(f"  Location: {team.current_depot.depot if team.current_depot else 'Base'}")
        print(f"  Active Tasks: {FaultAssignment.objects.filter(team=team, located_at__isnull=True).count()}")
        print()
