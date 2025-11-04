#!/usr/bin/env python
"""
Test script to verify that the role dashboard works without template errors.
"""

import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

import django
django.setup()

# Now import Django modules
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore

from it.users.models import UserProfile
from fault_locator.role_views import get_depot_foreperson_context

def test_depot_foreperson_context():
    """Test that depot foreperson context works without completed_today errors"""
    
    print("Testing depot foreperson context...")
    
    # Get a user profile
    user_profile = UserProfile.objects.first()
    
    if not user_profile:
        print("❌ No user profiles found. Please create a user profile first.")
        return False
    
    print(f"✅ Testing with user profile: {user_profile.get_full_name()}")
    
    try:
        # Test the context function
        print("Calling get_depot_foreperson_context...")
        context = get_depot_foreperson_context(user_profile)
        
        print(f"✅ Context generated successfully")
        print(f"Context keys: {list(context.keys())}")
        
        # Check if completed_today is in the context and is iterable
        if 'completed_today' in context:
            completed_today = context['completed_today']
            print(f"✅ completed_today type: {type(completed_today)}")
            print(f"✅ completed_today count: {len(completed_today) if hasattr(completed_today, '__len__') else 'N/A'}")
            
            # Test if it's iterable (what the template expects)
            try:
                list(completed_today)
                print("✅ completed_today is iterable (template will work)")
            except Exception as e:
                print(f"❌ completed_today is not iterable: {e}")
                return False
        else:
            print("⚠️ completed_today not in context")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing depot foreperson context: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing role dashboard fixes...")
    print("=" * 50)
    
    # Test depot foreperson context
    context_ok = test_depot_foreperson_context()
    
    print("\n" + "=" * 50)
    if context_ok:
        print("✅ All tests passed! Role dashboard should work correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 50)
