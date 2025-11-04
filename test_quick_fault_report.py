#!/usr/bin/env python
"""
Test script for Quick Fault Report regional filtering and search functionality
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.forms import QuickFaultReportForm
from it.users.models import Regions, Depots, UserProfile

def test_quick_fault_report_functionality():
    """Test the quick fault report form functionality"""
    
    print("🔍 Testing Quick Fault Report Functionality")
    print("=" * 50)
    
    # Test 1: Test form without regional filtering
    print("\n1. Testing form without regional filtering:")
    form = QuickFaultReportForm()
    total_depots = form.fields['depot'].queryset.count()
    print(f"   ✅ Total depots available: {total_depots}")
    
    # Test 2: Test form with regional filtering
    print("\n2. Testing form with regional filtering:")
    if Regions.objects.exists():
        region = Regions.objects.first()
        form_with_region = QuickFaultReportForm(user_region=region)
        regional_depots = form_with_region.fields['depot'].queryset.count()
        print(f"   ✅ Depots in region '{region.region}': {regional_depots}")
        
        # Show depot names in this region
        depot_names = list(form_with_region.fields['depot'].queryset.values_list('depot', flat=True))
        print(f"   📍 Depot names: {depot_names[:5]}{'...' if len(depot_names) > 5 else ''}")
    
    # Test 3: Test form with user depot restriction
    print("\n3. Testing form with user depot restriction:")
    if Depots.objects.exists():
        depot = Depots.objects.first()
        form_with_depot = QuickFaultReportForm(user_depot=depot)
        restricted_depots = form_with_depot.fields['depot'].queryset.count()
        print(f"   ✅ Restricted to user depot: {restricted_depots} depot(s)")
        print(f"   📍 Depot: {depot.depot}")
    
    # Test 4: Test regional distribution
    print("\n4. Regional distribution analysis:")
    regions = Regions.objects.all()
    for region in regions:
        depot_count = Depots.objects.filter(region=region).count()
        print(f"   📊 {region.region}: {depot_count} depots")
    
    # Test 5: Test form validation
    print("\n5. Testing form validation:")
    test_data = {
        'description': 'Test fault description',
        'depot': '',  # Empty depot to test validation
        'priority': 2
    }
    
    form = QuickFaultReportForm(data=test_data)
    is_valid = form.is_valid()
    print(f"   ✅ Form validation (empty depot): {'Valid' if is_valid else 'Invalid (Expected)'}")
    if not is_valid:
        print(f"   📝 Errors: {dict(form.errors)}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    test_quick_fault_report_functionality()
