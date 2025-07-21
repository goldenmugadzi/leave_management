#!/usr/bin/env python
"""
Test script to verify the ACE create report page loads correctly
"""
import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

def test_ace_create_report_page():
    """Test the ACE create report page"""
    print("Testing ACE create report page...")
    
    client = Client()
    User = get_user_model()
    
    # Try to access the page without authentication (should redirect to login)
    try:
        response = client.get('/ace/create_ace_report/')
        print(f"✓ Unauthenticated access: {response.status_code} (should be 302 redirect)")
        
        if response.status_code == 302:
            print(f"  Redirected to: {response.url}")
        
    except Exception as e:
        print(f"✗ Error testing unauthenticated access: {e}")
    
    # Test URL reverse lookup
    try:
        url = reverse('Ace:create_ace_report')
        print(f"✓ URL reverse lookup: {url}")
        
    except Exception as e:
        print(f"✗ Error with URL reverse lookup: {e}")

if __name__ == '__main__':
    test_ace_create_report_page()
