#!/usr/bin/env python
"""
Test script to verify sanction_for_test is properly integrated into business applications menu
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def test_menu_integration():
    """Test if sanction_for_test is in the business applications menu"""
    try:
        from it.beii_auth.views import APPLICATIONS
        
        sanction_app = None
        for app in APPLICATIONS:
            if app.get('name') == 'sanction_for_test':
                sanction_app = app
                break
        
        if sanction_app:
            print("✓ Sanction For Test found in business applications menu")
            print(f"  Title: {sanction_app['title']}")
            print(f"  Icon: {sanction_app['iconUrl']}")
            print(f"  URL: {sanction_app['url']}")
            return True
        else:
            print("✗ Sanction For Test not found in business applications menu")
            return False
            
    except Exception as e:
        print(f"✗ Error checking menu integration: {e}")
        return False

def test_url_resolution():
    """Test if URLs resolve correctly"""
    try:
        from django.urls import reverse, resolve
        from sanction_for_test.views import list_view
        
        # Test that sanction_for_test:list resolves
        url = reverse('sanction_for_test:list')
        print(f"✓ URL pattern resolves to: {url}")
        
        # Test that the URL resolves back to the correct view
        resolver = resolve('/sanction_for_test/')
        if resolver.func == list_view:
            print("✓ URL resolves to correct view function")
            return True
        else:
            print("✗ URL does not resolve to expected view")
            return False
            
    except Exception as e:
        print(f"✗ Error testing URL resolution: {e}")
        return False

def test_templates_exist():
    """Test if required templates exist"""
    template_files = [
        'd:\\b\\templates\\sanction_for_test\\list.html',
        'd:\\b\\templates\\sanction_for_test\\create.html',
        'd:\\b\\templates\\sanction_for_test\\detail.html',
        'd:\\b\\templates\\sanction_for_test\\confirm_delete.html'
    ]
    
    all_exist = True
    for template in template_files:
        if os.path.exists(template):
            print(f"✓ Template exists: {os.path.basename(template)}")
        else:
            print(f"✗ Template missing: {os.path.basename(template)}")
            all_exist = False
    
    return all_exist

def test_icon_exists():
    """Test if the icon file exists"""
    icon_path = 'd:\\b\\static\\assets\\images\\sanction_for_test.png'
    if os.path.exists(icon_path):
        print("✓ Icon file exists: sanction_for_test.png")
        return True
    else:
        print("✗ Icon file missing: sanction_for_test.png")
        return False

def main():
    print("Testing Sanction For Test Business Application Integration...")
    print("=" * 60)
    
    tests = [
        ("Menu Integration", test_menu_integration),
        ("URL Resolution", test_url_resolution),
        ("Templates", test_templates_exist),
        ("Icon File", test_icon_exists)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Sanction For Test is successfully integrated into the business applications menu!")
        print("\nNext steps:")
        print("1. Test the application in the browser")
        print("2. Verify the approval workflow works correctly")
        print("3. Test role-based access if configured")
    else:
        print("❌ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
