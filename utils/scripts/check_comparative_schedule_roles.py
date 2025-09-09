#!/usr/bin/env python
"""
Script to check and create required roles for comparative schedule approval system.
This script will:
1. Check if the required roles exist in the database
2. Create them if they don't exist
3. Show current user roles for debugging
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/var/www/beii_v1')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import Roles, Application, UserProfile

def check_and_create_roles():
    """Check and create required roles for comparative schedule approval"""
    
    # Check if the Application exists
    app, created = Application.objects.get_or_create(
        name="comparative_schedule",
        defaults={
            "fullname": "Comparative Schedule Management"
        }
    )
    
    if created:
        print(f"✅ Created Application: {app.name}")
    else:
        print(f"✅ Application exists: {app.name}")
    
    # Define required roles
    required_roles = [
        {
            "role": "check",
            "name": "Finance Manager",
            "description": "Finance Manager role for comparative schedule approval",
            "application": "comparative_schedule"
        },
        {
            "role": "approve", 
            "name": "General Manager",
            "description": "General Manager role for comparative schedule approval",
            "application": "comparative_schedule"
        },
        {
            "role": "procurement",
            "name": "Procurement Officer", 
            "description": "Procurement Officer role for comparative schedule management",
            "application": "comparative_schedule"
        }
    ]
    
    created_roles = []
    existing_roles = []
    
    for role_data in required_roles:
        role, created = Roles.objects.get_or_create(
            role=role_data["role"],
            application=role_data["application"],
            defaults={
                "name": role_data["name"],
                "description": role_data["description"],
                "app_id": app
            }
        )
        
        if created:
            created_roles.append(role)
            print(f"✅ Created role: {role.name} ({role.role})")
        else:
            existing_roles.append(role)
            print(f"✅ Role exists: {role.name} ({role.role})")
    
    return created_roles, existing_roles

def check_user_roles(username=None):
    """Check roles for a specific user or all users"""
    
    if username:
        users = UserProfile.objects.filter(username=username)
        if not users.exists():
            print(f"❌ User '{username}' not found")
            return
    else:
        users = UserProfile.objects.all()
    
    print(f"\n🔍 Checking roles for {users.count()} user(s):")
    
    for user in users:
        print(f"\n👤 User: {user.username} ({user.first_name} {user.last_name})")
        
        # Get all roles for this user
        all_roles = user.roles.all()
        if not all_roles.exists():
            print("   ❌ No roles assigned")
            continue
        
        # Group roles by application
        roles_by_app = {}
        for role in all_roles:
            app = role.application
            if app not in roles_by_app:
                roles_by_app[app] = []
            roles_by_app[app].append(role)
        
        for app, roles in roles_by_app.items():
            print(f"   📱 {app}:")
            for role in roles:
                print(f"      - {role.name} ({role.role})")
        
        # Check specifically for comparative_schedule roles
        cs_roles = user.roles.filter(application="comparative_schedule")
        if cs_roles.exists():
            print("   ✅ Has comparative_schedule roles:")
            for role in cs_roles:
                print(f"      - {role.name} ({role.role})")
        else:
            print("   ❌ No comparative_schedule roles assigned")

def assign_role_to_user(username, role_name):
    """Assign a specific role to a user"""
    
    try:
        user = UserProfile.objects.get(username=username)
        role = Roles.objects.get(role=role_name, application="comparative_schedule")
        
        if role in user.roles.all():
            print(f"✅ User {username} already has role {role.name}")
        else:
            user.roles.add(role)
            print(f"✅ Assigned role {role.name} to user {username}")
            
    except UserProfile.DoesNotExist:
        print(f"❌ User '{username}' not found")
    except Roles.DoesNotExist:
        print(f"❌ Role '{role_name}' not found for comparative_schedule application")

def main():
    """Main function"""
    
    print("🔧 Comparative Schedule Roles Checker")
    print("=" * 50)
    
    # Check and create roles
    created_roles, existing_roles = check_and_create_roles()
    
    print(f"\n📊 Summary:")
    print(f"   Created: {len(created_roles)} roles")
    print(f"   Existing: {len(existing_roles)} roles")
    
    # Check user roles
    print(f"\n" + "=" * 50)
    check_user_roles()
    
    # Interactive mode
    print(f"\n" + "=" * 50)
    print("🔧 Interactive Mode")
    print("Commands:")
    print("  check <username> - Check roles for specific user")
    print("  assign <username> <role> - Assign role to user")
    print("  quit - Exit")
    
    while True:
        try:
            command = input("\nEnter command: ").strip().split()
            
            if not command:
                continue
                
            if command[0] == "quit":
                break
            elif command[0] == "check" and len(command) == 2:
                check_user_roles(command[1])
            elif command[0] == "assign" and len(command) == 3:
                assign_role_to_user(command[1], command[2])
            else:
                print("❌ Invalid command. Use: check <username>, assign <username> <role>, or quit")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
