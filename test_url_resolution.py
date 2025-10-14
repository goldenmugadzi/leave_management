#!/usr/bin/env python
"""
Test script to check URL resolution for deploy_team view.
"""

import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

import django
django.setup()

# Test URL resolution
from django.urls import reverse, resolve
from django.test import Client

def test_url_resolution():
    """Test that the deploy_team URL resolves correctly"""
    
    print("🔍 Testing URL resolution for deploy_team...")
    
    try:
        # Test reverse URL resolution
        url = reverse('deploy_team')
        print(f"✅ Reverse URL resolution successful: {url}")
        
        # Test URL pattern matching
        resolved = resolve(url)
        print(f"✅ URL pattern resolution successful: {resolved.func.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL resolution failed: {e}")
        return False

def test_simple_request():
    """Test a simple request to the deploy_team view"""
    
    print("🔍 Testing simple request without authentication...")
    
    try:
        client = Client()
        response = client.get('/fault_locator/teams/deploy/')
        
        print(f"✅ Request successful, status: {response.status_code}")
        
        if response.status_code == 302:
            print("⚠️ Response is a redirect (likely for login)")
            location = response.get('Location', 'Unknown')
            print(f"Redirect location: {location}")
        
        return True
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing URL Resolution and Simple Request")
    print("=" * 60)
    
    # Test URL resolution
    url_ok = test_url_resolution()
    
    # Test simple request
    req_ok = test_simple_request()
    
    print("\n" + "=" * 60)
    if url_ok and req_ok:
        print("✅ URL tests passed!")
    else:
        print("❌ URL tests failed.")
    
    print("=" * 60)
