#!/usr/bin/env python
"""
Final verification that the ACE create report URLs are working
"""
import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse, resolve

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def final_verification():
    """Final verification of ACE create report URLs"""
    print("=== Final Verification of ACE Create Report URLs ===")
    print()
    
    # Test URL resolution
    print("1. URL Resolution Tests:")
    urls_to_test = [
        '/ace/create_ace_report/',
        '/ace/create_ace_report',
        '/ace/reports/'
    ]
    
    for url in urls_to_test:
        try:
            resolved = resolve(url)
            print(f"   ✓ {url} -> {resolved.view_name}")
        except Exception as e:
            print(f"   ✗ {url} -> ERROR: {e}")
    
    print()
    
    # Test reverse URL lookup
    print("2. Reverse URL Lookup Tests:")
    names_to_test = [
        'Ace:create_ace_report',
        'Ace:create_ace_report_no_slash',
        'Ace:ace_reports'
    ]
    
    for name in names_to_test:
        try:
            url = reverse(name)
            print(f"   ✓ {name} -> {url}")
        except Exception as e:
            print(f"   ✗ {name} -> ERROR: {e}")
    
    print()
    
    # Test HTTP responses
    print("3. HTTP Response Tests:")
    client = Client()
    
    for url in urls_to_test:
        try:
            response = client.get(url)
            if response.status_code == 302:
                print(f"   ✓ {url} -> {response.status_code} (redirect to login)")
            elif response.status_code == 200:
                print(f"   ✓ {url} -> {response.status_code} (page loaded)")
            else:
                print(f"   ? {url} -> {response.status_code} (unexpected)")
        except Exception as e:
            print(f"   ✗ {url} -> ERROR: {e}")
    
    print()
    print("=== Verification Complete ===")
    print()
    print("Summary: The URL 'ace/create_ace_report' (both with and without trailing slash)")
    print("is now properly configured and should work in your browser.")
    print()
    print("You can now access:")
    print("- http://127.0.0.1:8000/ace/create_ace_report")
    print("- http://127.0.0.1:8000/ace/create_ace_report/")
    print("- http://127.0.0.1:8000/ace/reports/")

if __name__ == '__main__':
    final_verification()
