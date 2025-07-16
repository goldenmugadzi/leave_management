#!/usr/bin/env python
"""
Simple test to demonstrate the enhanced depot foreperson dashboard with existing data.
"""

import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.users.models import UserProfile, Depots
from fault_locator.models import FaultLocatorRole, FaultLocatorTeam, FaultLocatorDevice, FaultLocatorDeviceAssignment
from fault_locator.role_views import get_depot_foreperson_context
from fault_locator.central_roles import get_user_fault_locator_role, is_depot_foreperson


def demonstrate_depot_foreperson_features():
    """Demonstrate the new depot foreperson dashboard features"""
    
    print("=" * 60)
    print("DEPOT FOREPERSON DASHBOARD ENHANCEMENTS")
    print("=" * 60)
    
    print("\n📋 NEW FEATURES IMPLEMENTED:")
    print("-" * 40)
    print("✓ Depot Assignment Information")
    print("  - Shows which depot the foreperson is in charge of")
    print("  - Displays formal vs. designation-based role assignment")
    print("  - Shows depot-specific statistics")
    
    print("\n✓ Team Assignment Status")
    print("  - Shows if foreperson is a team leader")
    print("  - Shows if foreperson is a team member")
    print("  - Displays team member count and current location")
    
    print("\n✓ Device Assignment Display")
    print("  - Shows devices assigned to foreperson's team(s)")
    print("  - Displays device serial numbers and status")
    print("  - Shows device assignment history")
    
    print("\n✓ Enhanced Dashboard Layout")
    print("  - Professional header with depot information")
    print("  - Color-coded status indicators")
    print("  - Improved team overview table")
    print("  - Clear action buttons for team management")
    
    print("\n" + "=" * 60)
    print("CHECKING EXISTING DATA")
    print("=" * 60)
    
    # Check for existing depots
    print("\n📍 Available Depots:")
    print("-" * 20)
    depots = Depots.objects.all()[:5]
    for depot in depots:
        print(f"  • {depot.code}: {depot.depot}")
    
    # Check for existing users with depot assignments
    print("\n👥 Users with Depot Assignments:")
    print("-" * 30)
    users_with_depots = UserProfile.objects.filter(depot__isnull=False)[:3]
    for user in users_with_depots:
        print(f"  • {user.get_full_name()}")
        if hasattr(user, 'depot') and user.depot:
            print(f"    Depot: {user.depot}")
        if hasattr(user, 'designation') and user.designation:
            print(f"    Designation: {user.designation}")
    
    # Check for existing fault locator roles
    print("\n🎭 Fault Locator Roles:")
    print("-" * 20)
    roles = FaultLocatorRole.objects.filter(is_active=True)[:3]
    for role in roles:
        print(f"  • {role.user.get_full_name()}: {role.get_role_display()}")
        if role.depot:
            print(f"    Depot: {role.depot.depot}")
    
    # Check for existing teams
    print("\n👥 Fault Locator Teams:")
    print("-" * 20)
    teams = FaultLocatorTeam.objects.all()[:3]
    for team in teams:
        print(f"  • {team.name}")
        if team.team_leader:
            print(f"    Leader: {team.team_leader.get_full_name()}")
        if team.current_depot:
            print(f"    Depot: {team.current_depot.depot}")
        print(f"    Members: {team.members.count()}")
    
    # Check for existing devices
    print("\n📱 Fault Locator Devices:")
    print("-" * 22)
    devices = FaultLocatorDevice.objects.all()[:3]
    for device in devices:
        print(f"  • {device.serial_number}: {device.get_status_display()}")
        if device.description:
            print(f"    Description: {device.description}")
    
    # Check for device assignments
    print("\n🔗 Device Assignments:")
    print("-" * 18)
    assignments = FaultLocatorDeviceAssignment.objects.all()[:3]
    for assignment in assignments:
        print(f"  • {assignment.device.serial_number} → {assignment.team.name}")
        if assignment.assigned_by:
            print(f"    Assigned by: {assignment.assigned_by.get_full_name()}")
        print(f"    Date: {assignment.assigned_at.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n" + "=" * 60)
    print("DASHBOARD CONTEXT EXAMPLE")
    print("=" * 60)
    
    # Test with an existing depot foreperson
    depot_foreperson = FaultLocatorRole.objects.filter(
        role='depot_foreperson',
        is_active=True
    ).first()
    
    if depot_foreperson:
        print(f"\n🧪 Testing with user: {depot_foreperson.user.get_full_name()}")
        print(f"   Role: {depot_foreperson.get_role_display()}")
        if depot_foreperson.depot:
            print(f"   Depot: {depot_foreperson.depot.depot}")
        
        try:
            context = get_depot_foreperson_context(depot_foreperson.user)
            
            print("\n📊 Dashboard Context:")
            print("-" * 18)
            print(f"✓ User depot: {context.get('user_depot')}")
            print(f"✓ Role assignment: {'Formal' if context.get('depot_foreperson_role') else 'Designation-based'}")
            print(f"✓ Team as leader: {context.get('my_team_as_leader')}")
            print(f"✓ Teams as member: {len(context.get('my_teams_as_member', []))}")
            print(f"✓ Team devices: {len(context.get('my_team_devices', []))}")
            
            # Display stats
            stats = context.get('stats', {})
            print(f"\n📈 Statistics:")
            print(f"  • Teams available: {stats.get('teams_available', 0)}")
            print(f"  • Teams with devices: {stats.get('teams_with_devices', 0)}")
            print(f"  • My team devices: {stats.get('my_team_devices', 0)}")
            print(f"  • Pending faults: {stats.get('pending_faults', 0)}")
            print(f"  • Active faults: {stats.get('active_faults', 0)}")
            
        except Exception as e:
            print(f"✗ Error getting dashboard context: {e}")
    else:
        print("\n⚠️  No existing depot foreperson found for testing")
    
    print("\n" + "=" * 60)
    print("SUMMARY OF ENHANCEMENTS")
    print("=" * 60)
    
    print("\n✅ The depot foreperson dashboard now shows:")
    print("   1. ✓ What depot they are in charge of")
    print("   2. ✓ Whether they've been given a team (as leader or member)")
    print("   3. ✓ Device assignments for their team(s)")
    print("   4. ✓ Enhanced visual layout with Bootstrap styling")
    print("   5. ✓ Clear status indicators and action buttons")
    print("   6. ✓ Comprehensive team overview table")
    print("   7. ✓ Statistics on team and device availability")
    
    print("\n🌐 Access the enhanced dashboard at:")
    print("   http://127.0.0.1:8000/fault_locator/")
    
    print("\n📝 Key improvements made:")
    print("   • Enhanced get_depot_foreperson_context() function")
    print("   • Updated depot_foreperson.html template")
    print("   • Added team assignment status section")
    print("   • Added device assignment display")
    print("   • Improved visual design with Bootstrap components")
    print("   • Added comprehensive debugging information")
    
    print("\n" + "=" * 60)
    print("READY FOR TESTING!")
    print("=" * 60)


if __name__ == '__main__':
    demonstrate_depot_foreperson_features()
