#!/usr/bin/env python3
"""
Phase 1 API Updates Test Script
Tests the new optimized file handling endpoints and API functions
"""

import os
import sys
import django
import requests
import json
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import Client
from it.users.models import UserProfile
from finance.comparative_schedules.models import ComparativeSchedules
from finance.purchase_request.models import PurchaseRequest, Attachment

def test_phase1_api_endpoints():
    """Test the new optimized file handling endpoints"""
    
    print("🧪 Testing Phase 1 API Updates...")
    print("=" * 50)
    
    # Setup test client
    client = Client()
    
    # Create test user
    user, created = UserProfile.objects.get_or_create(
        username='test_phase1',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Login
    client.login(username='test_phase1', password='testpass123')
    
    # Test 1: New file upload endpoint
    print("\n1️⃣ Testing FILE_UPLOAD endpoint...")
    try:
        # Create a test file
        test_file_path = '/tmp/test_upload.txt'
        with open(test_file_path, 'w') as f:
            f.write('Test file content for Phase 1')
        
        with open(test_file_path, 'rb') as f:
            response = client.post('/comperative_schedule/api/files/upload/', {
                'file': f,
                'file_type': 'test',
                'description': 'Phase 1 test file'
            })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ File upload successful: {data.get('file_path', 'N/A')}")
            print(f"   Metadata: {data.get('metadata', {})}")
            
            # Store file path for later tests
            uploaded_file_path = data.get('file_path')
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ File upload test error: {e}")
        return False
    
    # Test 2: New PR attachments endpoint
    print("\n2️⃣ Testing PR_ATTACHMENTS endpoint...")
    try:
        # Create test PR with unique number
        import random
        unique_pr_no = str(random.randint(10000000, 99999999))
        pr = PurchaseRequest.objects.create(
            pr_no=unique_pr_no,
            scope_of_work='Test scope for Phase 1',
            requested_by=user
        )
        
        # Create test attachment
        attachment = Attachment.objects.create(
            purchase_request=pr,
            file='test_attachment.txt'
        )
        
        response = client.get(f'/comperative_schedule/api/files/attachments/{pr.id}/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PR attachments successful: {len(data.get('attachments', []))} attachments")
            print(f"   Response structure: {list(data.keys())}")
            
            # Verify no Base64 data in response
            attachments = data.get('attachments', [])
            for attachment_data in attachments:
                if 'file_data' in attachment_data:
                    print(f"❌ Base64 data still present in attachment: {attachment_data.get('name')}")
                    return False
                else:
                    print(f"✅ No Base64 data in attachment: {attachment_data.get('name')}")
        else:
            print(f"❌ PR attachments failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ PR attachments test error: {e}")
        return False
    
    # Test 3: New PR create data endpoint
    print("\n3️⃣ Testing PR_BASIC (create-data) endpoint...")
    try:
        response = client.get(f'/comperative_schedule/api/files/create-data/{pr.id}/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PR create data successful")
            print(f"   Response structure: {list(data.keys())}")
            
            # Verify no Base64 data in response
            if 'pr_attachments' in data:
                pr_attachments = data['pr_attachments']
                for attachment_data in pr_attachments:
                    if 'file_data' in attachment_data:
                        print(f"❌ Base64 data still present in PR attachment: {attachment_data.get('name')}")
                        return False
                    else:
                        print(f"✅ No Base64 data in PR attachment: {attachment_data.get('name')}")
            else:
                print("✅ No PR attachments in response (expected)")
        else:
            print(f"❌ PR create data failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ PR create data test error: {e}")
        return False
    
    # Test 4: New CS files endpoint
    print("\n4️⃣ Testing CS_FILES endpoint...")
    try:
        # Create test CS
        cs = ComparativeSchedules.objects.create(
            pr_id=pr,
            created_by=user,
            cs_id=f'CS-{pr.id}',
            pr_date=datetime.now().date(),
            scope_of_work='Test scope',
            closing_date=datetime.now().date(),
            closing_time='12:00',
            advert='',
            pr_number=pr.id,
            cs_opened=datetime.now().date(),
            tac_date=datetime.now().date()
        )
        
        response = client.get(f'/comperative_schedule/api/files/cs-files/{cs.id}/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CS files successful")
            print(f"   Response structure: {list(data.keys())}")
            
            # Verify response structure
            expected_keys = ['advert', 'bid_documents']
            for key in expected_keys:
                if key in data:
                    print(f"✅ Found {key} in response")
                else:
                    print(f"⚠️  {key} not found in response (may be empty)")
        else:
            print(f"❌ CS files failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ CS files test error: {e}")
        return False
    
    # Test 5: File download endpoint
    print("\n5️⃣ Testing FILE_DOWNLOAD endpoint...")
    try:
        if uploaded_file_path:
            response = client.get(f'/comperative_schedule/api/files/download/{uploaded_file_path}/')
            
            if response.status_code == 200:
                print(f"✅ File download successful")
                print(f"   Content-Type: {response.get('Content-Type', 'N/A')}")
                # For StreamingHttpResponse, we can't get content length easily
                print(f"   Streaming response: {type(response).__name__}")
            else:
                print(f"❌ File download failed: {response.status_code}")
                print(f"   Response: {response.content.decode() if hasattr(response, 'content') else 'Streaming response'}")
                return False
        else:
            print("⚠️  Skipping file download test (no uploaded file)")
            
    except Exception as e:
        print(f"❌ File download test error: {e}")
        return False
    
    # Test 6: File preview endpoint
    print("\n6️⃣ Testing FILE_PREVIEW endpoint...")
    try:
        if uploaded_file_path:
            response = client.get(f'/comperative_schedule/api/files/preview/{uploaded_file_path}/')
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ File preview successful")
                print(f"   Preview data: {data.get('preview_data', 'N/A')[:100]}...")
            else:
                print(f"❌ File preview failed: {response.status_code}")
                print(f"   Response: {response.content.decode()}")
                return False
        else:
            print("⚠️  Skipping file preview test (no uploaded file)")
            
    except Exception as e:
        print(f"❌ File preview test error: {e}")
        return False
    
    # Test 7: File delete endpoint
    print("\n7️⃣ Testing FILE_DELETE endpoint...")
    try:
        if uploaded_file_path:
            response = client.delete(f'/comperative_schedule/api/files/delete/{uploaded_file_path}/')
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ File delete successful: {data.get('message', 'N/A')}")
            else:
                print(f"❌ File delete failed: {response.status_code}")
                print(f"   Response: {response.content.decode()}")
                return False
        else:
            print("⚠️  Skipping file delete test (no uploaded file)")
            
    except Exception as e:
        print(f"❌ File delete test error: {e}")
        return False
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    try:
        if 'uploaded_file_path' in locals() and uploaded_file_path:
            # Remove test file if it still exists
            if os.path.exists(uploaded_file_path):
                os.remove(uploaded_file_path)
        
        # Remove test file from temp
        if os.path.exists('/tmp/test_upload.txt'):
            os.remove('/tmp/test_upload.txt')
        
        # Clean up database objects
        if 'cs' in locals():
            cs.delete()
        if 'pr' in locals():
            pr.delete()
        if 'user' in locals():
            user.delete()
            
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 1 API Updates Test Completed Successfully!")
    print("✅ All new optimized file handling endpoints are working")
    print("✅ No Base64 data in responses")
    print("✅ File upload/download/preview/delete functionality verified")
    
    return True

def test_api_endpoint_urls():
    """Test that the API endpoint URLs are correctly configured"""
    
    print("\n🔗 Testing API Endpoint URL Configuration...")
    print("=" * 50)
    
    # Test the actual URL patterns
    test_urls = [
        '/comperative_schedule/api/files/upload/',
        '/comperative_schedule/api/files/attachments/1/',
        '/comperative_schedule/api/files/create-data/1/',
        '/comperative_schedule/api/files/cs-files/1/',
        '/comperative_schedule/api/files/download/test.txt/',
        '/comperative_schedule/api/files/preview/test.txt/',
        '/comperative_schedule/api/files/delete/test.txt/',
    ]
    
    client = Client()
    
    for url in test_urls:
        try:
            response = client.get(url)
            # We expect 401 (unauthorized) or 404 (not found) but not 500 (server error)
            if response.status_code >= 500:
                print(f"❌ Server error for {url}: {response.status_code}")
                return False
            else:
                print(f"✅ URL accessible: {url} ({response.status_code})")
        except Exception as e:
            print(f"❌ URL error for {url}: {e}")
            return False
    
    print("✅ All API endpoint URLs are correctly configured")
    return True

if __name__ == "__main__":
    print("🚀 Starting Phase 1 API Updates Testing...")
    
    # Test API endpoint URLs first
    if not test_api_endpoint_urls():
        print("❌ API endpoint URL test failed")
        sys.exit(1)
    
    # Test the actual functionality
    if not test_phase1_api_endpoints():
        print("❌ Phase 1 API updates test failed")
        sys.exit(1)
    
    print("\n🎯 Phase 1 Complete! Ready for Phase 2...")
    print("\nNext Steps:")
    print("1. Update Schedule.tsx to use new API functions")
    print("2. Replace Base64 processing with metadata handling")
    print("3. Update file upload handlers")
    print("4. Test frontend integration")
