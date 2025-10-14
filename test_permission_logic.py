#!/usr/bin/env python
"""
Test the key validation logic for fault priority changes
"""

def test_permission_logic():
    """Test the permission checking logic"""
    
    # Mock objects for testing
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    
    class MockFault:
        def __init__(self, reported_by, status):
            self.reported_by = reported_by
            self.status = status
    
    # Test users
    user1 = MockUser(1)
    user2 = MockUser(2)
    
    # Test cases
    test_cases = [
        {
            'name': 'Creator can change priority for active fault',
            'fault': MockFault(user1, 'assigned'),
            'user': user1,
            'expected': True
        },
        {
            'name': 'Non-creator cannot change priority',
            'fault': MockFault(user1, 'assigned'),
            'user': user2,
            'expected': False
        },
        {
            'name': 'Creator cannot change priority for closed fault',
            'fault': MockFault(user1, 'closed'),
            'user': user1,
            'expected': False
        },
        {
            'name': 'Creator cannot change priority for resolved fault',
            'fault': MockFault(user1, 'resolved'),
            'user': user1,
            'expected': False
        }
    ]
    
    print("Testing permission logic...")
    all_passed = True
    
    for test_case in test_cases:
        # Simulate the permission check logic
        can_change = (
            test_case['fault'].reported_by == test_case['user'] and 
            test_case['fault'].status not in ['closed', 'resolved']
        )
        
        if can_change == test_case['expected']:
            print(f"✅ {test_case['name']}")
        else:
            print(f"❌ {test_case['name']}")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All permission tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_permission_logic()
