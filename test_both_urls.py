#!/usr/bin/env python
"""
Test script to verify the ACE create report page loads correctly - both with and without slash
"""
import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def test_both_urls():
    """Test both URL variations"""
    print("Testing both URL variations...")
    
    client = Client()
    
    # Test with trailing slash
    try:
        response = client.get('/ace/create_ace_report/')
        print(f"✓ With slash: {response.status_code} (should be 302 redirect to login)")
        
        if response.status_code == 302:
            print(f"  Redirected to: {response.url}")
        elif response.status_code == 200:
            print(f"  Page loaded successfully")
        
    except Exception as e:
        print(f"✗ Error with slash: {e}")
    
    # Test without trailing slash
    try:
        response = client.get('/ace/create_ace_report')
        print(f"✓ Without slash: {response.status_code} (should be 302 redirect to login)")
        
        if response.status_code == 302:
            print(f"  Redirected to: {response.url}")
        elif response.status_code == 200:
            print(f"  Page loaded successfully")
        
    except Exception as e:
        print(f"✗ Error without slash: {e}")

if __name__ == '__main__':
    test_both_urls()
