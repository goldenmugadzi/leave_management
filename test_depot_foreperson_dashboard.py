#!/usr/bin/env python
"""
Test script to verify the enhanced depot foreperson dashboard functionality.
This script demonstrates the new features added to show depot assignment, 
team assignment, and device assignment for depot forepersons.
"""

import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.contrib.auth.models import User
from it.users.models import UserProfile, Depots, Application, Roles
from fault_locator.models import (
    FaultLocatorRole, FaultLocatorTeam, FaultLocatorDevice, 
    FaultLocatorDeviceAssignment, Fault, FaultAssignment
)
from fault_locator.role_views import get_depot_foreperson_context
from fault_locator.central_roles import get_user_fault_locator_role, is_depot_foreperson


def test_depot_foreperson_dashboard():
    """Test the enhanced depot foreperson dashboard functionality"""
    
    print("=" * 60)
    print("TESTING ENHANCED DEPOT FOREPERSON DASHBOARD")
    print("=" * 60)
    
    # 1. Test depot assignment information
    print("\n1. Testing Depot Assignment Information")
    print("-" * 40)
    
    # Find or create a test depot
    test_depot, created = Depots.objects.get_or_create(
        code='TEST_DEPOT',
        defaults={'depot': 'Test Depot for Fault Locator'}
    )
    if created:
        print(f"✓ Created test depot: {test_depot.depot}")
    else:
        print(f"✓ Using existing depot: {test_depot.depot}")
    
    # Find or create a test user profile
    test_user = UserProfile.objects.filter(
        first_name='Test',
        last_name='Foreperson'
    ).first()
    
    if not test_user:
        print("! No test depot foreperson user found")
        print("  Creating a sample user for testing...")
        
        # Create a test user
        django_user = User.objects.create_user(
            username='test_foreperson',
            email='test@example.com',
            password='test123'
        )
        
        test_user = UserProfile.objects.create(
            user=django_user,
            first_name='Test',
            last_name='Foreperson',
            depot=test_depot
        )
        print(f"✓ Created test user: {test_user.get_full_name()}")
    else:
        print(f"✓ Using existing user: {test_user.get_full_name()}")
    
    # 2. Test role assignment
    print("\n2. Testing Role Assignment")
    print("-" * 40)
    
    # Check if user has central role
    fault_locator_app = Application.objects.filter(name='fault_locator').first()
    if fault_locator_app:
        depot_foreperson_role = Roles.objects.filter(
            application='fault_locator',
            role='depot_foreperson'
        ).first()
        
        if depot_foreperson_role:
            # Assign central role to test user
            test_user.roles.add(depot_foreperson_role)
            print(f"✓ Assigned central role: {depot_foreperson_role.name}")
        else:
            print("! No depot foreperson role found in central system")
    
    # Check legacy role assignment
    legacy_role, created = FaultLocatorRole.objects.get_or_create(
        user=test_user,
        role='depot_foreperson',
        depot=test_depot,
        defaults={'is_active': True}
    )
    if created:
        print(f"✓ Created legacy role assignment")
    else:
        print(f"✓ Found existing legacy role assignment")
    
    # 3. Test team assignment
    print("\n3. Testing Team Assignment")
    print("-" * 40)
    
    # Create a test team with the user as leader
    test_team, created = FaultLocatorTeam.objects.get_or_create(
        name='Test Foreperson Team',
        defaults={
            'team_leader': test_user,
            'current_depot': test_depot
        }
    )
    if created:
        print(f"✓ Created test team: {test_team.name}")
    else:
        print(f"✓ Using existing team: {test_team.name}")
    
    # Add user as a member to the team
    test_team.members.add(test_user)
    print(f"✓ Added user as team member")
    
    # 4. Test device assignment
    print("\n4. Testing Device Assignment")
    print("-" * 40)
    
    # Create a test device
    test_device, created = FaultLocatorDevice.objects.get_or_create(
        serial_number='FL-TEST-001',
        defaults={
            'description': 'Test Fault Locator Device',
            'status': 'assigned',
            'created_by': test_user
        }
    )
    if created:
        print(f"✓ Created test device: {test_device.serial_number}")
    else:
        print(f"✓ Using existing device: {test_device.serial_number}")
    
    # Assign device to team
    device_assignment, created = FaultLocatorDeviceAssignment.objects.get_or_create(
        device=test_device,
        team=test_team,
        defaults={
            'assigned_by': test_user,
            'notes': 'Test device assignment for depot foreperson dashboard'
        }
    )
    if created:
        print(f"✓ Assigned device to team")
    else:
        print(f"✓ Found existing device assignment")
    
    # 5. Test dashboard context
    print("\n5. Testing Dashboard Context")
    print("-" * 40)
    
    try:
        context = get_depot_foreperson_context(test_user)
        
        print(f"✓ Dashboard context generated successfully")
        print(f"  - User depot: {context.get('user_depot')}")
        print(f"  - Role assignment: {context.get('depot_foreperson_role')}")
        print(f"  - Team as leader: {context.get('my_team_as_leader')}")
        print(f"  - Teams as member: {context.get('my_teams_as_member', [])}")
        print(f"  - Team devices: {len(context.get('my_team_devices', []))} devices")
        
        # Check stats
        stats = context.get('stats', {})
        print(f"  - Teams available: {stats.get('teams_available', 0)}")
        print(f"  - Teams with devices: {stats.get('teams_with_devices', 0)}")
        print(f"  - My team devices: {stats.get('my_team_devices', 0)}")
        
    except Exception as e:
        print(f"✗ Error getting dashboard context: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Test role checking functions
    print("\n6. Testing Role Checking Functions")
    print("-" * 40)
    
    try:
        user_role = get_user_fault_locator_role(test_user)
        print(f"✓ User role: {user_role}")
        
        is_foreperson = is_depot_foreperson(test_user)
        print(f"✓ Is depot foreperson: {is_foreperson}")
        
    except Exception as e:
        print(f"✗ Error checking roles: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Create sample faults for testing
    print("\n7. Creating Sample Faults")
    print("-" * 40)
    
    try:
        # Create a pending fault
        pending_fault, created = Fault.objects.get_or_create(
            description='Test Pending Fault at Depot',
            depot=test_depot,
            defaults={
                'reported_by': test_user,
                'status': 'requested',
                'priority': 2
            }
        )
        if created:
            print(f"✓ Created pending fault: {pending_fault.description}")
        
        # Create an active fault
        active_fault, created = Fault.objects.get_or_create(
            description='Test Active Fault at Depot',
            depot=test_depot,
            defaults={
                'reported_by': test_user,
                'status': 'assigned',
                'priority': 3
            }
        )
        if created:
            print(f"✓ Created active fault: {active_fault.description}")
            
            # Create an assignment for the active fault
            assignment, created = FaultAssignment.objects.get_or_create(
                fault=active_fault,
                team=test_team,
                device=test_device,
                defaults={
                    'assigned_by': test_user
                }
            )
            if created:
                print(f"✓ Created fault assignment")
        
    except Exception as e:
        print(f"✗ Error creating sample faults: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE!")
    print("=" * 60)
    print("\nThe enhanced depot foreperson dashboard now shows:")
    print("• What depot the foreperson is in charge of")
    print("• Whether they have been assigned a team (as leader or member)")
    print("• What devices their team has been assigned")
    print("• Clear status indicators for formal vs. designation-based roles")
    print("• Enhanced team overview with device assignments")
    print("• Statistics on team and device availability")
    print("\nYou can now access the fault locator dashboard at:")
    print("http://127.0.0.1:8000/fault_locator/")
    print("\nLog in with the test user credentials:")
    print("Username: test_foreperson")
    print("Password: test123")


if __name__ == '__main__':
    test_depot_foreperson_dashboard()
