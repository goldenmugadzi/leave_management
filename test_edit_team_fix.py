#!/usr/bin/env python
"""Test the edit_team template URL fix"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.urls import reverse
from django.template import Template, Context
from django.test import RequestFactory

def test_template_urls():
    """Test that the template URLs work correctly"""
    print("Testing template URL resolution...")
    
    # Test the URLs used in the template
    try:
        assign_fault_url = reverse('assign_fault')
        print(f"✅ 'assign_fault' URL: {assign_fault_url}")
        
        advanced_url = reverse('advanced_fault_assignment')
        print(f"✅ 'advanced_fault_assignment' URL: {advanced_url}")
        
        # Test the template fragment
        template_content = '''
        <a href="{% url 'assign_fault' %}?team_id={{ team.id }}">Quick Assign</a>
        <a href="{% url 'advanced_fault_assignment' %}">Advanced</a>
        '''
        
        template = Template(template_content)
        context = Context({'team': {'id': 1}})
        rendered = template.render(context)
        
        print(f"✅ Template rendered successfully:")
        print(rendered)
        
        # Check if the URLs are correctly resolved
        if '/fault_locator/simple-assign/' in rendered and '/fault_locator/advanced-assign/' in rendered:
            print("✅ All URLs resolved correctly")
            return True
        else:
            print("❌ Some URLs not resolved correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_url_patterns():
    """Test that URL patterns work correctly"""
    print("\nTesting URL patterns...")
    
    try:
        # Test simple_assign_fault with fault_id
        url1 = reverse('simple_assign_fault', kwargs={'fault_id': 1})
        print(f"✅ 'simple_assign_fault' with fault_id: {url1}")
        
        # Test assign_fault without fault_id
        url2 = reverse('assign_fault')
        print(f"✅ 'assign_fault' without fault_id: {url2}")
        
        # Test that simple_assign_fault without fault_id fails
        try:
            url3 = reverse('simple_assign_fault')
            print(f"❌ 'simple_assign_fault' without fault_id should fail: {url3}")
            return False
        except:
            print("✅ 'simple_assign_fault' without fault_id correctly fails")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Edit Team Template URL Fix ===")
    
    test1 = test_template_urls()
    test2 = test_url_patterns()
    
    if test1 and test2:
        print("\n✅ All tests passed! The URL fix is working correctly.")
        print("The template should now load without NoReverseMatch errors.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
