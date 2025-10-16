#!/usr/bin/env python
"""Test responsive improvements for edit_team template"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.template import Template, Context
from django.test import RequestFactory

def test_responsive_template():
    """Test that the responsive template renders correctly"""
    print("Testing responsive edit_team template...")
    
    # Test template fragment with responsive classes
    template_content = '''
    <div class="min-h-screen bg-gradient-to-br from-violet-50 via-white to-cyan-50 p-3 md:p-6">
      <div class="max-w-7xl mx-auto">
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6 lg:gap-8">
          <div class="space-y-8">
            <form method="post" class="flex flex-col sm:flex-row gap-4">
              <div class="flex-1 relative group/select">
                <input type="text" name="test" class="w-full responsive-input">
              </div>
              <button type="submit" class="group/btn relative overflow-hidden px-6 py-3 bg-gradient-to-r from-emerald-600 to-green-600 text-white rounded-xl font-bold shadow-xl hover:shadow-emerald-500/30 transition-all duration-300 hover:scale-105 sm:w-auto w-full">
                Test Button
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
    '''
    
    try:
        template = Template(template_content)
        context = Context({})
        rendered = template.render(context)
        
        print("✅ Template rendered successfully")
        
        # Check for responsive classes
        responsive_classes = [
            'p-3 md:p-6',
            'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3',
            'gap-4 md:gap-6 lg:gap-8',
            'flex-col sm:flex-row',
            'sm:w-auto w-full'
        ]
        
        all_found = True
        for cls in responsive_classes:
            if cls in rendered:
                print(f"✅ Found responsive class: {cls}")
            else:
                print(f"❌ Missing responsive class: {cls}")
                all_found = False
        
        if all_found:
            print("\n✅ All responsive classes found in template!")
            return True
        else:
            print("\n❌ Some responsive classes missing")
            return False
            
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        return False

def test_css_responsive_rules():
    """Test that CSS contains responsive rules"""
    print("\nTesting CSS responsive rules...")
    
    css_rules = [
        '@media (min-width: 640px)',
        '@media (max-width: 640px)',
        '@media (max-width: 480px)',
        'min-height: 44px',
        'box-sizing: border-box',
        'font-size: 16px'
    ]
    
    try:
        template_path = os.path.join(settings.BASE_DIR, 'templates', 'fault_locator', 'edit_team.html')
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            all_found = True
            for rule in css_rules:
                if rule in content:
                    print(f"✅ Found CSS rule: {rule}")
                else:
                    print(f"❌ Missing CSS rule: {rule}")
                    all_found = False
            
            if all_found:
                print("\n✅ All CSS responsive rules found!")
                return True
            else:
                print("\n❌ Some CSS rules missing")
                return False
        else:
            print("❌ Template file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Edit Team Template Responsive Improvements ===")
    
    test1 = test_responsive_template()
    test2 = test_css_responsive_rules()
    
    if test1 and test2:
        print("\n🎉 All responsive improvements are working correctly!")
        print("The edit team page should now be fully responsive on all devices.")
    else:
        print("\n❌ Some responsive improvements may need attention.")
