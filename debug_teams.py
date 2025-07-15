#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

# Setup Django
django.setup()

from fault_locator.models import FaultLocatorTeam, FaultLocatorDeviceAssignment
from it.users.models import UserProfile
from fault_locator.central_roles import is_senior_foreman

def debug_teams():
    print("=== FAULT LOCATOR TEAMS DEBUG ===")
    
    # Get all teams
    teams = FaultLocatorTeam.objects.all()
    print(f"Total teams: {teams.count()}")
    
    for team in teams:
        device_assignment = team.faultlocatordeviceassignment_set.first()
        print(f"\nTeam: {team.name}")
        print(f"  ID: {team.id}")
        print(f"  Current Depot: {team.current_depot}")
        print(f"  Has Device: {device_assignment is not None}")
        if device_assignment:
            print(f"  Device: {device_assignment.device.serial_number}")
        print(f"  Members: {team.members.count()}")
        print(f"  Leader: {team.team_leader}")
        print(f"  Can show 'Assign to Depot': {device_assignment is not None and team.current_depot is None}")
    
    # Check if there are any senior foremen
    print("\n=== SENIOR FOREMEN ===")
    senior_foremen = []
    for profile in UserProfile.objects.filter(is_active=True):
        if is_senior_foreman(profile):
            senior_foremen.append(profile)
    
    print(f"Senior foremen count: {len(senior_foremen)}")
    for foreman in senior_foremen:
        print(f"  - {foreman.user.get_full_name() or foreman.user.username}")

if __name__ == "__main__":
    debug_teams()
