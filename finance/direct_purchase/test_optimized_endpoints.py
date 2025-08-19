#!/usr/bin/env python3
"""
Test Script for Optimized File Handling Endpoints
Tests all new endpoints to ensure they work correctly
"""

import os
import sys
import django
import requests
import json
import tempfile
from pathlib import Path
import base64

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from finance.purchase_request.models import PurchaseRequest, Attachment
from finance.comparative_schedules.models import ComparativeSchedules, Bids
from finance.comparative_schedules.optimized_file_handlers import OptimizedFileHandler, OptimizedAttachmentHandler

User = get_user_model()

class OptimizedFileHandlersTest(TestCase):
    """Test class for optimized file handlers"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test PR
        self.purchase_request = PurchaseRequest.objects.create(
            pr_no='12345678',
            requested_by=self.user,
            scope_of_work='Test PR for file handling'
        )
        
        # Create test CS
        self.cs = ComparativeSchedules.objects.create(
            cs_id='CS001',
            pr_id=self.purchase_request,
            pr_date='2024-01-01',
            scope_of_work='Test CS',
            closing_date='2024-02-01',
            closing_time='17:00',
            advert='',
            pr_number='PR12345678',
            cs_opened='2024-01-01',
            tac_date='2024-01-01',
            created_by=self.user
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create test file
        self.test_file_content = b'This is a test file content for testing file uploads.'
        self.test_file = SimpleUploadedFile(
            'test_document.txt',
            self.test_file_content,
            content_type='text/plain'
        )
    
    def test_optimized_file_handler_creation(self):
        """Test OptimizedFileHandler creation"""
        handler = OptimizedFileHandler(self.user)
        self.assertIsNotNone(handler)
        self.assertEqual(handler.user, self.user)
    
    def test_optimized_attachment_handler_creation(self):
        """Test OptimizedAttachmentHandler creation"""
        handler = OptimizedAttachmentHandler(self.user)
        self.assertIsNotNone(handler)
        self.assertEqual(handler.user, self.user)
    
    def test_file_validation(self):
        """Test file validation"""
        handler = OptimizedFileHandler(self.user)
        
        # Test valid file
        valid_file = SimpleUploadedFile(
            'test.pdf',
            b'PDF content',
            content_type='application/pdf'
        )
        self.assertTrue(handler.validate_file(valid_file))
        
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            'test.exe',
            b'Executable content',
            content_type='application/x-executable'
        )
        with self.assertRaises(Exception):
            handler.validate_file(invalid_file)
    
    def test_file_metadata_generation(self):
        """Test file metadata generation"""
        handler = OptimizedFileHandler(self.user)
        metadata = handler.generate_file_metadata(self.test_file)
        
        self.assertIn('original_name', metadata)
        self.assertIn('size', metadata)
        self.assertIn('extension', metadata)
        self.assertIn('uploaded_by', metadata)
        self.assertIn('uploaded_at', metadata)
        self.assertEqual(metadata['original_name'], 'test_document.txt')
        self.assertEqual(metadata['size'], len(self.test_file_content))
    
    def test_save_file_optimized(self):
        """Test optimized file saving"""
        handler = OptimizedFileHandler(self.user)
        result = handler.save_file_optimized(self.test_file, 'test', 'Test file')
        
        self.assertIsNotNone(result)
        self.assertIn('file_path', result)
        self.assertIn('metadata', result)
        self.assertIn('download_url', result)
        self.assertIn('preview_url', result)
        
        # Check if file was actually saved
        self.assertTrue(os.path.exists(handler.fs.path(result['file_path'])))
    
    def test_get_attachments_metadata(self):
        """Test getting attachment metadata"""
        # Create test attachment
        attachment = Attachment.objects.create(
            file=self.test_file,
            purchase_request=self.purchase_request
        )
        
        handler = OptimizedAttachmentHandler(self.user)
        metadata_list = handler.get_attachments_metadata([attachment])
        
        self.assertEqual(len(metadata_list), 1)
        metadata = metadata_list[0]
        self.assertIn('id', metadata)
        self.assertIn('name', metadata)
        self.assertIn('size', metadata)
        self.assertIn('download_url', metadata)
        self.assertEqual(metadata['id'], attachment.id)
    
    def test_api_upload_file_optimized(self):
        """Test optimized file upload API endpoint"""
        url = '/comparative_schedules/api/files/upload/'
        
        with open('test_upload.txt', 'wb') as f:
            f.write(b'Test upload content')
        
        with open('test_upload.txt', 'rb') as f:
            response = self.client.post(url, {
                'file': f,
                'file_type': 'test',
                'description': 'Test upload'
            })
        
        # Clean up
        os.remove('test_upload.txt')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('file_path', data)
        self.assertIn('metadata', data)
        self.assertIn('download_url', data)
    
    def test_api_get_attachments_optimized(self):
        """Test optimized attachments API endpoint"""
        # Create test attachment
        attachment = Attachment.objects.create(
            file=self.test_file,
            purchase_request=self.purchase_request
        )
        
        url = f'/comparative_schedules/api/files/attachments/{self.purchase_request.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('pr_attachments', data)
        self.assertIn('total_count', data)
        self.assertEqual(data['total_count'], 1)
        
        attachment_data = data['pr_attachments'][0]
        self.assertIn('id', attachment_data)
        self.assertIn('name', attachment_data)
        self.assertIn('download_url', attachment_data)
        self.assertNotIn('file', attachment_data)  # No Base64 data
    
    def test_api_get_create_data_optimized(self):
        """Test optimized create data API endpoint"""
        # Create test attachment
        attachment = Attachment.objects.create(
            file=self.test_file,
            purchase_request=self.purchase_request
        )
        
        url = f'/comparative_schedules/api/files/create-data/{self.purchase_request.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('pr_attachments', data)
        
        # Check that attachments don't contain Base64 data
        for attachment_data in data['pr_attachments']:
            self.assertNotIn('file', attachment_data)  # No Base64 data
            self.assertIn('download_url', attachment_data)
    
    def test_api_get_cs_files_optimized(self):
        """Test optimized CS files API endpoint"""
        # Set advert file path
        self.cs.advert = 'uploads/test_advert.pdf'
        self.cs.save()
        
        url = f'/comparative_schedules/api/files/cs-files/{self.cs.cs_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('cs_files', data)
        self.assertIn('total_count', data)
    
    def test_file_download_optimized(self):
        """Test optimized file download"""
        handler = OptimizedFileHandler(self.user)
        result = handler.save_file_optimized(self.test_file, 'test', 'Test file')
        
        url = f'/comparative_schedules/api/files/download/{result["file_path"]}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('Content-Disposition', response)
    
    def test_file_preview_optimized(self):
        """Test optimized file preview"""
        handler = OptimizedFileHandler(self.user)
        result = handler.save_file_optimized(self.test_file, 'test', 'Test file')
        
        url = f'/comparative_schedules/api/files/preview/{result["file_path"]}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('preview', data)
        self.assertIn('preview_type', data)
    
    def test_file_delete_optimized(self):
        """Test optimized file deletion"""
        handler = OptimizedFileHandler(self.user)
        result = handler.save_file_optimized(self.test_file, 'test', 'Test file')
        
        # Verify file exists
        self.assertTrue(os.path.exists(handler.fs.path(result['file_path'])))
        
        url = f'/comparative_schedules/api/files/delete/{result["file_path"]}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify file was deleted
        self.assertFalse(os.path.exists(handler.fs.path(result['file_path'])))
    
    def test_error_handling(self):
        """Test error handling"""
        # Test non-existent file download
        url = '/comparative_schedules/api/files/download/nonexistent/file.txt/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
        # Test non-existent PR
        url = '/comparative_schedules/api/files/attachments/PR99999999/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('PR not found', data['message'])
    
    def test_performance_comparison(self):
        """Test performance comparison between old and new approaches"""
        import time
        
        # Create multiple attachments
        attachments = []
        for i in range(5):
            file_content = f'Test file content {i}'.encode()
            test_file = SimpleUploadedFile(
                f'test_file_{i}.txt',
                file_content,
                content_type='text/plain'
            )
            attachment = Attachment.objects.create(
                file=test_file,
                purchase_request=self.purchase_request
            )
            attachments.append(attachment)
        
        # Test optimized approach
        handler = OptimizedAttachmentHandler(self.user)
        
        start_time = time.time()
        metadata_list = handler.get_attachments_metadata(attachments)
        optimized_time = time.time() - start_time
        
        # Test old approach (simulated)
        start_time = time.time()
        old_list = []
        for attachment in attachments:
            if attachment.file and attachment.file.size < 5 * 1024 * 1024:
                file_data = attachment.file.read()
                encoded_data = base64.b64encode(file_data).decode('utf-8')
                old_list.append({
                    "id": attachment.id,
                    "file": encoded_data,
                    "name": os.path.basename(attachment.file.name),
                })
        old_time = time.time() - start_time
        
        # Optimized should be faster
        self.assertLess(optimized_time, old_time)
        print(f"Optimized time: {optimized_time:.4f}s")
        print(f"Old approach time: {old_time:.4f}s")
        print(f"Performance improvement: {((old_time - optimized_time) / old_time) * 100:.1f}%")
    
    def tearDown(self):
        """Clean up test files"""
        # Clean up any test files created
        test_files = [
            'test_upload.txt',
            'test_document.txt'
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)


def run_manual_tests():
    """Run manual tests for endpoints"""
    print("🚀 Starting Manual Tests for Optimized File Handling Endpoints")
    print("=" * 60)
    
    # Test data
    base_url = "http://localhost:8000"
    test_user = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    # Test endpoints
    endpoints = [
        {
            "name": "File Upload",
            "url": f"{base_url}/comparative_schedules/api/files/upload/",
            "method": "POST",
            "data": {"file_type": "test", "description": "Manual test"}
        },
        {
            "name": "Get Attachments",
            "url": f"{base_url}/comparative_schedules/api/files/attachments/PR12345678/",
            "method": "GET"
        },
        {
            "name": "Get Create Data",
            "url": f"{base_url}/comparative_schedules/api/files/create-data/PR12345678/",
            "method": "GET"
        },
        {
            "name": "Get CS Files",
            "url": f"{base_url}/comparative_schedules/api/files/cs-files/CS001/",
            "method": "GET"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n📋 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        print(f"Method: {endpoint['method']}")
        
        try:
            if endpoint['method'] == 'POST':
                # Create test file for upload
                with open('manual_test.txt', 'w') as f:
                    f.write('Manual test file content')
                
                with open('manual_test.txt', 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        endpoint['url'],
                        files=files,
                        data=endpoint['data']
                    )
                
                os.remove('manual_test.txt')
            else:
                response = requests.get(endpoint['url'])
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success', 'N/A')}")
                if 'pr_attachments' in data:
                    print(f"Attachments Count: {len(data['pr_attachments'])}")
                    if data['pr_attachments']:
                        attachment = data['pr_attachments'][0]
                        print(f"Sample Attachment: {attachment.get('name', 'N/A')}")
                        print(f"Has Download URL: {'download_url' in attachment}")
                        print(f"No Base64 Data: {'file' not in attachment}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n✅ Manual tests completed!")


if __name__ == "__main__":
    print("🧪 Testing Optimized File Handling Endpoints")
    print("=" * 50)
    
    # Run Django tests
    print("\n1. Running Django Unit Tests...")
    import django.test.utils
    runner = django.test.utils.DiscoverRunner()
    runner.run_tests(['finance.comparative_schedules.test_optimized_endpoints'])
    
    # Run manual tests
    print("\n2. Running Manual Tests...")
    run_manual_tests()
    
    print("\n🎉 All tests completed!")
