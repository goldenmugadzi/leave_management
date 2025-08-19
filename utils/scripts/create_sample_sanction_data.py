#!/usr/bin/env python
"""
Create sample sanction forms for testing
"""

import os
import sys
import django
from django.conf import settings
from django.utils import timezone

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

def create_sample_data():
    """Create sample sanction forms"""
    try:
        from sanction_for_test.models import SanctionForTestForm
        from it.users.models import UserProfile, Regions, Districts
        from approve.models import Workflow, Process
        
        # Get the first user (admin or any available user)
        user = UserProfile.objects.first()
        if not user:
            print("✗ No users found. Please create a user first.")
            return False
        
        print(f"✓ Using user: {user.username}")
        
        # Get the workflow
        workflow = Workflow.objects.filter(name='Sanction For Test Approval').first()
        if not workflow:
            print("✗ Sanction workflow not found. Please run setup_sanction_workflow_direct.py first.")
            return False
        
        print(f"✓ Using workflow: {workflow.name}")
        
        # Get region and district (optional)
        region = Regions.objects.first()
        district = Districts.objects.first()
        
        # Create sample sanction forms
        sample_forms = [
            {
                'work_to_be_carried_out': 'Testing of transmission line protection equipment on 33kV Feeder A',
                'plant_or_equipment_to_be_tested': '33kV Circuit Breaker CB-101, Protection Relay Set',
                'points_of_isolation': 'Isolate at 33kV Bus A, Earth switches closed',
                'priority': 'high',
                'risk_level': 'medium',
                'status': 'draft'
            },
            {
                'work_to_be_carried_out': 'Routine maintenance testing of distribution transformer',
                'plant_or_equipment_to_be_tested': '11kV/400V Distribution Transformer T-205',
                'points_of_isolation': 'HV Switch open, LV Isolator open',
                'priority': 'medium',
                'risk_level': 'low',
                'status': 'pending'
            },
            {
                'work_to_be_carried_out': 'Emergency testing of backup protection system',
                'plant_or_equipment_to_be_tested': 'Backup Protection Relay, Communication Equipment',
                'points_of_isolation': 'Primary protection disabled, Manual operation mode',
                'priority': 'critical',
                'risk_level': 'high',
                'status': 'awaiting_approval'
            },
        ]
        
        created_forms = []
        for i, form_data in enumerate(sample_forms, 1):
            # Create approval process
            process = Process.objects.create(workflow=workflow)
            
            # Create the form
            form = SanctionForTestForm.objects.create(
                form_no=f'SF-TEST-{timezone.now().year}-{i:03d}',
                created_by=user,
                region=region,
                district=district,
                approval_process=process,
                **form_data
            )
            created_forms.append(form)
            print(f"✓ Created form: {form.form_no} - {form.work_to_be_carried_out[:50]}...")
        
        print(f"\n✅ Created {len(created_forms)} sample sanction forms!")
        return True
        
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Creating Sample Sanction Forms")
    print("=" * 50)
    
    if create_sample_data():
        print("\n🎉 Sample data created successfully!")
        print("You can now test the sanction_for_test application in the browser.")
    else:
        print("\n❌ Failed to create sample data.")

if __name__ == "__main__":
    main()
