#!/usr/bin/env python3
"""
Test script to verify DirectPurchase URL patterns are working correctly.
Run this with: python manage.py shell < finance/direct_purchase/test_urls.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.urls import reverse
from django.test import Client

def test_urls():
    """Test that the key URLs are accessible"""
    
    print("🔍 Testing DirectPurchase URL patterns...")
    
    # Test the new API endpoint
    try:
        url = reverse('direct_purchase:api_files_create_data', kwargs={'pr_id': 'PR90000001'})
        print(f"✅ api_files_create_data URL: {url}")
    except Exception as e:
        print(f"❌ api_files_create_data URL failed: {e}")
    
    # Test the existing endpoint
    try:
        url = reverse('direct_purchase:get_create_data', kwargs={'pr_id': 'PR90000001'})
        print(f"✅ get_create_data URL: {url}")
    except Exception as e:
        print(f"❌ get_create_data URL failed: {e}")
    
    # Test the optimized file URLs
    try:
        url = reverse('direct_purchase:dp_files_upload_file')
        print(f"✅ dp_files_upload_file URL: {url}")
    except Exception as e:
        print(f"❌ dp_files_upload_file URL failed: {e}")
    
    print("\n🔍 Testing URL resolution...")
    
    # Test with a client
    client = Client()
    
    # Test the new API endpoint
    test_url = '/direct_purchase/api/files/create-data/PR90000001/'
    print(f"Testing URL: {test_url}")
    
    try:
        response = client.get(test_url)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✅ URL is accessible!")
        elif response.status_code == 404:
            print("❌ URL returned 404 - not found")
        else:
            print(f"⚠️  URL returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing URL: {e}")

if __name__ == '__main__':
    test_urls()
