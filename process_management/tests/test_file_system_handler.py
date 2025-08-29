"""
Tests for file system error handling functionality.

This module tests the comprehensive file system error handling including:
- File accessibility checks
- Path sanitization
- Error recovery strategies
- Integration with migration process
"""
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from process_management.file_system_handler import (
    FileSystemAccessibilityChecker,
    FilePathSanitizer,
    FileSystemErrorHandler,
    FileStatus,
    FileSystemErrorType
)
from process_management.models import ProcessDepartment, Process, ProcessDocument
from it.users.models import UserProfile


class FilePathSanitizerTest(TestCase):
    """Test file path sanitization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sanitizer = FilePathSanitizer()
    
    def test_sanitize_valid_path(self):
        """Test sanitization of a valid path."""
        path = "documents/valid_file.pdf"
        sanitized_path, changes = self.sanitizer.sanitize_path(path)
        
        self.assertEqual(sanitized_path, path)
        self.assertEqual(changes, [])
    
    def test_sanitize_invalid_characters_windows(self):
        """Test sanitization of invalid characters on Windows."""
        with patch('os.name', 'nt'):
            path = 'documents/file<with>invalid:chars.pdf'
            sanitized_path, changes = self.sanitizer.sanitize_path(path)
            
            self.assertNotIn('<', sanitized_path)
            self.assertNotIn('>', sanitized_path)
            self.assertNotIn(':', sanitized_path)
            self.assertTrue(len(changes) > 0)
    
    def test_sanitize_reserved_names(self):
        """Test handling of reserved names."""
        with patch('os.name', 'nt'):
            path = 'CON.txt'
            sanitized_path, changes = self.sanitizer.sanitize_path(path)
            
            self.assertNotEqual(sanitized_path, path)
            self.assertTrue(any('Reserved name handled' in change for change in changes))
    
    def test_sanitize_unicode_normalization(self):
        """Test Unicode normalization."""
        path = 'documents/filé_with_accénts.pdf'
        sanitized_path, changes = self.sanitizer.sanitize_path(path)
        
        # Should normalize Unicode characters
        self.assertIsInstance(sanitized_path, str)
    
    def test_sanitize_long_path(self):
        """Test handling of paths that are too long."""
        long_path = 'a' * 300 + '.txt'
        sanitized_path, changes = self.sanitizer.sanitize_path(long_path)
        
        self.assertLessEqual(len(sanitized_path), self.sanitizer.max_path_length)
        self.assertTrue(any('truncated' in change.lower() for change in changes))
    
    def test_sanitize_empty_filename(self):
        """Test handling of empty filename."""
        path = ''
        sanitized_path, changes = self.sanitizer.sanitize_path(path)
        
        self.assertNotEqual(sanitized_path, '')
        self.assertTrue(len(changes) > 0)


class FileSystemAccessibilityCheckerTest(TestCase):
    """Test file system accessibility checking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.checker = FileSystemAccessibilityChecker(base_path=self.temp_dir)
        
        # Create test files
        self.test_file = os.path.join(self.temp_dir, 'test_file.txt')
        with open(self.test_file, 'w') as f:
            f.write('Test content')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_accessible_file(self):
        """Test checking an accessible file."""
        result = self.checker.check_file_accessibility('test_file.txt')
        
        self.assertEqual(result.status, FileStatus.ACCESSIBLE)
        self.assertTrue(result.is_readable)
        self.assertIsNotNone(result.file_size)
        self.assertIsNone(result.error_type)
    
    def test_check_missing_file(self):
        """Test checking a missing file."""
        result = self.checker.check_file_accessibility('missing_file.txt')
        
        self.assertEqual(result.status, FileStatus.MISSING)
        self.assertEqual(result.error_type, FileSystemErrorType.FILE_NOT_FOUND)
        self.assertIsNotNone(result.error_message)
    
    def test_check_file_with_sanitization(self):
        """Test checking a file that needs path sanitization."""
        with patch('os.name', 'nt'):
            result = self.checker.check_file_accessibility('test<file>.txt')
            
            # Should attempt sanitization and find the file doesn't exist
            self.assertEqual(result.status, FileStatus.MISSING)
            self.assertIsNotNone(result.sanitized_path)
    
    @patch('os.access')
    def test_check_permission_denied(self, mock_access):
        """Test checking a file with permission denied."""
        mock_access.return_value = False
        
        result = self.checker.check_file_accessibility('test_file.txt')
        
        self.assertEqual(result.status, FileStatus.PERMISSION_DENIED)
        self.assertEqual(result.error_type, FileSystemErrorType.PERMISSION_DENIED)
    
    def test_batch_check_files(self):
        """Test batch checking of multiple files."""
        # Create additional test file
        test_file2 = os.path.join(self.temp_dir, 'test_file2.txt')
        with open(test_file2, 'w') as f:
            f.write('Test content 2')
        
        file_paths = ['test_file.txt', 'test_file2.txt', 'missing_file.txt']
        results = self.checker.batch_check_files(file_paths)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].status, FileStatus.ACCESSIBLE)
        self.assertEqual(results[1].status, FileStatus.ACCESSIBLE)
        self.assertEqual(results[2].status, FileStatus.MISSING)


class FileSystemErrorHandlerTest(TestCase):
    """Test file system error handling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.handler = FileSystemErrorHandler()
        self.handler.accessibility_checker.base_path = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_handle_missing_file_error(self):
        """Test handling of missing file error."""
        error_record = self.handler.handle_file_system_error('missing_file.txt')
        
        self.assertEqual(error_record['status'], 'missing')
        self.assertEqual(error_record['error_type'], 'file_not_found')
        self.assertTrue(error_record['recovery_applied'])
        self.assertEqual(error_record['recovery_strategy'], 'mark_as_missing')
    
    def test_handle_permission_error(self):
        """Test handling of permission error."""
        # Create a file first
        test_file = os.path.join(self.temp_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        # Mock permission denied
        with patch('os.access', return_value=False):
            error_record = self.handler.handle_file_system_error('test_file.txt')
            
            self.assertEqual(error_record['status'], 'permission_denied')
            self.assertEqual(error_record['error_type'], 'permission_denied')
            self.assertTrue(error_record['recovery_applied'])
            self.assertEqual(error_record['recovery_strategy'], 'mark_as_inaccessible')
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        # Generate some errors
        self.handler.handle_file_system_error('missing_file1.txt')
        self.handler.handle_file_system_error('missing_file2.txt')
        
        summary = self.handler.get_error_summary()
        
        self.assertEqual(summary['total_errors'], 2)
        self.assertIn('file_not_found', summary['error_types'])
        self.assertEqual(summary['error_types']['file_not_found'], 2)
        self.assertGreater(summary['recovery_success_rate'], 0)


class FileSystemHandlerIntegrationTest(TestCase):
    """Test integration of file system error handling with migration process."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test department
        self.department = ProcessDepartment.objects.create(
            name='TEST DEPARTMENT',
            description='Test department for file system error handling'
        )
        
        # Create test process
        self.process = Process.objects.create(
            name='Test Process',
            process_code='TEST001',
            department=self.department,
            description='Test process for file system error handling'
        )
    
    def test_create_document_with_missing_file(self):
        """Test creating a document with missing file status."""
        document = ProcessDocument.objects.create(
            process=self.process,
            document_type='procedure',
            filename='missing_file.pdf',
            file_path='/path/to/missing_file.pdf',
            status='missing_file',
            is_active=False,
            metadata={
                'file_system_error': {
                    'error_type': 'file_not_found',
                    'error_message': 'File not found',
                    'recovery_strategy': 'mark_as_missing'
                }
            }
        )
        
        self.assertEqual(document.status, 'missing_file')
        self.assertFalse(document.is_active)
        self.assertTrue(document.has_file_system_error())
        self.assertEqual(document.get_recovery_strategy(), 'mark_as_missing')
    
    def test_create_document_with_sanitized_path(self):
        """Test creating a document with sanitized path."""
        document = ProcessDocument.objects.create(
            process=self.process,
            document_type='procedure',
            filename='sanitized_file.pdf',
            original_filename='file<with>invalid:chars.pdf',
            file_path='/path/to/sanitized_file.pdf',
            original_file_path='/path/to/file<with>invalid:chars.pdf',
            status='sanitized',
            is_active=True,
            metadata={
                'file_system_check': {
                    'sanitization_changes': [
                        'Invalid characters replaced: < > :'
                    ]
                }
            }
        )
        
        self.assertEqual(document.status, 'sanitized')
        self.assertTrue(document.is_active)
        self.assertTrue(document.is_path_sanitized())
        self.assertNotEqual(document.filename, document.original_filename)
    
    def test_create_document_with_permission_error(self):
        """Test creating a document with permission error."""
        document = ProcessDocument.objects.create(
            process=self.process,
            document_type='procedure',
            filename='restricted_file.pdf',
            file_path='/path/to/restricted_file.pdf',
            status='permission_denied',
            is_active=False,
            metadata={
                'file_system_error': {
                    'error_type': 'permission_denied',
                    'error_message': 'Permission denied reading file',
                    'recovery_strategy': 'mark_as_inaccessible'
                }
            }
        )
        
        self.assertEqual(document.status, 'permission_denied')
        self.assertFalse(document.is_active)
        self.assertTrue(document.has_file_system_error())
        self.assertEqual(document.get_file_system_error_message(), 'Permission denied reading file')
    
    def test_document_status_affects_is_active(self):
        """Test that document status automatically sets is_active field."""
        # Test accessible document
        accessible_doc = ProcessDocument(
            process=self.process,
            document_type='procedure',
            filename='accessible_file.pdf',
            status='accessible'
        )
        accessible_doc.save()
        self.assertTrue(accessible_doc.is_active)
        
        # Test missing file document
        missing_doc = ProcessDocument(
            process=self.process,
            document_type='process_map',
            filename='missing_file.pdf',
            status='missing_file'
        )
        missing_doc.save()
        self.assertFalse(missing_doc.is_active)