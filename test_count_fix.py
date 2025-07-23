#!/usr/bin/env python3
"""
Simple test to verify the Count('id') fix works
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import AssetBudget, Ace2
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

def test_count_fix():
    """Test that Count('Ace_id') works correctly"""
    
    print("Testing Count('Ace_id') fix...")
    
    try:
        # Get a budget with ACEs
        budget = AssetBudget.objects.filter(ace2__isnull=False).first()
        
        if not budget:
            print("No budget with ACEs found for testing")
            return
        
        print(f"Testing with budget: {budget.budget_name}")
        
        # Test the fixed query
        aces = Ace2.objects.filter(budget_id=budget).order_by('-date_created')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        monthly_usage = aces.filter(
            date_created__gte=start_date,
            date_created__lte=end_date
        ).annotate(
            month=TruncMonth('date_created')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            ace_count=Count('Ace_id')  # This should work now
        ).order_by('month')
        
        print(f"✅ SUCCESS: Query executed successfully!")
        print(f"Found {len(monthly_usage)} months of data")
        
        for item in monthly_usage:
            print(f"  {item['month'].strftime('%b %Y')}: {item['ace_count']} ACEs, Total: ${item['total_amount'] or 0:,.2f}")
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_count_fix()
