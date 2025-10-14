#!/usr/bin/env python
"""Test script to verify URL fixes"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.urls import reverse
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from it.users.models import UserProfile

def test_url_reversal():
    """Test that URL reversal works correctly"""
    print("Testing URL reversal...")
    
    try:
        # Test the assign_fault URL (should work)
        url1 = reverse('assign_fault')
        print(f"✅ 'assign_fault' URL: {url1}")
        
        # Test the simple_assign_fault URL with fault_id (should work)
        url2 = reverse('simple_assign_fault', kwargs={'fault_id': 1})
        print(f"✅ 'simple_assign_fault' with fault_id URL: {url2}")
        
        # Test that simple_assign_fault without fault_id fails (expected)
        try:
            url3 = reverse('simple_assign_fault')
            print(f"❌ 'simple_assign_fault' without fault_id should fail but got: {url3}")
        except Exception as e:
            print(f"✅ 'simple_assign_fault' without fault_id correctly fails: {e}")
        
    except Exception as e:
        print(f"❌ URL reversal test failed: {e}")
        return False
    
    return True

def test_template_rendering():
    """Test that template rendering works"""
    print("\nTesting template rendering...")
    
    try:
        # Create a simple template with the URL pattern
        template_content = """
        <a href="{% url 'assign_fault' %}?team_id=1">Quick Assign</a>
        <a href="{% url 'simple_assign_fault' fault_id=1 %}">Assign Fault 1</a>
        """
        
        template = Template(template_content)
        context = Context({})
        
        rendered = template.render(context)
        print(f"✅ Template rendered successfully:")
        print(rendered)
        
        # Check that the rendered content contains expected URLs
        if '/fault_locator/simple-assign/' in rendered:
            print("✅ Template contains correct URLs")
        else:
            print("❌ Template URLs might be incorrect")
        
    except Exception as e:
        print(f"❌ Template rendering test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== URL Fix Verification Tests ===")
    
    test1_passed = test_url_reversal()
    test2_passed = test_template_rendering()
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! URL fixes are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the fixes.")
