#!/usr/bin/env python
"""
Test script to verify the ACE URL without trailing slash
"""
import os
import sys
import django
from django.conf import settings
from django.urls import reverse, resolve

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def test_ace_url_no_slash():
    """Test ACE URL without trailing slash"""
    print("Testing ACE URL without trailing slash...")
    
    # Test direct URL resolution without slash
    try:
        resolved = resolve('/ace/create_ace_report')
        print(f"✓ Direct URL resolution: /ace/create_ace_report -> {resolved.view_name}")
        
    except Exception as e:
        print(f"✗ Error resolving /ace/create_ace_report: {e}")
    
    # Test reverse lookup for no slash version
    try:
        url = reverse('Ace:create_ace_report_no_slash')
        print(f"✓ No slash URL reverse lookup: {url}")
        
    except Exception as e:
        print(f"✗ Error with no slash URL reverse lookup: {e}")

if __name__ == '__main__':
    test_ace_url_no_slash()
