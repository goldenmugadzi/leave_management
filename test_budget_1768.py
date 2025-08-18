#!/usr/bin/env python3
"""
Test with specific budget ID 1768
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

def test_budget_1768():
    """Test with budget ID 1768 specifically"""
    
    print("Testing budget ID 1768...")
    
    try:
        # Get budget 1768
        budget = AssetBudget.objects.get(pk=1768)
        
        print(f"Budget: {budget.budget_name}")
        
        # Test the fixed query
        aces = Ace2.objects.filter(budget_id=budget).order_by('-date_created')
        
        print(f"Found {aces.count()} ACEs for this budget")
        
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
            
    except AssetBudget.DoesNotExist:
        print(f"❌ Budget with ID 1768 not found")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_budget_1768()
