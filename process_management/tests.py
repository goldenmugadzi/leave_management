from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch, mock_open
import os
import tempfile
from it.users.models import UserProfile, Regions
from .models import ProcessDepartment, Process, ProcessDocument


class DocumentDownloadTestCase(TestCase):
    """
    Test cases for document download functionality.
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create user profile
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            employee_number='EMP001'
        )
        
        # Create test department
        self.department = ProcessDepartment.objects.create(
            name='Test Department',
            description='Test department for testing',
            order=1
        )
        
        # Create test process
        self.process = Process.objects.create(
            name='Test Process',
            description='Test process for testing',
            department=self.department,
            created_by=self.user_profile
        )
        
        # Create test document with mock file
        self.test_file_content = b'Test PDF content'
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            self.test_file_content,
            content_type="application/pdf"
        )
        
        self.document = ProcessDocument.objects.create(
            process=self.process,
            document_type='process_map',
            file=self.test_file,
            filename='test_document.pdf',
            version='1.0',
            uploaded_by=self.user_profile
        )
    
    def test_document_download_requires_authentication(self):
        """Test that document download requires authentication"""
        url = reverse('process_management:document_download', args=[self.document.id])
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_document_download_authenticated_user(self):
        """Test document download for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        
        # Mock file existence and content
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=self.test_file_content)):
            
            url = reverse('process_management:document_download', args=[self.document.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('inline', response['Content-Disposition'])
            self.assertIn('test_document.pdf', response['Content-Disposition'])
    
    def test_document_download_nonexistent_document(self):
        """Test download of non-existent document"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('process_management:document_download', args=[99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_document_download_missing_file(self):
        """Test download when document file is missing"""
        self.client.login(username='testuser', password='testpass123')
        
        # Mock file not existing
        with patch('os.path.exists', return_value=False):
            url = reverse('process_management:document_download', args=[self.document.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 404)
    
    def test_document_download_io_error(self):
        """Test download when file cannot be read"""
        self.client.login(username='testuser', password='testpass123')
        
        # Mock file exists but cannot be opened
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("Cannot read file")):
            
            url = reverse('process_management:document_download', args=[self.document.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 404)
    
    def test_document_download_by_process_and_type(self):
        """Test document download by process and type"""
        self.client.login(username='testuser', password='testpass123')
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=self.test_file_content)):
            
            url = reverse('process_management:document_download_by_type', 
                         args=[self.process.id, 'process_map'])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_document_download_by_type_invalid_type(self):
        """Test download with invalid document type"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('process_management:document_download_by_type', 
                     args=[self.process.id, 'invalid_type'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_document_download_by_type_no_document(self):
        """Test download when no document of specified type exists"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('process_management:document_download_by_type', 
                     args=[self.process.id, 'procedure'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_document_download_by_type_nonexistent_process(self):
        """Test download for non-existent process"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('process_management:document_download_by_type', 
                     args=[99999, 'process_map'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_document_download_content_type_detection(self):
        """Test content type detection for different file types"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test different file types
        test_cases = [
            ('test.pdf', 'application/pdf', 'inline'),
            ('test.doc', 'application/msword', 'attachment'),
            ('test.jpg', 'image/jpeg', 'inline'),
            ('test.unknown', 'application/octet-stream', 'attachment'),
        ]
        
        for filename, expected_content_type, expected_disposition in test_cases:
            # Update document filename
            self.document.filename = filename
            self.document.save()
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=b'test content')):
                
                url = reverse('process_management:document_download', args=[self.document.id])
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], expected_content_type)
                self.assertIn(expected_disposition, response['Content-Disposition'])
    
    def test_document_download_security_headers(self):
        """Test that security headers are set correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=self.test_file_content)):
            
            url = reverse('process_management:document_download', args=[self.document.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(response['X-Frame-Options'], 'DENY')
            self.assertIn('Cache-Control', response)
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up any uploaded files
        if self.document.file:
            try:
                os.remove(self.document.file.path)
            except (OSError, ValueError):
                pass


class DocumentUploadTestCase(TestCase):
    """
    Test cases for document upload functionality.
    Requirements: 2.2, 2.3
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create user profile
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            employee_number='EMP001'
        )
        
        # Create test department
        self.department = ProcessDepartment.objects.create(
            name='Test Department',
            description='Test department for testing',
            order=1
        )
        
        # Create test process
        self.process = Process.objects.create(
            name='Test Process',
            description='Test process for testing',
            department=self.department,
            created_by=self.user_profile
        )
    
    def test_document_upload_view_get(self):
        """Test GET request to upload view"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('process_management:document_upload', args=[self.process.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload Document')
        self.assertContains(response, self.process.name)
    
    def test_document_upload_requires_authentication(self):
        """Test that upload requires authentication"""
        url = reverse('process_management:document_upload', args=[self.process.id])
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_document_upload_valid_file(self):
        """Test uploading a valid document"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create test file
        test_file = SimpleUploadedFile(
            "test_process_map.pdf",
            b"Test PDF content",
            content_type="application/pdf"
        )
        
        url = reverse('process_management:document_upload', args=[self.process.id])
        response = self.client.post(url, {
            'document_type': 'process_map',
            'document_file': test_file,
            'version': '1.0',
        })
        
        # Should redirect to process detail
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'/detail/{self.process.id}/', response.url)
        
        # Check document was created
        document = ProcessDocument.objects.get(process=self.process, document_type='process_map')
        self.assertEqual(document.filename, 'test_process_map.pdf')
        self.assertEqual(document.version, '1.0')
        self.assertTrue(document.is_current)
    
    def test_document_upload_missing_file(self):
        """Test upload without file"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('process_management:document_upload', args=[self.process.id])
        response = self.client.post(url, {
            'document_type': 'process_map',
            'version': '1.0',
        })
        
        # Should return to upload form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Document type and file are required')
    
    def test_document_upload_invalid_type(self):
        """Test upload with invalid document type"""
        self.client.login(username='testuser', password='testpass123')
        
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"Test content",
            content_type="application/pdf"
        )
        
        url = reverse('process_management:document_upload', args=[self.process.id])
        response = self.client.post(url, {
            'document_type': 'invalid_type',
            'document_file': test_file,
            'version': '1.0',
        })
        
        # Should return to upload form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid document type')
    
    def test_document_upload_replace_current(self):
        """Test uploading with replace current option"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create existing document
        existing_file = SimpleUploadedFile(
            "existing.pdf",
            b"Existing content",
            content_type="application/pdf"
        )
        existing_doc = ProcessDocument.objects.create(
            process=self.process,
            document_type='process_map',
            file=existing_file,
            filename='existing.pdf',
            version='1.0',
            is_current=True,
            uploaded_by=self.user_profile
        )
        
        # Upload new document with replace option
        new_file = SimpleUploadedFile(
            "new.pdf",
            b"New content",
            content_type="application/pdf"
        )
        
        url = reverse('process_management:document_upload', args=[self.process.id])
        response = self.client.post(url, {
            'document_type': 'process_map',
            'document_file': new_file,
            'version': '2.0',
            'replace_current': 'on',
        })
        
        # Should redirect successfully
        self.assertEqual(response.status_code, 302)
        
        # Check old document is no longer current
        existing_doc.refresh_from_db()
        self.assertFalse(existing_doc.is_current)
        
        # Check new document is current
        new_doc = ProcessDocument.objects.get(process=self.process, version='2.0')
        self.assertTrue(new_doc.is_current)
    
    def test_file_validation_size_limit(self):
        """Test file size validation"""
        from process_management.views import validate_uploaded_file
        
        # Mock large file
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (51 * 1024 * 1024),  # 51MB
            content_type="application/pdf"
        )
        
        result = validate_uploaded_file(large_file)
        self.assertFalse(result['valid'])
        self.assertIn('exceeds maximum allowed size', result['error'])
    
    def test_file_validation_extension(self):
        """Test file extension validation"""
        from process_management.views import validate_uploaded_file
        
        # Invalid extension
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"Test content",
            content_type="application/octet-stream"
        )
        
        result = validate_uploaded_file(invalid_file)
        self.assertFalse(result['valid'])
        self.assertIn('not allowed', result['error'])
    
    def test_file_validation_empty_file(self):
        """Test empty file validation"""
        from process_management.views import validate_uploaded_file
        
        # Empty file
        empty_file = SimpleUploadedFile(
            "empty.pdf",
            b"",
            content_type="application/pdf"
        )
        
        result = validate_uploaded_file(empty_file)
        self.assertFalse(result['valid'])
        self.assertIn('empty', result['error'])
    
    def test_file_validation_dangerous_filename(self):
        """Test dangerous filename validation"""
        from process_management.views import validate_uploaded_file
        
        # Dangerous filename
        dangerous_file = SimpleUploadedFile(
            "../../../etc/passwd",
            b"Test content",
            content_type="application/pdf"
        )
        
        result = validate_uploaded_file(dangerous_file)
        self.assertFalse(result['valid'])
        self.assertIn('invalid characters', result['error'])
    
    def test_virus_scan_clean_file(self):
        """Test virus scanning for clean file"""
        from process_management.views import perform_virus_scan
        
        clean_file = SimpleUploadedFile(
            "clean.pdf",
            b"Clean PDF content",
            content_type="application/pdf"
        )
        
        result = perform_virus_scan(clean_file)
        self.assertTrue(result['clean'])
        self.assertIsNone(result['threat'])
    
    def test_virus_scan_suspicious_content(self):
        """Test virus scanning for suspicious content"""
        from process_management.views import perform_virus_scan
        
        suspicious_file = SimpleUploadedFile(
            "suspicious.pdf",
            b"<script>alert('xss')</script>",
            content_type="application/pdf"
        )
        
        result = perform_virus_scan(suspicious_file)
        self.assertFalse(result['clean'])
        self.assertIsNotNone(result['threat'])
    
    def test_document_replace_view_get(self):
        """Test GET request to replace view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create existing document
        test_file = SimpleUploadedFile(
            "existing.pdf",
            b"Existing content",
            content_type="application/pdf"
        )
        document = ProcessDocument.objects.create(
            process=self.process,
            document_type='process_map',
            file=test_file,
            filename='existing.pdf',
            version='1.0',
            is_current=True,
            uploaded_by=self.user_profile
        )
        
        url = reverse('process_management:document_replace', args=[document.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Replace Document')
        self.assertContains(response, document.filename)
    
    def test_document_replace_post(self):
        """Test POST request to replace document"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create existing document
        existing_file = SimpleUploadedFile(
            "existing.pdf",
            b"Existing content",
            content_type="application/pdf"
        )
        document = ProcessDocument.objects.create(
            process=self.process,
            document_type='process_map',
            file=existing_file,
            filename='existing.pdf',
            version='1.0',
            is_current=True,
            uploaded_by=self.user_profile
        )
        
        # Replace with new file
        new_file = SimpleUploadedFile(
            "new.pdf",
            b"New content",
            content_type="application/pdf"
        )
        
        url = reverse('process_management:document_replace', args=[document.id])
        response = self.client.post(url, {
            'document_file': new_file,
            'version': '2.0',
        })
        
        # Should redirect to process detail
        self.assertEqual(response.status_code, 302)
        
        # Check old document is no longer current
        document.refresh_from_db()
        self.assertFalse(document.is_current)
        
        # Check new document exists and is current
        new_doc = ProcessDocument.objects.get(process=self.process, version='2.0')
        self.assertTrue(new_doc.is_current)
        self.assertEqual(new_doc.filename, 'new.pdf')
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up any uploaded files
        for document in ProcessDocument.objects.all():
            if document.file:
                try:
                    os.remove(document.file.path)
                except (OSError, ValueError):
                    pass