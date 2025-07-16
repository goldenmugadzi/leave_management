#!/usr/bin/env python3
"""
Simple setup script to create fault locator roles in the database
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile, Application, Roles

def setup_fault_locator_roles():
    """Create fault locator application and roles if they don't exist"""
    
    print("Setting up fault locator roles...")
    
    # 1. Create or get fault locator application
    app, created = Application.objects.get_or_create(
        name='fault_locator',
        defaults={
            'fullname': 'Fault Locator System'
        }
    )
    
    if created:
        print(f"✓ Created fault locator application: {app.name}")
    else:
        print(f"✓ Found existing fault locator application: {app.name}")
    
    # 2. Define fault locator roles
    roles_data = [
        {
            'role': 'senior_foreman',
            'name': 'Senior Foreman',
            'description': 'Can manage all fault locator operations, deploy teams, and manage devices'
        },
        {
            'role': 'depot_foreperson',
            'name': 'Depot Foreperson',
            'description': 'Can assign faults to teams and manage operations within their depot'
        },
        {
            'role': 'team_leader',
            'name': 'Team Leader',
            'description': 'Can manage team assignments and report fault status'
        },
        {
            'role': 'team_member',
            'name': 'Team Member',
            'description': 'Can update fault status and view team assignments'
        },
        {
            'role': 'fault_reporter',
            'name': 'Fault Reporter',
            'description': 'Can report new faults in the system'
        }
    ]
    
    # 3. Create roles
    for role_data in roles_data:
        role, created = Roles.objects.get_or_create(
            role=role_data['role'],
            application='fault_locator',
            defaults={
                'name': role_data['name'],
                'description': role_data['description'],
                'app_id': app
            }
        )
        
        if created:
            print(f"✓ Created role: {role.name} ({role.role})")
        else:
            print(f"✓ Found existing role: {role.name} ({role.role})")
    
    print("\nSetup complete!")
    print("\nTo assign roles to users, use the fault locator admin interface or run:")
    print("python manage.py shell")
    print(">>> from fault_locator.central_roles import assign_fault_locator_role")
    print(">>> from it.users.models import UserProfile")
    print(">>> user = UserProfile.objects.get(username='your_username')")
    print(">>> assign_fault_locator_role(user, 'senior_foreman')")

if __name__ == '__main__':
    try:
        setup_fault_locator_roles()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
