#!/usr/bin/env python3
"""
Test script to verify the asset_budget_report fix
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from ACE2.models import AssetBudget, Ace2
from ACE2.views import asset_budget_report
from it.users.models import UserProfile

def test_asset_budget_report_fix():
    """Test that the asset_budget_report view works without FieldError"""
    
    # Get a budget that has ACEs
    budget = AssetBudget.objects.filter(ace2__isnull=False).first()
    
    if not budget:
        print("No budget with ACEs found. Creating test data...")
        # You could create test data here if needed
        return
    
    print(f"Testing budget: {budget.budget_name} (ID: {budget.budget_id})")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get(f'/ace/asset_budget_report/{budget.budget_id}/')
    
    # Add a user to the request (required for @login_required)
    user = UserProfile.objects.first()
    if user:
        request.user = user
    else:
        print("No user found to test with")
        return
    
    try:
        # Try to call the view
        response = asset_budget_report(request, budget.budget_id)
        
        if response.status_code == 200:
            print("✅ SUCCESS: asset_budget_report view works correctly!")
            print(f"Response status: {response.status_code}")
            
            # Check if the context contains expected data
            if hasattr(response, 'context_data'):
                context = response.context_data
                print(f"Context keys: {list(context.keys())}")
            
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_asset_budget_report_fix()
