#!/usr/bin/env python3
"""
Debug script to check team leader assignment for user ze9104681
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import *
from django.contrib.auth import get_user_model
from fault_locator.views import get_user_fault_locator_role

User = get_user_model()

print("🔍 DEBUGGING TEAM LEADER ASSIGNMENT FOR ze9104681")
print("=" * 60)

# Check your user profile
user = User.objects.filter(username='ze9104681').first()
print(f"User found: {user}")

if user:
    print(f"User ID: {user.id}")
    print(f"User full name: {user.get_full_name()}")
    print(f"User email: {user.email}")
    print(f"Is active: {user.is_active}")
    
    # Check user roles
    roles = user.roles.all()
    print(f"User roles: {list(roles.values_list('name', flat=True))}")
    
    # Check if user has team leader role
    has_team_leader_role = user.roles.filter(name='TEAM_LEADER').exists()
    print(f"Has TEAM_LEADER role: {has_team_leader_role}")
    
    # Check team assignments as leader
    teams_leading = FaultLocatorTeam.objects.filter(team_leader=user)
    print(f"Teams leading: {teams_leading.count()}")
    for team in teams_leading:
        print(f"  - Leading team: {team.name} (ID: {team.id})")
        print(f"    Members: {team.members.count()}")
        print(f"    Current location: {team.current_depot.depot if team.current_depot else 'Not deployed'}")
    
    # Check team assignments as member
    teams_member = user.fault_locator_teams.all()
    print(f"Teams as member: {teams_member.count()}")
    for team in teams_member:
        print(f"  - Member of team: {team.name} (ID: {team.id})")
        print(f"    Team leader: {team.team_leader.get_full_name() if team.team_leader else 'No leader'}")
    
    # Check fault locator role detection
    detected_role = get_user_fault_locator_role(user)
    print(f"Detected fault locator role: {detected_role}")
    
    # Check active fault assignments
    if teams_leading.exists():
        team = teams_leading.first()
        active_assignments = FaultAssignment.objects.filter(
            team=team,
            located_at__isnull=True
        )
        print(f"Active fault assignments for led team: {active_assignments.count()}")
        for assignment in active_assignments:
            print(f"  - Fault: {assignment.fault.description[:50]}...")
    
    # Check if user is in any role that prevents team leadership
    from fault_locator.views import is_depot_foreperson, is_senior_foreman
    is_depot_fp = is_depot_foreperson(user)
    is_senior_fm = is_senior_foreman(user)
    print(f"Is depot foreperson: {is_depot_fp}")
    print(f"Is senior foreman: {is_senior_fm}")
    
else:
    print("❌ User not found!")
    
    # Search for similar usernames
    similar_users = User.objects.filter(username__icontains='ze9104681')
    print(f"Similar usernames: {similar_users.count()}")
    for user in similar_users:
        print(f"  - {user.username}")

print("=" * 60)
print("✅ Debug complete")
