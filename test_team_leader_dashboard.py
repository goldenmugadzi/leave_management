#!/usr/bin/env python3
"""
Test team leader dashboard functionality
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
from fault_locator.role_views import get_team_leader_context

User = get_user_model()

print("🔍 TESTING TEAM LEADER DASHBOARD FUNCTIONALITY")
print("=" * 60)

# Get user
user = User.objects.filter(username='ze9104681').first()
if not user:
    print("❌ User not found!")
    exit()

print(f"User: {user.get_full_name()}")
print(f"User ID: {user.id}")

# Check teams where user is leader
led_teams = FaultLocatorTeam.objects.filter(team_leader=user)
print(f"Teams where user is leader: {led_teams.count()}")
for team in led_teams:
    print(f"  - Team: {team.name} (ID: {team.id})")
    print(f"    Team leader: {team.team_leader}")
    print(f"    Members: {team.members.count()}")

# Test the context function
print("\n🎯 Testing get_team_leader_context function:")
context = get_team_leader_context(user)
print(f"Context keys: {list(context.keys())}")

if 'error' in context:
    print(f"❌ Error: {context['error']}")
else:
    print("✅ Context loaded successfully!")
    print(f"Team: {context.get('my_team')}")
    print(f"Current assignments: {context.get('current_assignments', 'None')}")
    if 'stats' in context:
        print(f"Stats: {context['stats']}")

print("=" * 60)
print("✅ Test complete")
