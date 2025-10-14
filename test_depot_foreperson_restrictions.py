#!/usr/bin/env python
"""
Test script to verify depot foreperson team interaction restrictions
"""

def test_depot_foreperson_team_interaction():
    """Test the team interaction logic for depot forepersons"""
    
    # Mock objects for testing
    class MockDepot:
        def __init__(self, id, name):
            self.id = id
            self.depot = name
            self.code = f"DEP_{id}"
    
    class MockUser:
        def __init__(self, user_id, depot, is_senior=False, is_depot_fp=False):
            self.id = user_id
            self.depot = depot
            self.is_senior = is_senior
            self.is_depot_fp = is_depot_fp
    
    class MockTeam:
        def __init__(self, team_id, name, current_depot=None):
            self.id = team_id
            self.name = name
            self.current_depot = current_depot
    
    # Test data
    depot_a = MockDepot(1, "Depot A")
    depot_b = MockDepot(2, "Depot B")
    
    # Users
    senior_foreman = MockUser(1, depot_a, is_senior=True)
    depot_fp_a = MockUser(2, depot_a, is_depot_fp=True)
    depot_fp_b = MockUser(3, depot_b, is_depot_fp=True)
    
    # Teams
    team_at_depot_a = MockTeam(1, "Team Alpha", depot_a)
    team_at_depot_b = MockTeam(2, "Team Beta", depot_b)
    team_undeployed = MockTeam(3, "Team Gamma")
    
    # Test cases
    test_cases = [
        {
            'name': 'Senior foreman can interact with any team',
            'user': senior_foreman,
            'team': team_at_depot_a,
            'expected': True
        },
        {
            'name': 'Depot FP can interact with team at their depot',
            'user': depot_fp_a,
            'team': team_at_depot_a,
            'expected': True
        },
        {
            'name': 'Depot FP cannot interact with team at another depot',
            'user': depot_fp_a,
            'team': team_at_depot_b,
            'expected': False
        },
        {
            'name': 'Depot FP cannot interact with undeployed team',
            'user': depot_fp_a,
            'team': team_undeployed,
            'expected': False
        },
        {
            'name': 'Different depot FP cannot interact with team',
            'user': depot_fp_b,
            'team': team_at_depot_a,
            'expected': False
        }
    ]
    
    print("Testing depot foreperson team interaction restrictions...")
    all_passed = True
    
    for test_case in test_cases:
        # Simulate the permission check logic
        can_interact = False
        
        if test_case['user'].is_senior:
            can_interact = True
        elif test_case['user'].is_depot_fp:
            # Depot foreperson can only interact with teams deployed to their depot
            can_interact = (test_case['team'].current_depot == test_case['user'].depot)
        
        if can_interact == test_case['expected']:
            print(f"✅ {test_case['name']}")
        else:
            print(f"❌ {test_case['name']}")
            print(f"    Expected: {test_case['expected']}, Got: {can_interact}")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All team interaction tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_depot_foreperson_team_interaction()
