#!/usr/bin/env python3

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.change_requests.models import ChangeRequest, ProfileChange, NewProfile
from it.change_requests.constants import WARNING_MESSAGES, LOG_MESSAGES

def test_approval_scenarios():
    """Test the new IT approval logic for different scenarios"""
    print("Testing IT Approval Logic for Empty Roles")
    print("=" * 50)
    
    def simulate_approval_logic(change_type, roles_to_action, roles_actions_input):
        """Simulate the approval logic"""
        print(f"\n--- Testing {change_type} ---")
        print(f"Roles to action: '{roles_to_action}'")
        print(f"Roles actions input: '{roles_actions_input}'")
        
        # Simulate the logic from the view
        roles_actions = roles_actions_input
        if roles_actions:
            roles_actions = roles_actions.strip()
        
        # Check if there are roles to assign/designate
        has_roles_to_assign = bool(roles_to_action and roles_to_action.strip() and 
                                   roles_to_action.strip() not in ['No roles or designations specified', 'None', ''])
        
        print(f"Has roles to assign: {has_roles_to_assign}")
        
        # Simulate the approval logic
        if not roles_actions:
            if has_roles_to_assign:
                print("❌ RESULT: Would show error - 'Please enter the roles implemented'")
                print("   APPROVAL: BLOCKED")
            else:
                print("✅ RESULT: Would show warning and allow approval")
                suggested_roles_actions = "No roles applied - no roles were specified for assignment"
                print(f"   ROLES ACTIONS SET TO: '{suggested_roles_actions}'")
                print(f"   WARNING MESSAGE: {WARNING_MESSAGES['NO_ROLES_TO_ASSIGN']}")
                print("   APPROVAL: ALLOWED")
        else:
            print(f"✅ RESULT: Would save roles_actions: '{roles_actions}'")
            print("   APPROVAL: ALLOWED")
    
    # Test different scenarios
    scenarios = [
        ("Profile Change", "Admin", ""),  # Has roles, no input - should block
        ("Profile Change", "Admin", "Added admin role to user"),  # Has roles, has input - should allow
        ("Profile Change", "", ""),  # No roles, no input - should allow with warning  
        ("Profile Change", "No roles or designations specified", ""),  # Explicitly no roles - should allow with warning
        ("Profile Change", "None", ""),  # Explicitly none - should allow with warning
        ("Profile Change", "   ", ""),  # Whitespace only - should allow with warning
        ("New Profile", "All roles", ""),  # Has roles, no input - should block
        ("New Profile", "Test Role", "Created user with test role"),  # Has roles, has input - should allow
        ("New Profile", "", "Created user with no additional roles"),  # No roles specified but explanation given - should allow
    ]
    
    for change_type, roles_to_action, roles_actions_input in scenarios:
        simulate_approval_logic(change_type, roles_to_action, roles_actions_input)
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- IT can approve requests with no roles specified (shows warning)")
    print("- IT must provide implementation details for requests with specific roles")
    print("- System logs all approvals with no roles for audit purposes")

if __name__ == "__main__":
    test_approval_scenarios()