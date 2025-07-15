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

def debug_teams():
    print("=== DEBUGGING TEAM OVERVIEW ===")
    
    # Check team overview data
    teams = FaultLocatorTeam.objects.prefetch_related(
        'members', 
        'faultlocatordeviceassignment_set__device'
    ).annotate(
        member_count=Count('members', distinct=True),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True), distinct=True)
    )
    
    print(f"Total teams: {teams.count()}")
    print()
    
    for team in teams:
        print(f"Team: {team.name}")
        print(f"  Annotated member_count: {team.member_count}")
        print(f"  Actual member count: {team.members.count()}")
        print(f"  Annotated active_assignments: {team.active_assignments}")
        
        actual_active = FaultAssignment.objects.filter(team=team, located_at__isnull=True).count()
        print(f"  Actual active assignments: {actual_active}")
        
        print(f"  Team leader: {team.team_leader.get_full_name() if team.team_leader else 'None'}")
        print(f"  Current depot: {team.current_depot.depot if team.current_depot else 'None'}")
        
        device_assignment = team.faultlocatordeviceassignment_set.first()
        print(f"  Device: {device_assignment.device.serial_number if device_assignment else 'None'}")
        
        # Check members
        members = team.members.all()
        print(f"  Members ({members.count()}):")
        for member in members:
            name = member.get_full_name() if member.get_full_name().strip() else f"User {member.id}"
            print(f"    - {name} ({member.email or 'no email'})")
        
        # Check if there are any mismatches
        if team.member_count != team.members.count():
            print(f"  ❌ MEMBER COUNT MISMATCH!")
        if team.active_assignments != actual_active:
            print(f"  ❌ ACTIVE ASSIGNMENTS MISMATCH!")
        
        print()

if __name__ == "__main__":
    debug_teams()
