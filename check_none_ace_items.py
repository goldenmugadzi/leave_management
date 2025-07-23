#!/usr/bin/env python3
"""
Check existing ACE items with None values to understand the scope of the problem
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

from ACE2.models import Ace2
from django.db import connection

def check_none_ace_items():
    """Check for existing ACE items with None values"""
    
    print("Checking existing ACE items with None values...")
    
    try:
        # Count all ACE items
        total_aces = Ace2.objects.count()
        print(f"Total ACE items: {total_aces}")
        
        # Count ACE items with None Ace_id2
        none_ace_id2 = Ace2.objects.filter(Ace_id2__isnull=True).count()
        print(f"ACE items with None Ace_id2: {none_ace_id2}")
        
        # Count ACE items with empty details_of_expenditure
        empty_details = Ace2.objects.filter(details_of_expenditure__isnull=True).count()
        empty_details += Ace2.objects.filter(details_of_expenditure='').count()
        print(f"ACE items with empty details_of_expenditure: {empty_details}")
        
        # Count ACE items with None amount
        none_amount = Ace2.objects.filter(amount__isnull=True).count()
        print(f"ACE items with None amount: {none_amount}")
        
        # Count ACE items with None budget_id
        none_budget = Ace2.objects.filter(budget_id__isnull=True).count()
        print(f"ACE items with None budget_id: {none_budget}")
        
        # Count ACE items with None section
        none_section = Ace2.objects.filter(section__isnull=True).count()
        print(f"ACE items with None section: {none_section}")
        
        print("\n" + "="*50)
        print("PROBLEMATIC ACE ITEMS SUMMARY")
        print("="*50)
        
        # Find ACE items with multiple None values
        problem_aces = Ace2.objects.filter(
            Ace_id2__isnull=True
        ).values('Ace_id', 'Ace_id2', 'details_of_expenditure', 'amount', 'budget_id', 'section')[:10]
        
        if problem_aces:
            print(f"Sample of {len(problem_aces)} ACE items with None Ace_id2:")
            for ace in problem_aces:
                print(f"  - ID: {ace['Ace_id']}, Ace_id2: {ace['Ace_id2']}, Details: {ace['details_of_expenditure']}")
                print(f"    Amount: {ace['amount']}, Budget: {ace['budget_id']}, Section: {ace['section']}")
        else:
            print("No ACE items with None Ace_id2 found")
            
        # Test string representation of existing None items
        print("\n" + "="*50)
        print("TESTING STRING REPRESENTATION")
        print("="*50)
        
        none_aces = Ace2.objects.filter(Ace_id2__isnull=True)[:3]
        if none_aces:
            print(f"Testing string representation of {len(none_aces)} ACE items with None Ace_id2:")
            for ace in none_aces:
                str_repr = str(ace)
                print(f"  - ACE ID: {ace.Ace_id}, String repr: '{str_repr}'")
        else:
            print("No ACE items with None Ace_id2 found for string representation test")
            
    except Exception as e:
        print(f"Error checking ACE items: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_none_ace_items()
