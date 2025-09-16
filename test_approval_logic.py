#!/usr/bin/env python3

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.change_requests.models import ChangeRequest, ProfileChange

def test_approval_logic():
    """Test the new approval logic for empty roles"""
    print("Testing approval logic for change requests with no roles to assign...")
    print("=" * 60)
    
    # Get a profile change request
    cr = ChangeRequest.objects.filter(profile_change__isnull=False).first()
    if not cr:
        print("No profile change requests found to test")
        return
    
    pc = cr.profile_change
    print(f"Testing with Change Request: {cr.cr_id}")
    print(f"User: {pc.user.username}")
    print(f"Roles to action: '{pc.roles_to_action}'")
    print(f"Current roles actions: '{pc.roles_actions}'")
    print()
    
    # Test the logic for determining if roles need to be assigned
    has_roles_to_assign = bool(pc.roles_to_action and pc.roles_to_action.strip() and 
                               pc.roles_to_action.strip() not in ['No roles or designations specified', 'None', ''])
    
    print("Logic test results:")
    print(f"  has_roles_to_assign: {has_roles_to_assign}")
    
    # Simulate empty roles_actions (what IT would enter)
    roles_actions = ""  # Empty input from IT
    
    if not roles_actions:
        if has_roles_to_assign:
            print("  Result: Would require IT to enter roles implemented")
        else:
            print("  Result: Would allow approval with warning message")
            suggested_message = "No roles applied - no roles were specified for assignment"
            print(f"  Suggested roles_actions: '{suggested_message}'")
    else:
        print(f"  Result: Would save roles_actions: '{roles_actions}'")
    
    print()
    print("Testing different scenarios:")
    print("-" * 40)
    
    # Test scenarios
    scenarios = [
        ("Admin", "Has roles to assign"),
        ("", "No roles to assign"),
        ("None", "No roles to assign"),
        ("No roles or designations specified", "No roles to assign"),
        ("Test Role", "Has roles to assign"),
        ("   ", "No roles to assign (whitespace only)"),
    ]
    
    for roles_to_action, expected in scenarios:
        has_roles = bool(roles_to_action and roles_to_action.strip() and 
                        roles_to_action.strip() not in ['No roles or designations specified', 'None', ''])
        print(f"  '{roles_to_action}' -> {expected} -> {has_roles}")

if __name__ == "__main__":
    test_approval_logic()