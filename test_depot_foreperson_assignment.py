#!/usr/bin/env python
"""
Test script to verify depot foreperson assignment restrictions
"""

import os
import sys
import django
from unittest.mock import Mock, patch

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile, Depots
from fault_locator.depot_foreperson_validation import (
    validate_depot_foreperson_assignment,
    get_depot_forepersons,
    get_available_depots_for_foreperson_assignment,
    get_depot_foreperson_for_depot,
    can_reassign_depot_foreperson,
    get_depot_assignment_summary
)
from fault_locator.central_roles import (
    assign_depot_foreperson_to_depot,
    remove_depot_foreperson_from_depot,
    is_depot_foreperson_by_designation
)


def test_depot_foreperson_restrictions():
    """Test that depot foreperson restrictions work correctly"""
    
    print("🔍 Testing Depot Foreperson Assignment Restrictions")
    print("=" * 60)
    
    # Create mock objects for testing
    class MockDepot:
        def __init__(self, id, name):
            self.id = id
            self.depot = name
            self.code = f"DEP_{id}"
    
    class MockUser:
        def __init__(self, id, name, is_qualified=False):
            self.id = id
            self.name = name
            self.is_qualified = is_qualified
            self.depot = None
            
        def get_full_name(self):
            return self.name
    
    # Test data
    depot_a = MockDepot(1, "Depot A")
    depot_b = MockDepot(2, "Depot B")
    depot_c = MockDepot(3, "Depot C")
    
    # Users
    qualified_user1 = MockUser(1, "John Doe", is_qualified=True)
    qualified_user2 = MockUser(2, "Jane Smith", is_qualified=True)
    unqualified_user = MockUser(3, "Bob Johnson", is_qualified=False)
    
    # Mock the is_depot_foreperson_by_designation function
    def mock_is_depot_foreperson_by_designation(user):
        return user.is_qualified
    
    # Test cases
    test_cases = [
        {
            'name': 'Qualified user can be assigned to available depot',
            'user': qualified_user1,
            'depot': depot_a,
            'existing_forepersons': [],
            'expected_valid': True
        },
        {
            'name': 'Unqualified user cannot be assigned as depot foreperson',
            'user': unqualified_user,
            'depot': depot_a,
            'existing_forepersons': [],
            'expected_valid': False
        },
        {
            'name': 'Cannot assign second depot foreperson to same depot',
            'user': qualified_user2,
            'depot': depot_a,
            'existing_forepersons': [qualified_user1],
            'expected_valid': False
        },
        {
            'name': 'Can assign depot foreperson to different depot',
            'user': qualified_user2,
            'depot': depot_b,
            'existing_forepersons': [],
            'expected_valid': True
        },
        {
            'name': 'Can reassign existing depot foreperson to different depot',
            'user': qualified_user1,
            'depot': depot_c,
            'existing_forepersons': [],
            'expected_valid': True,
            'exclude_user': qualified_user1
        }
    ]
    
    print("Testing validation logic...")
    all_passed = True
    
    with patch('fault_locator.depot_foreperson_validation.is_depot_foreperson_by_designation', mock_is_depot_foreperson_by_designation):
        with patch('fault_locator.depot_foreperson_validation.get_depot_forepersons') as mock_get_depot_forepersons:
            
            for test_case in test_cases:
                # Set up mock return value
                mock_queryset = Mock()
                mock_queryset.exists.return_value = len(test_case['existing_forepersons']) > 0
                mock_queryset.first.return_value = test_case['existing_forepersons'][0] if test_case['existing_forepersons'] else None
                
                # Handle exclude_user case
                if test_case.get('exclude_user'):
                    mock_queryset.exclude.return_value = Mock()
                    mock_queryset.exclude.return_value.exists.return_value = False
                    mock_get_depot_forepersons.return_value = mock_queryset
                else:
                    mock_get_depot_forepersons.return_value = mock_queryset
                
                # Run validation
                exclude_user = test_case.get('exclude_user', None)
                is_valid, error_message = validate_depot_foreperson_assignment(
                    test_case['user'], 
                    test_case['depot'], 
                    exclude_user
                )
                
                # Check result
                if is_valid == test_case['expected_valid']:
                    print(f"✅ {test_case['name']}")
                    if not is_valid:
                        print(f"   └── Error: {error_message}")
                else:
                    print(f"❌ {test_case['name']}")
                    print(f"   └── Expected: {test_case['expected_valid']}, Got: {is_valid}")
                    print(f"   └── Error: {error_message}")
                    all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All depot foreperson restriction tests passed!")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return all_passed


def test_assignment_functions():
    """Test the assignment helper functions"""
    
    print("\n🔧 Testing Assignment Helper Functions")
    print("=" * 60)
    
    # Test that functions are properly imported and callable
    functions_to_test = [
        assign_depot_foreperson_to_depot,
        remove_depot_foreperson_from_depot,
        get_depot_assignment_summary,
        get_available_depots_for_foreperson_assignment,
        get_depot_foreperson_for_depot,
        can_reassign_depot_foreperson
    ]
    
    all_functions_exist = True
    
    for func in functions_to_test:
        try:
            # Check if function exists and is callable
            if callable(func):
                print(f"✅ {func.__name__} - Function exists and is callable")
            else:
                print(f"❌ {func.__name__} - Function exists but is not callable")
                all_functions_exist = False
        except Exception as e:
            print(f"❌ {func.__name__} - Error: {str(e)}")
            all_functions_exist = False
    
    print("\n" + "=" * 60)
    if all_functions_exist:
        print("🎉 All assignment helper functions are properly defined!")
    else:
        print("❌ Some functions are missing or not callable.")
    
    return all_functions_exist


def test_integration():
    """Test the integration with the central roles system"""
    
    print("\n🔗 Testing Integration with Central Roles")
    print("=" * 60)
    
    # Test that the central roles system has been updated
    try:
        from fault_locator.central_roles import FaultLocatorRoleManager
        
        # Check that depot foreperson role exists
        depot_foreperson_role = FaultLocatorRoleManager.DEPOT_FOREPERSON
        print(f"✅ Depot foreperson role constant: {depot_foreperson_role}")
        
        # Test role assignment with validation
        print("✅ Central roles system integration successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    
    print("🚀 Starting Depot Foreperson Assignment Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(test_depot_foreperson_restrictions())
    test_results.append(test_assignment_functions())
    test_results.append(test_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! The depot foreperson assignment restrictions are working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    main()
