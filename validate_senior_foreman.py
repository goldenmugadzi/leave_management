#!/usr/bin/env python
"""
Simple validation script for Senior Foreman views
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.senior_foreman_views import *

def test_view_imports():
    """Test that all Senior Foreman views can be imported"""
    
    functions_to_test = [
        'senior_foreman_dashboard',
        'team_depot_management', 
        'device_team_management',
        'performance_monitoring',
        'quick_deploy_team',
        'quick_assign_device',
        'quick_recall_team'
    ]
    
    success_count = 0
    
    for func_name in functions_to_test:
        try:
            func = globals()[func_name]
            if callable(func):
                print(f"✅ {func_name}: Import successful")
                success_count += 1
            else:
                print(f"❌ {func_name}: Not callable")
        except Exception as e:
            print(f"❌ {func_name}: Import failed - {e}")
    
    print(f"\n📊 Import Test Results: {success_count}/{len(functions_to_test)} functions imported successfully")
    return success_count == len(functions_to_test)

def test_template_files():
    """Test that all template files exist"""
    
    template_files = [
        'templates/fault_locator/senior_foreman_dashboard.html',
        'templates/fault_locator/team_depot_management.html',
        'templates/fault_locator/device_team_management.html',
        'templates/fault_locator/performance_monitoring.html'
    ]
    
    success_count = 0
    
    for template_file in template_files:
        try:
            full_path = os.path.join('d:\\b', template_file)
            if os.path.exists(full_path):
                print(f"✅ {template_file}: Template exists")
                success_count += 1
            else:
                print(f"❌ {template_file}: Template not found")
        except Exception as e:
            print(f"❌ {template_file}: Error checking template - {e}")
    
    print(f"\n📊 Template Test Results: {success_count}/{len(template_files)} templates found")
    return success_count == len(template_files)

def test_url_configuration():
    """Test that URL patterns are configured"""
    
    try:
        from fault_locator.urls import urlpatterns
        
        required_patterns = [
            'senior-dashboard/',
            'team-depot-management/',
            'device-team-management/',
            'performance-monitoring/'
        ]
        
        url_patterns = [str(pattern.pattern) for pattern in urlpatterns]
        found_patterns = []
        
        for required in required_patterns:
            found = any(required in pattern for pattern in url_patterns)
            if found:
                print(f"✅ URL Pattern '{required}': Found")
                found_patterns.append(required)
            else:
                print(f"❌ URL Pattern '{required}': Not found")
        
        print(f"\n📊 URL Test Results: {len(found_patterns)}/{len(required_patterns)} URL patterns configured")
        return len(found_patterns) == len(required_patterns)
    
    except Exception as e:
        print(f"❌ URL Configuration Test: Error - {e}")
        return False

if __name__ == '__main__':
    print("🔍 Senior Foreman Implementation Validation")
    print("=" * 60)
    
    print("\n1. Testing View Imports...")
    import_success = test_view_imports()
    
    print("\n2. Testing Template Files...")
    template_success = test_template_files()
    
    print("\n3. Testing URL Configuration...")
    url_success = test_url_configuration()
    
    print("\n" + "=" * 60)
    print("📋 Final Summary:")
    
    if import_success and template_success and url_success:
        print("🎉 All tests passed! Senior Foreman interface is ready for use.")
        print("\n📝 Access URLs:")
        print("   - Senior Foreman Dashboard: /fault_locator/senior-dashboard/")
        print("   - Team Depot Management: /fault_locator/team-depot-management/")
        print("   - Device Team Management: /fault_locator/device-team-management/")
        print("   - Performance Monitoring: /fault_locator/performance-monitoring/")
    else:
        print("⚠️  Some components need attention:")
        if not import_success:
            print("   - View imports failed")
        if not template_success:
            print("   - Template files missing")
        if not url_success:
            print("   - URL configuration incomplete")
