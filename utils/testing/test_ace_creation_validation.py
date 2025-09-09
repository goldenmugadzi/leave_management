#!/usr/bin/env python3
"""
Test script to verify ACE creation validation prevents None ACE items
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

from ACE2.models import Ace2, UserProfile, AssetBudget
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime

def test_ace_creation_validation():
    """Test that ACE creation validation prevents None ACE items"""
    
    print("Testing ACE creation validation...")
    
    # Test 1: Try to create ACE with None Ace_id2 (should fail)
    print("\n1. Testing ACE creation with None Ace_id2...")
    try:
        ace = Ace2(
            Ace_id2=None,  # This should fail validation
            details_of_expenditure="Test expenditure",
            amount=Decimal('1000.00'),
            date_created=datetime.now()
        )
        ace.save()
        print("❌ ERROR: ACE with None Ace_id2 was created (should have failed)")
    except (ValidationError, ValueError) as e:
        print(f"✅ SUCCESS: ACE with None Ace_id2 was rejected: {e}")
    except Exception as e:
        print(f"⚠️  UNEXPECTED ERROR: {e}")
    
    # Test 2: Try to create ACE with empty details_of_expenditure (should fail)
    print("\n2. Testing ACE creation with empty details_of_expenditure...")
    try:
        ace = Ace2(
            Ace_id2="ACE-TEST-001",
            details_of_expenditure="",  # Empty string should fail
            amount=Decimal('1000.00'),
            date_created=datetime.now()
        )
        ace.save()
        print("❌ ERROR: ACE with empty details_of_expenditure was created (should have failed)")
    except (ValidationError, ValueError) as e:
        print(f"✅ SUCCESS: ACE with empty details_of_expenditure was rejected: {e}")
    except Exception as e:
        print(f"⚠️  UNEXPECTED ERROR: {e}")
    
    # Test 3: Try to create ACE with None amount (should fail)
    print("\n3. Testing ACE creation with None amount...")
    try:
        ace = Ace2(
            Ace_id2="ACE-TEST-002",
            details_of_expenditure="Test expenditure",
            amount=None,  # None amount should fail
            date_created=datetime.now()
        )
        ace.save()
        print("❌ ERROR: ACE with None amount was created (should have failed)")
    except (ValidationError, ValueError) as e:
        print(f"✅ SUCCESS: ACE with None amount was rejected: {e}")
    except Exception as e:
        print(f"⚠️  UNEXPECTED ERROR: {e}")
    
    # Test 4: Create valid ACE (should succeed)
    print("\n4. Testing valid ACE creation...")
    try:
        ace = Ace2(
            Ace_id2="ACE-TEST-VALID-001",
            details_of_expenditure="Valid test expenditure",
            amount=Decimal('1000.00'),
            date_created=datetime.now()
        )
        ace.save()
        print(f"✅ SUCCESS: Valid ACE created with ID: {ace.Ace_id2}")
        
        # Test string representation
        str_repr = str(ace)
        print(f"✅ String representation: {str_repr}")
        
        # Clean up
        ace.delete()
        print("✅ Test ACE cleaned up")
        
    except Exception as e:
        print(f"❌ ERROR: Valid ACE creation failed: {e}")
    
    # Test 5: Test existing ACE with None Ace_id2 (string representation)
    print("\n5. Testing string representation of ACE with None Ace_id2...")
    try:
        # Find existing ACE with None Ace_id2
        none_aces = Ace2.objects.filter(Ace_id2__isnull=True)[:5]
        
        if none_aces:
            print(f"Found {len(none_aces)} ACE(s) with None Ace_id2:")
            for ace in none_aces:
                str_repr = str(ace)
                print(f"  - ACE ID: {ace.id}, String repr: '{str_repr}'")
        else:
            print("No ACE items with None Ace_id2 found")
            
    except Exception as e:
        print(f"❌ ERROR: Could not test existing ACE items: {e}")

def test_ace_str_method():
    """Test the __str__ method handles None values correctly"""
    
    print("\n\nTesting ACE __str__ method...")
    
    # Create test ACE with None Ace_id2
    ace = Ace2()
    ace.Ace_id2 = None
    ace.details_of_expenditure = "Test expenditure"
    
    str_repr = str(ace)
    print(f"ACE with None Ace_id2 string representation: '{str_repr}'")
    
    if "None" not in str_repr:
        print("✅ SUCCESS: __str__ method handles None Ace_id2 correctly")
    else:
        print("❌ ERROR: __str__ method still shows 'None' for None Ace_id2")
    
    # Test with valid Ace_id2
    ace.Ace_id2 = "ACE-TEST-STR-001"
    str_repr = str(ace)
    print(f"ACE with valid Ace_id2 string representation: '{str_repr}'")

if __name__ == "__main__":
    print("=" * 60)
    print("ACE CREATION VALIDATION TEST")
    print("=" * 60)
    
    test_ace_creation_validation()
    test_ace_str_method()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
