#!/usr/bin/env python
"""
Debug script to check device availability for team assignment
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorDevice, FaultLocatorDeviceAssignment, FaultLocatorTeam

def check_device_availability():
    """Check device availability for assignment"""
    
    print("🔍 Device Assignment Debug Analysis")
    print("=" * 50)
    
    # 1. Check total devices in system
    total_devices = FaultLocatorDevice.objects.count()
    print(f"📱 Total devices in system: {total_devices}")
    
    if total_devices == 0:
        print("❌ No devices found in the system!")
        print("💡 Solution: Create some devices first")
        return
    
    # 2. Show all devices with their status
    print("\n📋 All devices in system:")
    for device in FaultLocatorDevice.objects.all():
        print(f"   - {device.serial_number} ({device.status}) - {device.description}")
    
    # 3. Check assigned devices
    assigned_devices = FaultLocatorDeviceAssignment.objects.values_list('device_id', flat=True)
    print(f"\n🔗 Assigned devices: {list(assigned_devices)}")
    
    # 4. Check available devices (those not assigned)
    available_devices = FaultLocatorDevice.objects.exclude(id__in=assigned_devices)
    print(f"\n✅ Available devices for assignment: {available_devices.count()}")
    
    if available_devices.count() == 0:
        print("❌ No available devices for assignment!")
        print("💡 All devices are already assigned to teams")
        
        # Show current assignments
        print("\n📋 Current device assignments:")
        for assignment in FaultLocatorDeviceAssignment.objects.select_related('device', 'team'):
            print(f"   - {assignment.device.serial_number} → {assignment.team.name}")
    else:
        print("📋 Available devices:")
        for device in available_devices:
            print(f"   - {device.serial_number} ({device.status}) - {device.description}")
    
    # 5. Check teams
    total_teams = FaultLocatorTeam.objects.count()
    print(f"\n👥 Total teams in system: {total_teams}")
    
    if total_teams == 0:
        print("❌ No teams found in the system!")
        print("💡 Solution: Create some teams first")
        return
    
    print("\n📋 All teams:")
    for team in FaultLocatorTeam.objects.all():
        print(f"   - {team.name} (Leader: {team.get_team_leader_name()})")
    
    # 6. Summary and recommendations
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   - Total devices: {total_devices}")
    print(f"   - Available devices: {available_devices.count()}")
    print(f"   - Total teams: {total_teams}")
    
    if available_devices.count() == 0 and total_devices > 0:
        print("\n⚠️  Issue: No devices available for assignment")
        print("💡 Solutions:")
        print("   1. Create new devices")
        print("   2. Unassign devices from teams that don't need them")
        print("   3. Check if device status is preventing assignment")
    elif available_devices.count() > 0:
        print("\n✅ Good: Devices are available for assignment")
        print("💡 If the form is empty, check:")
        print("   1. User permissions (must be senior foreperson)")
        print("   2. Form initialization in the view")
        print("   3. Template rendering")

def create_sample_devices():
    """Create some sample devices for testing"""
    print("\n🛠️  Creating sample devices...")
    
    sample_devices = [
        {"serial_number": "FLD-001", "description": "Fault Locator Device 1", "status": "available"},
        {"serial_number": "FLD-002", "description": "Fault Locator Device 2", "status": "available"},
        {"serial_number": "FLD-003", "description": "Fault Locator Device 3", "status": "available"},
    ]
    
    created = 0
    for device_data in sample_devices:
        device, created_new = FaultLocatorDevice.objects.get_or_create(
            serial_number=device_data["serial_number"],
            defaults={
                "description": device_data["description"],
                "status": device_data["status"]
            }
        )
        if created_new:
            print(f"✅ Created device: {device.serial_number}")
            created += 1
        else:
            print(f"ℹ️  Device already exists: {device.serial_number}")
    
    print(f"\n📊 Created {created} new devices")

if __name__ == '__main__':
    check_device_availability()
    
    # Ask if user wants to create sample devices
    print("\n" + "=" * 50)
    response = input("Do you want to create sample devices? (y/n): ").lower().strip()
    if response == 'y':
        create_sample_devices()
        print("\n" + "=" * 50)
        print("🔄 Rechecking device availability...")
        check_device_availability()
