"""
Test file for Optimized File Handlers in Direct Purchase
Verifies that the handlers can be imported and basic functionality works
"""

import os
import sys
import django
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.conf import settings

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

# Import the handlers after Django setup
from .optimized_file_handlers import (
    OptimizedFileHandler,
    OptimizedDirectPurchaseFileHandler,
    validate_dp_file,
    get_dp_file_download_url,
    get_dp_file_preview_url
)

class OptimizedFileHandlersTest(TestCase):
    """Test case for optimized file handlers"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test file
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"Test PDF content",
            content_type="application/pdf"
        )
    
    def test_optimized_file_handler_import(self):
        """Test that OptimizedFileHandler can be imported and instantiated"""
        try:
            handler = OptimizedFileHandler(self.user)
            self.assertIsNotNone(handler)
            self.assertEqual(handler.user, self.user)
        except Exception as e:
            self.fail(f"Failed to import OptimizedFileHandler: {e}")
    
    def test_optimized_dp_file_handler_import(self):
        """Test that OptimizedDirectPurchaseFileHandler can be imported and instantiated"""
        try:
            handler = OptimizedDirectPurchaseFileHandler(self.user)
            self.assertIsNotNone(handler)
            self.assertEqual(handler.user, self.user)
        except Exception as e:
            self.fail(f"Failed to import OptimizedDirectPurchaseFileHandler: {e}")
    
    def test_utility_functions_import(self):
        """Test that utility functions can be imported"""
        try:
            # Test utility functions
            self.assertIsNotNone(validate_dp_file)
            self.assertIsNotNone(get_dp_file_download_url)
            self.assertIsNotNone(get_dp_file_preview_url)
        except Exception as e:
            self.fail(f"Failed to import utility functions: {e}")
    
    def test_file_validation(self):
        """Test file validation functionality"""
        handler = OptimizedFileHandler(self.user)
        
        # Test valid file
        try:
            result = handler.validate_file(self.test_file)
            self.assertTrue(result)
        except Exception as e:
            self.fail(f"File validation failed for valid file: {e}")
        
        # Test file size validation
        large_file = SimpleUploadedFile(
            "large_file.pdf",
            b"x" * (51 * 1024 * 1024),  # 51MB (over limit)
            content_type="application/pdf"
        )
        
        with self.assertRaises(Exception):
            handler.validate_file(large_file)
    
    def test_file_metadata_generation(self):
        """Test file metadata generation"""
        handler = OptimizedFileHandler(self.user)
        
        try:
            metadata = handler.generate_file_metadata(self.test_file)
            
            # Check required metadata fields
            required_fields = ['original_name', 'size', 'extension', 'uploaded_by', 'uploaded_at']
            for field in required_fields:
                self.assertIn(field, metadata)
            
            # Check specific values
            self.assertEqual(metadata['original_name'], 'test_document.pdf')
            self.assertEqual(metadata['size'], len(b"Test PDF content"))
            self.assertEqual(metadata['extension'], '.pdf')
            self.assertEqual(metadata['uploaded_by'], 'testuser')
            
        except Exception as e:
            self.fail(f"File metadata generation failed: {e}")
    
    def test_utility_functions(self):
        """Test utility functions work correctly"""
        # Test download URL generation
        test_path = "uploads/test/file.pdf"
        download_url = get_dp_file_download_url(test_path)
        self.assertEqual(download_url, "/api/dp-files/download/uploads/test/file.pdf/")
        
        # Test preview URL generation
        preview_url = get_dp_file_preview_url(test_path)
        self.assertEqual(preview_url, "/api/dp-files/preview/uploads/test/file.pdf/")
        
        # Test with None path
        self.assertIsNone(get_dp_file_download_url(None))
        self.assertIsNone(get_dp_file_preview_url(None))
    
    def test_file_size_utility(self):
        """Test file size utility function"""
        from .optimized_file_handlers import get_dp_file_size
        
        # Test with non-existent file
        size = get_dp_file_size("non_existent_file.txt")
        self.assertEqual(size, 0)
        
        # Test with existing file (create a temporary file)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_file.flush()
            
            size = get_dp_file_size(temp_file.name)
            self.assertEqual(size, len(b"Test content"))
            
            # Clean up
            os.unlink(temp_file.name)

if __name__ == '__main__':
    # Run tests if executed directly
    import django
    django.setup()
    
    # Run the tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Discover and run tests
    failures = test_runner.run_tests(['finance.direct_purchase.test_optimized_file_handlers'])
    
    if failures:
        sys.exit(1)
    else:
        print("✅ All tests passed!")
