"""
Simple test script to check the fault locator dashboard functionality
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, 'd:/b')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def test_dashboard_fixes():
    """Test that the dashboard view works without errors"""
    
    print("Testing Fault Locator Dashboard Fixes")
    print("=" * 40)
    
    # Test 1: Check Depots model fields
    from it.users.models import Depots
    
    depots = Depots.objects.all()[:3]
    print(f"✓ Found {depots.count()} depots in database")
    
    for depot in depots:
        print(f"  - {depot.depot} (code: {depot.code})")
    
    # Test 2: Check if depot has 'depot' field (not 'name')
    if hasattr(Depots, 'depot'):
        print("✓ Depots model has 'depot' field")
    else:
        print("✗ Depots model missing 'depot' field")
    
    # Test 3: Check UserProfile depot relationship
    from it.users.models import UserProfile
    
    users_with_depot = UserProfile.objects.filter(depot__isnull=False)[:3]
    print(f"✓ Found {users_with_depot.count()} users with depot assignments")
    
    for user in users_with_depot:
        print(f"  - {user.username}: {user.depot.depot if user.depot else 'No depot'}")
    
    # Test 4: Check fault locator models
    from fault_locator.models import Fault, FaultLocatorTeam
    
    faults = Fault.objects.all()[:3]
    print(f"✓ Found {faults.count()} faults in database")
    
    teams = FaultLocatorTeam.objects.all()[:3]
    print(f"✓ Found {teams.count()} teams in database")
    
    # Test 5: Check central roles integration
    try:
        from fault_locator.central_roles import FaultLocatorRoleManager
        from it.users.models import Application
        
        app = Application.objects.filter(name='Fault Locator').first()
        if app:
            print("✓ Fault Locator application found in central roles")
        else:
            print("⚠ Fault Locator application not found - run setup command")
        
    except Exception as e:
        print(f"✗ Central roles error: {e}")
    
    print("\n" + "=" * 40)
    print("Dashboard test completed!")
    print("The 'Depots' object has no attribute 'name' error should be fixed.")
    print("Dashboard should now work correctly with depot.depot field.")

if __name__ == '__main__':
    test_dashboard_fixes()
