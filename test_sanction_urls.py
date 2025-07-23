#!/usr/bin/env python
"""
Simple verification test for sanction_for_test application
"""

import requests
import time

def test_url(url, description):
    """Test if a URL is accessible"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✓ {description}: {url} (Status: {response.status_code})")
            return True
        else:
            print(f"✗ {description}: {url} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ {description}: {url} - Error: {e}")
        return False

def main():
    print("Sanction For Test - URL Accessibility Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Test URLs
    urls_to_test = [
        (f"{base_url}/", "Main page"),
        (f"{base_url}/sanction_for_test/", "Sanction For Test List"),
        (f"{base_url}/sanction_for_test/create/", "Create Form"),
        (f"{base_url}/sanction_for_test/reports/", "Reports Page"),
    ]
    
    passed = 0
    total = len(urls_to_test)
    
    for url, description in urls_to_test:
        if test_url(url, description):
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} URLs accessible")
    
    if passed == total:
        print("\n🎉 ALL URLS ACCESSIBLE!")
        print("The Sanction For Test application is working!")
    else:
        print(f"\n❌ {total - passed} URL(s) failed")

if __name__ == "__main__":
    main()
