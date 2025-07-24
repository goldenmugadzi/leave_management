#!/usr/bin/env python
"""
Test script to verify sanction_for_test app is working
This script tests the basic app structure without requiring database migrations
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.urls import reverse, resolve
from django.http import HttpRequest

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def test_app_imports():
    """Test if sanction_for_test app imports successfully"""
    try:
        from sanction_for_test import views, models, urls, admin, forms
        print("✓ All sanction_for_test modules import successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_model_definitions():
    """Test if models are properly defined"""
    try:
        from sanction_for_test.models import (
            SanctionForTestForm, SanctionFormComment, 
            SanctionFormAuditLog, SanctionFormAttachment
        )
        print("✓ All models are properly defined")
        return True
    except Exception as e:
        print(f"✗ Model definition error: {e}")
        return False

def test_url_patterns():
    """Test if URL patterns are working"""
    try:
        from sanction_for_test.urls import urlpatterns
        print(f"✓ URL patterns loaded successfully ({len(urlpatterns)} patterns)")
        return True
    except Exception as e:
        print(f"✗ URL pattern error: {e}")
        return False

def test_view_functions():
    """Test if view functions exist"""
    try:
        from sanction_for_test.views import list_view, create_view, detail_view, edit_view, approve_action
        print("✓ All view functions are properly defined")
        return True
    except Exception as e:
        print(f"✗ View function error: {e}")
        return False

def test_admin_configuration():
    """Test if admin configuration loads"""
    try:
        from sanction_for_test.admin import SanctionForTestFormAdmin
        print("✓ Admin configuration loads successfully")
        return True
    except Exception as e:
        print(f"✗ Admin configuration error: {e}")
        return False

def test_forms():
    """Test if forms are properly defined"""
    try:
        from sanction_for_test.forms import SanctionForTestForm
        print("✓ Forms are properly defined")
        return True
    except Exception as e:
        print(f"✗ Form definition error: {e}")
        return False

def main():
    print("Testing sanction_for_test app structure...")
    print("=" * 50)
    
    tests = [
        test_app_imports,
        test_model_definitions,
        test_url_patterns,
        test_view_functions,
        test_admin_configuration,
        test_forms
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The sanction_for_test app structure is working correctly.")
        print("\nNext steps:")
        print("1. Resolve database migration issues")
        print("2. Run database migrations")
        print("3. Test the approval workflow integration")
    else:
        print("❌ Some tests failed. Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()
