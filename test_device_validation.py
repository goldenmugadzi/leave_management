#!/usr/bin/env python
"""
Test script to verify device validation for team deployment
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorDevice, FaultLocatorDeviceAssignment, FaultLocatorTeam
from fault_locator.views import validate_team_device_for_deployment
from it.users.models import UserProfile, Depots

def test_device_validation():
    """Test device validation for team deployment"""
    
    print("🔍 Testing Device Validation for Team Deployment")
    print("=" * 50)
    
    # Get or create a test team
    team, created = FaultLocatorTeam.objects.get_or_create(
        name='Test Team 1',
        defaults={'created_by': UserProfile.objects.first()}
    )
    
    print(f"📋 Using team: {team.name}")
    
    # Test 1: Team without device
    print("\n1. Testing team without device assignment...")
    is_valid, error_message = validate_team_device_for_deployment(team)
    print(f"   Valid: {is_valid}")
    print(f"   Message: {error_message}")
    assert not is_valid, "Team without device should not be valid"
    
    # Create a device
    device, created = FaultLocatorDevice.objects.get_or_create(
        serial_number='TEST-001',
        defaults={
            'description': 'Test Device',
            'status': 'available'
        }
    )
    
    # Test 2: Team with available device
    print("\n2. Testing team with available device...")
    assignment = FaultLocatorDeviceAssignment.objects.create(
        device=device,
        team=team,
        assigned_by=UserProfile.objects.first()
    )
    
    is_valid, error_message = validate_team_device_for_deployment(team)
    print(f"   Valid: {is_valid}")
    print(f"   Message: {error_message}")
    assert is_valid, "Team with available device should be valid"
    
    # Test 3: Team with device under maintenance
    print("\n3. Testing team with device under maintenance...")
    device.status = 'maintenance'
    device.save()
    
    is_valid, error_message = validate_team_device_for_deployment(team)
    print(f"   Valid: {is_valid}")
    print(f"   Message: {error_message}")
    assert not is_valid, "Team with device under maintenance should not be valid"
    
    # Test 4: Team with retired device
    print("\n4. Testing team with retired device...")
    device.status = 'retired'
    device.save()
    
    is_valid, error_message = validate_team_device_for_deployment(team)
    print(f"   Valid: {is_valid}")
    print(f"   Message: {error_message}")
    assert not is_valid, "Team with retired device should not be valid"
    
    # Test 5: Team with assigned device (should be valid)
    print("\n5. Testing team with assigned device...")
    device.status = 'assigned'
    device.save()
    
    is_valid, error_message = validate_team_device_for_deployment(team)
    print(f"   Valid: {is_valid}")
    print(f"   Message: {error_message}")
    assert is_valid, "Team with assigned device should be valid"
    
    # Clean up
    assignment.delete()
    device.delete()
    team.delete()
    
    print("\n✅ All tests passed!")
    print("Device validation is working correctly.")

def test_form_filtering():
    """Test that forms only show teams with working devices"""
    
    print("\n🔍 Testing Form Filtering")
    print("=" * 30)
    
    # Create test devices with different statuses
    device_available = FaultLocatorDevice.objects.create(
        serial_number='FORM-001',
        description='Available Device',
        status='available'
    )
    
    device_maintenance = FaultLocatorDevice.objects.create(
        serial_number='FORM-002',
        description='Maintenance Device',
        status='maintenance'
    )
    
    device_retired = FaultLocatorDevice.objects.create(
        serial_number='FORM-003',
        description='Retired Device',
        status='retired'
    )
    
    # Create test teams
    team1 = FaultLocatorTeam.objects.create(
        name='Form Test Team 1',
        created_by=UserProfile.objects.first()
    )
    
    team2 = FaultLocatorTeam.objects.create(
        name='Form Test Team 2',
        created_by=UserProfile.objects.first()
    )
    
    team3 = FaultLocatorTeam.objects.create(
        name='Form Test Team 3',
        created_by=UserProfile.objects.first()
    )
    
    # Assign devices to teams
    FaultLocatorDeviceAssignment.objects.create(
        device=device_available,
        team=team1,
        assigned_by=UserProfile.objects.first()
    )
    
    FaultLocatorDeviceAssignment.objects.create(
        device=device_maintenance,
        team=team2,
        assigned_by=UserProfile.objects.first()
    )
    
    FaultLocatorDeviceAssignment.objects.create(
        device=device_retired,
        team=team3,
        assigned_by=UserProfile.objects.first()
    )
    
    # Test form filtering
    from fault_locator.forms import TeamDeploymentForm
    
    form = TeamDeploymentForm()
    available_teams = form.fields['team'].queryset
    
    print(f"Teams available in form: {available_teams.count()}")
    for team in available_teams:
        device = team.faultlocatordeviceassignment_set.first().device
        print(f"   - {team.name} (Device: {device.serial_number}, Status: {device.status})")
    
    # Only team1 should be available (has working device)
    assert team1 in available_teams, "Team with available device should be in form"
    assert team2 not in available_teams, "Team with maintenance device should not be in form"
    assert team3 not in available_teams, "Team with retired device should not be in form"
    
    # Clean up
    FaultLocatorDeviceAssignment.objects.filter(team__in=[team1, team2, team3]).delete()
    team1.delete()
    team2.delete()
    team3.delete()
    device_available.delete()
    device_maintenance.delete()
    device_retired.delete()
    
    print("✅ Form filtering test passed!")

if __name__ == '__main__':
    test_device_validation()
    test_form_filtering()
    print("\n🎉 All device validation tests completed successfully!")
