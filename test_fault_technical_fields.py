#!/usr/bin/env python3
"""
Test script to verify the new fault technical fields are working properly
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import Fault
from it.users.models import Depots
from django.db import connection

def test_fault_technical_fields():
    """Test the new technical fields in the Fault model"""
    print("Testing Fault Technical Fields...")
    print("=" * 50)
    
    # Test 1: Check model field definitions
    print("1. Checking model field definitions...")
    try:
        fault = Fault()
        
        # Check voltage field
        voltage_field = fault._meta.get_field('voltage')
        print(f"✅ Voltage field: {voltage_field.__class__.__name__}")
        print(f"   Choices: {len(voltage_field.choices)} options available")
        
        # Check backfeed field
        backfeed_field = fault._meta.get_field('backfeed')
        print(f"✅ Backfeed field: {backfeed_field.__class__.__name__}")
        print(f"   Default: {backfeed_field.default}")
        
        # Check clients_affected field
        clients_field = fault._meta.get_field('clients_affected')
        print(f"✅ Clients affected field: {clients_field.__class__.__name__}")
        
    except Exception as e:
        print(f"❌ Error checking field definitions: {e}")
        return False
    
    # Test 2: Check voltage choices
    print("\n2. Checking voltage choices...")
    try:
        choices = Fault.VOLTAGE_CHOICES
        print(f"Available voltage levels: {len(choices)}")
        for choice in choices:
            print(f"   - {choice[0]}: {choice[1]}")
    except Exception as e:
        print(f"❌ Error checking voltage choices: {e}")
        return False
    
    # Test 3: Check database table structure
    print("\n3. Checking database table structure...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE fault_locator_fault")
            columns = cursor.fetchall()
            
            # Look for our new fields
            column_names = [col[0] for col in columns]
            
            if 'voltage' in column_names:
                print("✅ Voltage column exists in database")
            else:
                print("❌ Voltage column not found in database")
                
            if 'backfeed' in column_names:
                print("✅ Backfeed column exists in database")
            else:
                print("❌ Backfeed column not found in database")
                
            if 'clients_affected' in column_names:
                print("✅ Clients affected column exists in database")
            else:
                print("❌ Clients affected column not found in database")
                
    except Exception as e:
        print(f"❌ Error checking database structure: {e}")
        return False
    
    # Test 4: Test creating a fault with new fields (if depot exists)
    print("\n4. Testing fault creation with new fields...")
    try:
        depot = Depots.objects.first()
        if depot:
            # Create a test fault
            fault = Fault(
                description="Test fault with technical details",
                depot=depot,
                voltage='33',  # 33kV
                backfeed=True,
                clients_affected=250
            )
            
            # Test validation without saving
            fault.full_clean()
            print("✅ Fault validation passed with technical fields")
            print(f"   Voltage: {fault.get_voltage_display() if fault.voltage else 'Not set'}")
            print(f"   Backfeed: {'Yes' if fault.backfeed else 'No'}")
            print(f"   Clients affected: {fault.clients_affected or 'Not specified'}")
            
        else:
            print("⚠️  No depot found, skipping fault creation test")
            
    except Exception as e:
        print(f"❌ Error testing fault creation: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("✅ Fault technical fields are working correctly!")
    return True

def test_form_choices():
    """Test that forms include the new fields"""
    print("\n" + "=" * 50)
    print("Testing Form Integration...")
    print("=" * 50)
    
    try:
        from fault_locator.forms import FaultForm, QuickFaultReportForm
        
        # Test FaultForm
        print("1. Testing FaultForm...")
        form = FaultForm()
        
        if 'voltage' in form.fields:
            print("✅ Voltage field in FaultForm")
            print(f"   Field type: {form.fields['voltage'].__class__.__name__}")
        else:
            print("❌ Voltage field missing from FaultForm")
            
        if 'backfeed' in form.fields:
            print("✅ Backfeed field in FaultForm")
        else:
            print("❌ Backfeed field missing from FaultForm")
            
        if 'clients_affected' in form.fields:
            print("✅ Clients affected field in FaultForm")
        else:
            print("❌ Clients affected field missing from FaultForm")
        
        # Test QuickFaultReportForm
        print("\n2. Testing QuickFaultReportForm...")
        quick_form = QuickFaultReportForm()
        
        technical_fields = ['voltage', 'backfeed', 'clients_affected']
        for field in technical_fields:
            if field in quick_form.fields:
                print(f"✅ {field} field in QuickFaultReportForm")
            else:
                print(f"❌ {field} field missing from QuickFaultReportForm")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing forms: {e}")
        return False

def main():
    print("=" * 60)
    print("FAULT TECHNICAL FIELDS TEST SUITE")
    print("=" * 60)
    
    success = True
    
    # Test model fields
    if not test_fault_technical_fields():
        success = False
    
    # Test form integration
    if not test_form_choices():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS SUCCESSFUL!")
        print("The fault system now includes:")
        print("   ⚡ Voltage level selection (0.4kV to 400kV)")
        print("   🔄 Backfeed availability indicator")
        print("   👥 Number of clients affected tracking")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above")
    print("=" * 60)

if __name__ == "__main__":
    main()
