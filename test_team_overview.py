#!/usr/bin/env python3
"""
Team Overview Diagnostic Script
This script checks the team overview data to identify accuracy issues.
"""

import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('d:\\b')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorTeam, FaultLocatorDeviceAssignment, FaultAssignment, Fault
from it.users.models import UserProfile, Depots
from django.db.models import Count, Q

def test_team_overview_data():
    print("=== TEAM OVERVIEW DIAGNOSTIC ===")
    print()
    
    # 1. Check all teams
    teams = FaultLocatorTeam.objects.all()
    print(f"Total teams in database: {teams.count()}")
    print()
    
    for team in teams:
        print(f"--- Team: {team.name} ---")
        print(f"ID: {team.id}")
        print(f"Created: {team.created_at}")
        print(f"Team Leader: {team.team_leader.get_full_name() if team.team_leader else 'None'}")
        print(f"Current Depot: {team.current_depot.depot if team.current_depot else 'None'}")
        print(f"Assigned At: {team.assigned_at}")
        print(f"Assigned By: {team.assigned_by.get_full_name() if team.assigned_by else 'None'}")
        
        # Check members
        members = team.members.all()
        print(f"Members ({members.count()}):")
        for member in members:
            print(f"  - {member.get_full_name()} ({member.email})")
        
        # Check device assignment
        device_assignment = team.faultlocatordeviceassignment_set.first()
        if device_assignment:
            print(f"Device: {device_assignment.device.serial_number}")
            print(f"Device Status: {device_assignment.device.status}")
            print(f"Device Description: {device_assignment.device.description}")
        else:
            print("Device: None assigned")
        
        # Check active fault assignments
        active_assignments = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        )
        print(f"Active Assignments: {active_assignments.count()}")
        for assignment in active_assignments:
            print(f"  - Fault: {assignment.fault.description}")
            print(f"    Depot: {assignment.fault.depot.depot}")
            print(f"    Priority: {assignment.fault.get_priority_display()}")
            print(f"    Assigned: {assignment.assigned_at}")
        
        # Check completed assignments (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        completed_assignments = FaultAssignment.objects.filter(
            team=team,
            located_at__gte=week_ago
        )
        print(f"Completed (last 7 days): {completed_assignments.count()}")
        
        print()

    # 2. Check device assignments
    print("=== DEVICE ASSIGNMENTS ===")
    device_assignments = FaultLocatorDeviceAssignment.objects.select_related('device', 'team', 'assigned_by')
    print(f"Total device assignments: {device_assignments.count()}")
    
    for assignment in device_assignments:
        print(f"Device {assignment.device.serial_number} → Team {assignment.team.name}")
        print(f"  Assigned by: {assignment.assigned_by.get_full_name() if assignment.assigned_by else 'Unknown'}")
        print(f"  Assigned at: {assignment.assigned_at}")
        print(f"  Device status: {assignment.device.status}")
        print()

    # 3. Check fault assignments
    print("=== FAULT ASSIGNMENTS ===")
    fault_assignments = FaultAssignment.objects.select_related('fault', 'team', 'device').order_by('-assigned_at')[:10]
    print(f"Recent fault assignments (last 10):")
    
    for assignment in fault_assignments:
        status = "Located" if assignment.located_at else "In Progress"
        print(f"Fault: {assignment.fault.description}")
        print(f"  Team: {assignment.team.name}")
        print(f"  Device: {assignment.device.serial_number}")
        print(f"  Status: {status}")
        print(f"  Assigned: {assignment.assigned_at}")
        if assignment.located_at:
            print(f"  Located: {assignment.located_at}")
        print()

    # 4. Check annotations used in team_overview view
    print("=== TEAM OVERVIEW ANNOTATIONS ===")
    teams_with_annotations = FaultLocatorTeam.objects.prefetch_related(
        'members', 
        'faultlocatordeviceassignment_set__device'
    ).annotate(
        member_count=Count('members'),
        active_assignments=Count('faultassignment', filter=Q(faultassignment__located_at__isnull=True))
    )
    
    for team in teams_with_annotations:
        print(f"Team: {team.name}")
        print(f"  Annotated member_count: {team.member_count}")
        print(f"  Actual members: {team.members.count()}")
        print(f"  Annotated active_assignments: {team.active_assignments}")
        
        # Manual count for verification
        actual_active = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        ).count()
        print(f"  Actual active assignments: {actual_active}")
        
        # Check if counts match
        if team.member_count != team.members.count():
            print(f"  ❌ MEMBER COUNT MISMATCH!")
        if team.active_assignments != actual_active:
            print(f"  ❌ ACTIVE ASSIGNMENTS MISMATCH!")
        
        print()

    # 5. Check depot information
    print("=== DEPOT INFORMATION ===")
    depots = Depots.objects.all()
    print(f"Total depots: {depots.count()}")
    
    for depot in depots[:5]:  # Show first 5
        print(f"Depot: {depot.depot}")
        print(f"  Code: {depot.code}")
        print(f"  District: {depot.district}")
        print(f"  Region: {depot.region}")
        
        # Teams at this depot
        teams_at_depot = FaultLocatorTeam.objects.filter(current_depot=depot)
        print(f"  Teams deployed: {teams_at_depot.count()}")
        for team in teams_at_depot:
            print(f"    - {team.name}")
        print()

if __name__ == "__main__":
    test_team_overview_data()
