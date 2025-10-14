#!/usr/bin/env python3
"""
Script to demonstrate how to use the new central role system for fault locator.
This script shows how to set up and use the fault locator roles integration.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile, Application, Roles
from fault_locator.central_roles import FaultLocatorRoleManager, assign_fault_locator_role
from fault_locator.models import FaultLocatorRole

def setup_fault_locator_roles():
    """Set up fault locator roles in the central system"""
    print("Setting up fault locator roles in central system...")
    
    # This is equivalent to running the management command
    from django.core.management import call_command
    call_command('setup_fault_locator_roles')
    
    print("Setup complete!")

def demonstrate_role_usage():
    """Demonstrate how to use the new role system"""
    print("\n" + "="*50)
    print("DEMONSTRATING ROLE USAGE")
    print("="*50)
    
    # Get some sample users
    users = UserProfile.objects.filter(is_active=True)[:5]
    
    if not users:
        print("No users found in the system")
        return
    
    print(f"Found {users.count()} users to demonstrate with")
    
    # Demonstrate role assignment
    print("\n1. Assigning roles to users:")
    for i, user in enumerate(users):
        if i == 0:
            role = FaultLocatorRoleManager.SENIOR_FOREMAN
        elif i == 1:
            role = FaultLocatorRoleManager.DEPOT_FOREPERSON
        elif i == 2:
            role = FaultLocatorRoleManager.TEAM_LEADER
        else:
            role = FaultLocatorRoleManager.TEAM_MEMBER
        
        success = assign_fault_locator_role(user, role)
        if success:
            print(f"   ✓ Assigned {role} to {user.username}")
        else:
            print(f"   ✗ Failed to assign {role} to {user.username}")
    
    print("\n2. Checking user roles:")
    for user in users:
        role = FaultLocatorRoleManager.get_user_role(user)
        role_display = FaultLocatorRoleManager.get_user_role_display(user)
        print(f"   {user.username}: {role_display if role_display else 'No role'}")
    
    print("\n3. Role-based permission checks:")
    for user in users:
        from fault_locator.central_roles import is_senior_foreman, is_depot_foreperson, is_team_leader
        
        permissions = []
        if is_senior_foreman(user):
            permissions.append("Senior Foreman")
        if is_depot_foreperson(user):
            permissions.append("Depot Foreperson")
        if is_team_leader(user):
            permissions.append("Team Leader")
        
        print(f"   {user.username}: {', '.join(permissions) if permissions else 'No special permissions'}")
    
    print("\n4. Getting users by role:")
    for role_code, role_name in [
        (FaultLocatorRoleManager.SENIOR_FOREMAN, 'Senior Foreman'),
        (FaultLocatorRoleManager.DEPOT_FOREPERSON, 'Depot Foreperson'),
        (FaultLocatorRoleManager.TEAM_LEADER, 'Team Leader'),
        (FaultLocatorRoleManager.TEAM_MEMBER, 'Team Member'),
    ]:
        users_with_role = FaultLocatorRoleManager.get_users_with_role(role_code)
        print(f"   {role_name}: {users_with_role.count()} users")

def check_system_status():
    """Check the current status of the role system"""
    print("\n" + "="*50)
    print("SYSTEM STATUS CHECK")
    print("="*50)
    
    # Check if application exists
    app = FaultLocatorRoleManager.get_application()
    if app:
        print(f"✓ Application '{app.name}' exists")
    else:
        print("✗ Application 'fault_locator' not found")
        print("  Run: python manage.py setup_fault_locator_roles")
        return
    
    # Check available roles
    roles = FaultLocatorRoleManager.get_available_roles()
    print(f"✓ Found {roles.count()} available roles:")
    for role in roles:
        print(f"  - {role.name} ({role.role})")
    
    # Check legacy roles
    legacy_roles = FaultLocatorRole.objects.filter(is_active=True)
    print(f"📋 Legacy roles: {legacy_roles.count()}")
    if legacy_roles.count() > 0:
        print("  Consider migrating these to the central system")
    
    # Check current assignments
    users_with_roles = UserProfile.objects.filter(
        roles__application='fault_locator',
        roles__app_id=app
    ).distinct()
    print(f"👥 Users with fault locator roles: {users_with_roles.count()}")

def migration_helper():
    """Help with migrating from legacy roles"""
    print("\n" + "="*50)
    print("MIGRATION HELPER")
    print("="*50)
    
    legacy_count = FaultLocatorRole.objects.filter(is_active=True).count()
    print(f"Legacy roles to migrate: {legacy_count}")
    
    if legacy_count > 0:
        print("\nTo migrate, you can:")
        print("1. Use the web interface: /fault_locator/migrate-legacy-roles/")
        print("2. Run: python manage.py migrate_legacy_roles")
        print("3. Use the migrate_legacy_roles() function")
        
        response = input("\nWould you like to migrate now? (y/n): ")
        if response.lower() == 'y':
            from fault_locator.central_roles import migrate_legacy_roles
            migrated, errors = migrate_legacy_roles()
            print(f"Migrated: {migrated}")
            if errors:
                print("Errors:")
                for error in errors:
                    print(f"  - {error}")
    else:
        print("No legacy roles to migrate")

if __name__ == "__main__":
    print("FAULT LOCATOR CENTRAL ROLES SETUP")
    print("="*50)
    
    # Check current status
    check_system_status()
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Set up fault locator roles in central system")
    print("2. Demonstrate role usage")
    print("3. Migration helper")
    print("4. Check system status")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == '1':
        setup_fault_locator_roles()
    elif choice == '2':
        demonstrate_role_usage()
    elif choice == '3':
        migration_helper()
    elif choice == '4':
        check_system_status()
    elif choice == '5':
        print("Goodbye!")
    else:
        print("Invalid choice")
