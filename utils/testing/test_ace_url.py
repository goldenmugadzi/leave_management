#!/usr/bin/env python
"""
Test script to verify the ACE URL configuration
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

def test_ace_urls():
    """Test ACE URL patterns"""
    print("Testing ACE URL patterns...")
    
    # Test the original reports URL
    try:
        url = reverse('Ace:ace_reports')
        print(f"✓ ace_reports URL: {url}")
        
        # Test reverse resolution
        resolved = resolve(url)
        print(f"  Resolved to: {resolved.view_name}")
        
    except Exception as e:
        print(f"✗ Error with ace_reports: {e}")
    
    # Test the new create_ace_report URL
    try:
        url = reverse('Ace:create_ace_report')
        print(f"✓ create_ace_report URL: {url}")
        
        # Test reverse resolution
        resolved = resolve(url)
        print(f"  Resolved to: {resolved.view_name}")
        
    except Exception as e:
        print(f"✗ Error with create_ace_report: {e}")
    
    # Test direct URL resolution
    try:
        resolved = resolve('/ace/create_ace_report/')
        print(f"✓ Direct URL resolution: /ace/create_ace_report/ -> {resolved.view_name}")
        
    except Exception as e:
        print(f"✗ Error resolving /ace/create_ace_report/: {e}")

if __name__ == '__main__':
    test_ace_urls()
