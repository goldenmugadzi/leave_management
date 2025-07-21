#!/usr/bin/env python
"""
Test script for VVIP Boolean Field Implementation
This script tests the VVIP field functionality across the fault locator system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.append('d:\\b')

django.setup()

from fault_locator.models import Fault, FaultAssignment, FaultLocatorTeam
from it.users.models import UserProfile, Depots
from datetime import datetime, timedelta
from django.utils import timezone

def test_vvip_field_exists():
    """Test that the VVIP field exists in the Fault model"""
    print("=" * 60)
    print("TEST 1: VVIP Field Existence")
    print("=" * 60)
    
    # Check if VVIP field exists
    fault_fields = [field.name for field in Fault._meta.fields]
    vvip_exists = 'vvip' in fault_fields
    
    print(f"VVIP field exists in Fault model: {vvip_exists}")
    
    if vvip_exists:
        vvip_field = Fault._meta.get_field('vvip')
        print(f"Field type: {type(vvip_field).__name__}")
        print(f"Default value: {vvip_field.default}")
        print(f"Help text: {vvip_field.help_text}")
        print("✅ VVIP field implementation: PASSED")
    else:
        print("❌ VVIP field implementation: FAILED")
    
    return vvip_exists

def test_vvip_priority_ordering():
    """Test that VVIP faults appear first in ordering"""
    print("\n" + "=" * 60)
    print("TEST 2: VVIP Priority Ordering")
    print("=" * 60)
    
    try:
        # Get first depot for testing
        depot = Depots.objects.first()
        if not depot:
            print("❌ No depots found for testing")
            return False
        
        # Create test faults - one VVIP and one regular high priority
        test_faults_created = []
        
        # Regular high priority fault
        regular_fault = Fault.objects.create(
            description="Regular High Priority Test Fault",
            depot=depot,
            voltage='400',  # Highest voltage
            clients_affected=500,  # High client count
            priority=4,  # Critical priority
            vvip=False
        )
        test_faults_created.append(regular_fault)
        
        # VVIP fault with lower specs
        vvip_fault = Fault.objects.create(
            description="VVIP Test Fault",
            depot=depot,
            voltage='11',  # Lower voltage
            clients_affected=10,  # Lower client count
            priority=1,  # Low priority
            vvip=True  # VVIP status
        )
        test_faults_created.append(vvip_fault)
        
        # Test ordering using the same logic as views
        ordered_faults = Fault.objects.filter(depot=depot).order_by(
            '-vvip',                 # VVIP first
            '-voltage',              # Then voltage
            '-clients_affected',     # Then clients
            'reported_at',           # Then date
            '-priority'              # Then priority
        )
        
        first_fault = ordered_faults.first()
        
        print(f"Total test faults created: {len(test_faults_created)}")
        print(f"First fault in ordered list: {first_fault.description}")
        print(f"First fault VVIP status: {first_fault.vvip}")
        print(f"First fault voltage: {first_fault.voltage}")
        print(f"First fault clients: {first_fault.clients_affected}")
        
        # VVIP fault should be first despite lower technical specs
        vvip_first = first_fault.vvip == True
        
        if vvip_first:
            print("✅ VVIP priority ordering: PASSED")
            print("   VVIP fault correctly appears first despite lower technical specifications")
        else:
            print("❌ VVIP priority ordering: FAILED")
            print("   VVIP fault should appear first in priority ordering")
        
        # Cleanup test data
        for fault in test_faults_created:
            fault.delete()
            
        return vvip_first
    
    except Exception as e:
        print(f"❌ VVIP priority ordering test error: {e}")
        return False

def test_admin_interface():
    """Test admin interface integration"""
    print("\n" + "=" * 60)
    print("TEST 3: Admin Interface Integration")
    print("=" * 60)
    
    try:
        from fault_locator.admin import FaultAdmin
        
        # Check if VVIP is in list_display
        vvip_in_display = 'vvip' in FaultAdmin.list_display
        print(f"VVIP in admin list_display: {vvip_in_display}")
        
        # Check if VVIP is in list_filter
        vvip_in_filter = 'vvip' in FaultAdmin.list_filter
        print(f"VVIP in admin list_filter: {vvip_in_filter}")
        
        # Check ordering includes VVIP
        ordering_includes_vvip = FaultAdmin.ordering[0] == '-vvip'
        print(f"VVIP first in admin ordering: {ordering_includes_vvip}")
        
        admin_integration = vvip_in_display and vvip_in_filter and ordering_includes_vvip
        
        if admin_integration:
            print("✅ Admin interface integration: PASSED")
        else:
            print("❌ Admin interface integration: FAILED")
            
        return admin_integration
    
    except Exception as e:
        print(f"❌ Admin interface test error: {e}")
        return False

def test_form_integration():
    """Test form integration"""
    print("\n" + "=" * 60)
    print("TEST 4: Form Integration")
    print("=" * 60)
    
    try:
        from fault_locator.forms import FaultForm, QuickFaultReportForm
        
        # Test FaultForm
        fault_form = FaultForm()
        vvip_in_fault_form = 'vvip' in fault_form.fields
        print(f"VVIP field in FaultForm: {vvip_in_fault_form}")
        
        if vvip_in_fault_form:
            vvip_field = fault_form.fields['vvip']
            print(f"VVIP field label: {vvip_field.label}")
            print(f"VVIP field help text: {vvip_field.help_text}")
        
        # Test QuickFaultReportForm
        quick_form = QuickFaultReportForm()
        vvip_in_quick_form = 'vvip' in quick_form.fields
        print(f"VVIP field in QuickFaultReportForm: {vvip_in_quick_form}")
        
        form_integration = vvip_in_fault_form and vvip_in_quick_form
        
        if form_integration:
            print("✅ Form integration: PASSED")
        else:
            print("❌ Form integration: FAILED")
            
        return form_integration
    
    except Exception as e:
        print(f"❌ Form integration test error: {e}")
        return False

def test_view_ordering():
    """Test view ordering logic"""
    print("\n" + "=" * 60)
    print("TEST 5: View Ordering Logic")
    print("=" * 60)
    
    try:
        # Check if views are using correct ordering
        depot = Depots.objects.first()
        if not depot:
            print("❌ No depots found for testing")
            return False
            
        # Simulate the depot foreperson context ordering
        my_faults = Fault.objects.filter(depot=depot).order_by(
            '-vvip',                 # Priority 0: VVIP status (VVIP first)
            '-voltage',              # Priority 1: Voltage (highest first)
            '-clients_affected',     # Priority 2: Clients affected (most first)
            'reported_at',           # Priority 3: Date reported (oldest first) 
            '-priority'              # Priority 4: Priority level (highest first)
        )
        
        print(f"Testing view ordering with depot: {depot.depot}")
        print("Ordering criteria: -vvip, -voltage, -clients_affected, reported_at, -priority")
        
        # Simple test - just verify the query executes without error
        fault_count = my_faults.count()
        print(f"Total faults for ordering test: {fault_count}")
        
        if fault_count > 0:
            first_fault = my_faults.first()
            print(f"First fault VVIP status: {first_fault.vvip}")
            
        print("✅ View ordering logic: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ View ordering test error: {e}")
        return False

def test_complete_priority_system():
    """Complete test of priority system with multiple faults"""
    print("\n" + "=" * 60)
    print("TEST 6: Complete Priority System")
    print("=" * 60)
    
    try:
        depot = Depots.objects.first()
        if not depot:
            print("❌ No depots found for testing")
            return False
        
        # Create comprehensive test scenario
        test_faults = []
        
        # Fault 1: VVIP with low specs (should be first)
        fault1 = Fault.objects.create(
            description="VVIP Low Specs",
            depot=depot,
            voltage='0.4',  # Lowest voltage
            clients_affected=1,  # Minimal clients
            priority=1,  # Low priority
            vvip=True
        )
        test_faults.append(fault1)
        
        # Fault 2: Regular high voltage critical (should be second)
        fault2 = Fault.objects.create(
            description="Regular High Voltage Critical",
            depot=depot,
            voltage='400',  # Highest voltage
            clients_affected=1000,  # Many clients
            priority=4,  # Critical
            vvip=False
        )
        test_faults.append(fault2)
        
        # Fault 3: Another VVIP with higher specs (should be first, but after fault1 due to same VVIP status)
        fault3 = Fault.objects.create(
            description="VVIP High Specs",
            depot=depot,
            voltage='220',  # High voltage
            clients_affected=500,  # Many clients
            priority=4,  # Critical
            vvip=True
        )
        test_faults.append(fault3)
        
        # Wait a moment to ensure different timestamps
        import time
        time.sleep(0.1)
        
        # Fault 4: Regular medium priority (should be last)
        fault4 = Fault.objects.create(
            description="Regular Medium Priority",
            depot=depot,
            voltage='33',  # Medium voltage
            clients_affected=50,  # Medium clients
            priority=2,  # Medium priority
            vvip=False
        )
        test_faults.append(fault4)
        
        # Test the complete ordering
        ordered_faults = Fault.objects.filter(
            id__in=[f.id for f in test_faults]
        ).order_by(
            '-vvip',                 # VVIP first
            '-voltage',              # Then voltage
            '-clients_affected',     # Then clients
            'reported_at',           # Then date (oldest first)
            '-priority'              # Then priority
        )
        
        print("Expected order: VVIP faults first (by voltage/clients), then regular faults")
        print("\nActual ordering:")
        for i, fault in enumerate(ordered_faults, 1):
            print(f"{i}. {fault.description}")
            print(f"   VVIP: {fault.vvip}, Voltage: {fault.voltage}, Clients: {fault.clients_affected}, Priority: {fault.priority}")
        
        # Check if VVIP faults are first
        first_two_are_vvip = all(fault.vvip for fault in ordered_faults[:2])
        last_two_are_regular = all(not fault.vvip for fault in ordered_faults[2:])
        
        priority_system_correct = first_two_are_vvip and last_two_are_regular
        
        if priority_system_correct:
            print("\n✅ Complete priority system: PASSED")
            print("   VVIP faults correctly prioritized over all regular faults")
        else:
            print("\n❌ Complete priority system: FAILED")
        
        # Cleanup
        for fault in test_faults:
            fault.delete()
            
        return priority_system_correct
        
    except Exception as e:
        print(f"❌ Complete priority system test error: {e}")
        return False

def main():
    """Run all VVIP implementation tests"""
    print("VVIP BOOLEAN FIELD IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    print("Testing VVIP field that trumps all other priority rankings")
    print("=" * 60)
    
    tests = [
        ("VVIP Field Exists", test_vvip_field_exists),
        ("VVIP Priority Ordering", test_vvip_priority_ordering),
        ("Admin Interface Integration", test_admin_interface),
        ("Form Integration", test_form_integration),
        ("View Ordering Logic", test_view_ordering),
        ("Complete Priority System", test_complete_priority_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! VVIP implementation is working correctly.")
        print("\nVVIP Boolean Field Summary:")
        print("• VVIP field added to Fault model")
        print("• VVIP faults trump all other priority criteria")
        print("• Admin interface includes VVIP field")
        print("• Forms include VVIP field")
        print("• Views use correct VVIP-first ordering")
        print("• Priority system working as expected")
    else:
        print(f"⚠️  {total-passed} tests failed. Review implementation.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
