#!/usr/bin/env python3
"""
Fix team leader role assignment for user ze9104681
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
from it.users.models import Roles, Application

User = get_user_model()

print("🔧 FIXING TEAM LEADER ROLE FOR ze9104681")
print("=" * 50)

# Get user
user = User.objects.filter(username='ze9104681').first()
if not user:
    print("❌ User not found!")
    exit()

print(f"User: {user.get_full_name()}")

# Check current roles
current_roles = user.roles.all()
print(f"Current roles: {list(current_roles.values_list('name', flat=True))}")

# Check if TEAM_LEADER role exists
team_leader_role = Roles.objects.filter(name='TEAM_LEADER').first()
if not team_leader_role:
    print("❌ TEAM_LEADER role not found in system!")
    # Check what roles exist
    all_roles = Roles.objects.all()
    print(f"Available roles: {list(all_roles.values_list('name', flat=True))}")
    
    # Look for similar roles
    similar_roles = Roles.objects.filter(name__icontains='TEAM').values_list('name', flat=True)
    print(f"Team-related roles: {list(similar_roles)}")
    
    # Create TEAM_LEADER role if it doesn't exist
    team_leader_role = Roles.objects.create(name='TEAM_LEADER', description='Team Leader for fault locator teams')
    print(f"✅ Created TEAM_LEADER role")

# Check if user already has TEAM_LEADER role
has_team_leader_role = user.roles.filter(name='TEAM_LEADER').exists()
print(f"Has TEAM_LEADER role: {has_team_leader_role}")

if not has_team_leader_role:
    # Add TEAM_LEADER role to user
    user.roles.add(team_leader_role)
    print("✅ Added TEAM_LEADER role to user")
else:
    print("✅ User already has TEAM_LEADER role")

# Now check if user should be team leader of their team
team = user.fault_locator_teams.first()
if team:
    print(f"User is member of team: {team.name}")
    print(f"Current team leader: {team.team_leader.get_full_name() if team.team_leader else 'None'}")
    
    # Make user the team leader
    team.team_leader = user
    team.save()
    print(f"✅ Made {user.get_full_name()} the leader of {team.name}")
    
    # Remove user from members since they're now the leader
    team.members.remove(user)
    print(f"✅ Removed {user.get_full_name()} from team members (now leader)")
    
else:
    print("❌ User is not a member of any team")

print("=" * 50)
print("✅ Fix complete - please test the dashboard now")
