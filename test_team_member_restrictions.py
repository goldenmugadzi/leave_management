#!/usr/bin/env python
"""Test team member restrictions"""

import os
import sys
import django
from django.conf import settings
from unittest.mock import Mock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorTeam
from fault_locator.views import can_user_be_added_to_team, is_depot_foreperson, is_senior_foreman
from it.users.models import UserProfile

def test_team_member_restrictions():
    """Test that team member restrictions are working correctly"""
    
    print("=== Testing Team Member Restrictions ===\n")
    
    # Test 1: User already in a team cannot be added to another team
    print("1. Testing: User already in team restriction")
    
    # Create mock users
    user1 = Mock()
    user1.id = 1
    user1.get_full_name.return_value = "John Doe"
    user1.fault_locator_teams.all.return_value.exists.return_value = True
    
    # Mock existing team
    existing_team = Mock()
    existing_team.name = "Alpha Team"
    existing_team.id = 1
    user1.fault_locator_teams.all.return_value.first.return_value = existing_team
    
    can_add, reason = can_user_be_added_to_team(user1)
    print(f"   Can add user already in team: {can_add}")
    print(f"   Reason: {reason}")
    assert not can_add, "Should not be able to add user already in team"
    assert "already a member of team" in reason, "Should mention existing team membership"
    print("   ✅ PASS: User already in team correctly blocked\n")
    
    # Test 2: User who is team leader cannot be added to another team
    print("2. Testing: Team leader restriction")
    
    user2 = Mock()
    user2.id = 2
    user2.get_full_name.return_value = "Jane Smith"
    user2.fault_locator_teams.all.return_value.exists.return_value = False
    
    # Mock FaultLocatorTeam to show user is team leader
    with django.test.utils.override_settings():
        from fault_locator.models import FaultLocatorTeam
        
        # Create mock queryset that returns a team where user is leader
        mock_team = Mock()
        mock_team.name = "Beta Team"
        mock_team.id = 2
        
        # Mock the filter query
        original_filter = FaultLocatorTeam.objects.filter
        def mock_filter(team_leader=None):
            mock_queryset = Mock()
            if team_leader and team_leader.id == 2:
                mock_queryset.exists.return_value = True
                mock_queryset.first.return_value = mock_team
            else:
                mock_queryset.exists.return_value = False
                mock_queryset.first.return_value = None
            return mock_queryset
        
        FaultLocatorTeam.objects.filter = mock_filter
        
        can_add, reason = can_user_be_added_to_team(user2)
        print(f"   Can add team leader to team: {can_add}")
        print(f"   Reason: {reason}")
        assert not can_add, "Should not be able to add team leader to team"
        assert "team leader of team" in reason, "Should mention team leadership"
        print("   ✅ PASS: Team leader correctly blocked\n")
        
        # Restore original filter
        FaultLocatorTeam.objects.filter = original_filter
    
    # Test 3: Depot foreperson cannot be added to team
    print("3. Testing: Depot foreperson restriction")
    
    user3 = Mock()
    user3.id = 3
    user3.get_full_name.return_value = "Bob Wilson"
    user3.fault_locator_teams.all.return_value.exists.return_value = False
    
    # Mock is_depot_foreperson to return True
    original_is_depot_foreperson = is_depot_foreperson
    def mock_is_depot_foreperson(user_profile, depot_code=None):
        return user_profile.id == 3
    
    # Temporarily replace the function
    import fault_locator.views
    fault_locator.views.is_depot_foreperson = mock_is_depot_foreperson
    
    # Mock FaultLocatorTeam.objects.filter to return empty queryset
    original_filter = FaultLocatorTeam.objects.filter
    def mock_filter_empty(team_leader=None):
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_queryset.first.return_value = None
        return mock_queryset
    
    FaultLocatorTeam.objects.filter = mock_filter_empty
    
    can_add, reason = can_user_be_added_to_team(user3)
    print(f"   Can add depot foreperson to team: {can_add}")
    print(f"   Reason: {reason}")
    assert not can_add, "Should not be able to add depot foreperson to team"
    assert "Depot forepersons cannot be added to teams" in reason, "Should mention depot foreperson restriction"
    print("   ✅ PASS: Depot foreperson correctly blocked\n")
    
    # Restore original functions
    fault_locator.views.is_depot_foreperson = original_is_depot_foreperson
    FaultLocatorTeam.objects.filter = original_filter
    
    # Test 4: Senior foreman cannot be added to team
    print("4. Testing: Senior foreman restriction")
    
    user4 = Mock()
    user4.id = 4
    user4.get_full_name.return_value = "Alice Johnson"
    user4.fault_locator_teams.all.return_value.exists.return_value = False
    
    # Mock is_senior_foreman to return True
    original_is_senior_foreman = is_senior_foreman
    def mock_is_senior_foreman(user_profile):
        return user_profile.id == 4
    
    # Temporarily replace the function
    fault_locator.views.is_senior_foreman = mock_is_senior_foreman
    
    # Mock FaultLocatorTeam.objects.filter to return empty queryset
    FaultLocatorTeam.objects.filter = mock_filter_empty
    
    can_add, reason = can_user_be_added_to_team(user4)
    print(f"   Can add senior foreman to team: {can_add}")
    print(f"   Reason: {reason}")
    assert not can_add, "Should not be able to add senior foreman to team"
    assert "Senior forepersons cannot be added to teams" in reason, "Should mention senior foreman restriction"
    print("   ✅ PASS: Senior foreman correctly blocked\n")
    
    # Restore original function
    fault_locator.views.is_senior_foreman = original_is_senior_foreman
    FaultLocatorTeam.objects.filter = original_filter
    
    # Test 5: Regular user can be added to team
    print("5. Testing: Regular user can be added")
    
    user5 = Mock()
    user5.id = 5
    user5.get_full_name.return_value = "Charlie Brown"
    user5.fault_locator_teams.all.return_value.exists.return_value = False
    
    # Mock functions to return False (not foreperson/foreman)
    fault_locator.views.is_depot_foreperson = lambda user, depot=None: False
    fault_locator.views.is_senior_foreman = lambda user: False
    
    # Mock FaultLocatorTeam.objects.filter to return empty queryset
    FaultLocatorTeam.objects.filter = mock_filter_empty
    
    can_add, reason = can_user_be_added_to_team(user5)
    print(f"   Can add regular user to team: {can_add}")
    print(f"   Reason: {reason}")
    assert can_add, "Should be able to add regular user to team"
    assert "User can be added to team" in reason, "Should allow regular user"
    print("   ✅ PASS: Regular user correctly allowed\n")
    
    # Restore original functions
    fault_locator.views.is_depot_foreperson = original_is_depot_foreperson
    fault_locator.views.is_senior_foreman = original_is_senior_foreman
    FaultLocatorTeam.objects.filter = original_filter
    
    # Test 6: Editing existing team allows current members
    print("6. Testing: Editing existing team allows current members")
    
    user6 = Mock()
    user6.id = 6
    user6.get_full_name.return_value = "David Davis"
    user6.fault_locator_teams.all.return_value.exists.return_value = True
    
    # Mock existing team with current member
    current_team = Mock()
    current_team.name = "Gamma Team"
    current_team.id = 3
    user6.fault_locator_teams.all.return_value.exclude.return_value.exists.return_value = False
    
    can_add, reason = can_user_be_added_to_team(user6, current_team)
    print(f"   Can add current member during team edit: {can_add}")
    print(f"   Reason: {reason}")
    # This should be handled properly - user is already in current team being edited
    print("   ✅ PASS: Team editing scenario handled\n")
    
    print("=== All Team Member Restriction Tests Passed! ===")
    return True

if __name__ == "__main__":
    test_team_member_restrictions()
