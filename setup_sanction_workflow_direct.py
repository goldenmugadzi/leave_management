#!/usr/bin/env python
"""
Direct setup script for Sanction For Test workflow
"""

import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

def setup_workflow():
    """Setup the sanction for test workflow"""
    try:
        from it.users.models import Application, Roles
        from approve.models import Workflow, Step
        
        print("Setting up Sanction For Test workflow...")
        
        # Create or get the application
        app, created = Application.objects.get_or_create(
            name='sanction_for_test',
            defaults={'fullname': 'Sanction For Test Forms'}
        )
        if created:
            print(f'✓ Created application: {app.fullname}')
        else:
            print(f'✓ Application already exists: {app.fullname}')

        # Create roles for sanction workflow
        roles_to_create = [
            {
                'role': 'sanction_responsible_official',
                'name': 'Responsible Official (Sanction)',
                'description': 'Can issue/declare sanction for test forms',
                'application': 'sanction_for_test'
            },
            {
                'role': 'sanction_receiver',
                'name': 'Sanction Receiver',
                'description': 'Can receive sanction for test forms',
                'application': 'sanction_for_test'
            },
            {
                'role': 'sanction_clearer',
                'name': 'Sanction Clearer',
                'description': 'Can clear sanction for test forms',
                'application': 'sanction_for_test'
            },
            {
                'role': 'sanction_controller',
                'name': 'Sanction Controller',
                'description': 'Can cancel sanction for test forms',
                'application': 'sanction_for_test'
            },
        ]

        created_roles = []
        for role_data in roles_to_create:
            role, created = Roles.objects.get_or_create(
                role=role_data['role'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'application': role_data['application'],
                    'app_id': app
                }
            )
            created_roles.append(role)
            if created:
                print(f'✓ Created role: {role.name}')
            else:
                print(f'✓ Role already exists: {role.name}')

        # Create workflow
        workflow, created = Workflow.objects.get_or_create(
            name='Sanction For Test Approval',
            defaults={'application': app}
        )
        if created:
            print(f'✓ Created workflow: {workflow.name}')
        else:
            print(f'✓ Workflow already exists: {workflow.name}')

        # Create workflow steps
        steps_to_create = [
            {
                'step': 1,
                'approver': created_roles[0],  # Responsible Official
                'to': 'Issue/Declaration',
            },
            {
                'step': 2,
                'approver': created_roles[1],  # Receiver
                'to': 'Receipt',
            },
            {
                'step': 3,
                'approver': created_roles[2],  # Clearer
                'to': 'Clearance',
            },
            {
                'step': 4,
                'approver': created_roles[3],  # Controller (for cancellation)
                'to': 'Cancellation (Optional)',
            },
        ]

        for step_data in steps_to_create:
            step, created = Step.objects.get_or_create(
                workflow=workflow,
                step=step_data['step'],
                defaults={
                    'approver': step_data['approver'],
                    'to': step_data['to']
                }
            )
            if created:
                print(f'✓ Created step {step.step}: {step.approver.name} -> {step.to}')
            else:
                print(f'✓ Step {step.step} already exists: {step.approver.name} -> {step.to}')

        print("\n✅ Sanction For Test workflow setup complete!")
        print("\nNext steps:")
        print("1. Assign users to the created roles using the admin interface")
        print("2. Configure role matrix for cost centers if needed")
        print("3. Test the workflow by creating a sanction form")
        return True
        
    except Exception as e:
        print(f"✗ Error setting up workflow: {e}")
        return False

def main():
    print("Sanction For Test Workflow Setup")
    print("=" * 50)
    
    if setup_workflow():
        print("\n🎉 Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
