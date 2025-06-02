#!/usr/bin/env python3
"""
Simple test script to check API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n=== Testing {url} ===")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Data type: {type(data)}")
                print(f"Data length: {len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"Sample item: {data[0]}")
                elif isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
            except json.JSONDecodeError:
                print(f"Response text: {response.text[:200]}...")
        else:
            print(f"Error response: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Is Django running?")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    
    # Test all three applications
    endpoints = [
        "/comperative_schedule/api/users/",
        "/comperative_schedule/api/suppliers/",
        "/comperative_schedule/api/restricted_bidding/cs/CS20240618071337/",
        "/direct_purchase/api/users/",
        "/direct_purchase/api/suppliers/", 
        "/ristricted_bidding/api/users/",
        "/ristricted_bidding/api/suppliers/",
    ]
    
    for endpoint in endpoints:
        test_api_endpoint(endpoint) 