"""
Unit tests for migration infrastructure components.

Tests the BatchProcessor, ErrorRecoveryManager, and ProgressTracker classes
to ensure robust error handling and transaction management.
"""
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError
from django.utils import timezone

from process_management.migration_infrastructure import (
    BatchProcessor, ErrorRecoveryManager, ProgressTracker,
    ProcessingItem, ProcessingStatus, ErrorType, BatchResult
)


class ProgressTrackerTests(TestCase):
    """Test cases for ProgressTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker(total_items=100, description="Test Processing")
    
    def test_initialization(self):
        """Test ProgressTracker initialization."""
        self.assertEqual(self.tracker.total_items, 100)
        self.assertEqual(self.tracker.description, "Test Processing")
        self.assertEqual(self.tracker.processed_items, 0)
        self.assertEqual(self.tracker.successful_items, 0)
        self.assertEqual(self.tracker.failed_items, 0)
        self.assertEqual(self.tracker.skipped_items, 0)
        self.assertIsNotNone(self.tracker.start_time)
    
    def test_update_progress_success(self):
        """Test updating progress with successful items."""
        self.tracker.update_progress(10, ProcessingStatus.SUCCESS)
        
        self.assertEqual(self.tracker.processed_items, 10)
        self.assertEqual(self.tracker.successful_items, 10)
        self.assertEqual(self.tracker.failed_items, 0)
        self.assertEqual(self.tracker.status_counts[ProcessingStatus.SUCCESS], 10)
    
    def test_update_progress_failure(self):
        """Test updating progress with failed items."""
        self.tracker.update_progress(5, ProcessingStatus.FAILED, ErrorType.DATABASE_CONSTRAINT)
        
        self.assertEqual(self.tracker.processed_items, 5)
        self.assertEqual(self.tracker.successful_items, 0)
        self.assertEqual(self.tracker.failed_items, 5)
        self.assertEqual(self.tracker.status_counts[ProcessingStatus.FAILED], 5)
        self.assertEqual(self.tracker.error_counts[ErrorType.DATABASE_CONSTRAINT], 5)
    
    def test_update_progress_skipped(self):
        """Test updating progress with skipped items."""
        self.tracker.update_progress(3, ProcessingStatus.SKIPPED)
        
        self.assertEqual(self.tracker.processed_items, 3)
        self.assertEqual(self.tracker.skipped_items, 3)
        self.assertEqual(self.tracker.status_counts[ProcessingStatus.SKIPPED], 3)
    
    def test_get_progress_info(self):
        """Test getting comprehensive progress information."""
        self.tracker.update_progress(25, ProcessingStatus.SUCCESS)
        self.tracker.update_progress(5, ProcessingStatus.FAILED, ErrorType.VALIDATION)
        
        info = self.tracker.get_progress_info()
        
        self.assertEqual(info['total_items'], 100)
        self.assertEqual(info['processed_items'], 30)
        self.assertEqual(info['successful_items'], 25)
        self.assertEqual(info['failed_items'], 5)
        self.assertEqual(info['percentage'], 30.0)
        self.assertIn('elapsed_time', info)
        self.assertIn('eta_seconds', info)
        self.assertIn('rate_per_second', info)
    
    def test_format_progress_message(self):
        """Test formatting progress message."""
        self.tracker.update_progress(50, ProcessingStatus.SUCCESS)
        
        message = self.tracker.format_progress_message()
        
        self.assertIn("Test Processing", message)
        self.assertIn("50.0%", message)
        self.assertIn("(50/100)", message)
    
    def test_is_complete(self):
        """Test completion detection."""
        self.assertFalse(self.tracker.is_complete())
        
        self.tracker.update_progress(100, ProcessingStatus.SUCCESS)
        self.assertTrue(self.tracker.is_complete())
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        callback_mock = Mock()
        self.tracker.set_progress_callback(callback_mock)
        
        self.tracker.update_progress(10, ProcessingStatus.SUCCESS)
        
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        self.assertEqual(call_args['processed_items'], 10)
    
    def test_get_summary(self):
        """Test getting final processing summary."""
        self.tracker.update_progress(80, ProcessingStatus.SUCCESS)
        self.tracker.update_progress(15, ProcessingStatus.FAILED, ErrorType.FILE_SYSTEM)
        self.tracker.update_progress(5, ProcessingStatus.SKIPPED)
        
        summary = self.tracker.get_summary()
        
        self.assertEqual(summary['total_processed'], 100)
        self.assertEqual(summary['successful'], 80)
        self.assertEqual(summary['failed'], 15)
        self.assertEqual(summary['skipped'], 5)
        self.assertEqual(summary['success_rate'], 80.0)
        self.assertIn('total_time', summary)
        self.assertIn('average_rate', summary)


class ErrorRecoveryManagerTests(TestCase):
    """Test cases for ErrorRecoveryManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_manager = ErrorRecoveryManager(max_retries=2, base_delay=0.1)
        self.test_item = ProcessingItem(id="test_item", data={"test": "data"})
    
    def test_initialization(self):
        """Test ErrorRecoveryManager initialization."""
        self.assertEqual(self.error_manager.max_retries, 2)
        self.assertEqual(self.error_manager.base_delay, 0.1)
        self.assertEqual(len(self.error_manager.error_log), 0)
    
    def test_categorize_error_integrity_error(self):
        """Test error categorization for IntegrityError."""
        error = IntegrityError("Duplicate key")
        error_type = self.error_manager._categorize_error(error)
        self.assertEqual(error_type, ErrorType.DATABASE_CONSTRAINT)
    
    def test_categorize_error_database_error(self):
        """Test error categorization for DatabaseError."""
        error = DatabaseError("Connection failed")
        error_type = self.error_manager._categorize_error(error)
        self.assertEqual(error_type, ErrorType.TRANSACTION)
    
    def test_categorize_error_validation_error(self):
        """Test error categorization for ValidationError."""
        error = ValidationError("Invalid data")
        error_type = self.error_manager._categorize_error(error)
        self.assertEqual(error_type, ErrorType.VALIDATION)
    
    def test_categorize_error_file_not_found(self):
        """Test error categorization for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        error_type = self.error_manager._categorize_error(error)
        self.assertEqual(error_type, ErrorType.FILE_SYSTEM)
    
    def test_categorize_error_permission_error(self):
        """Test error categorization for PermissionError."""
        error = PermissionError("Access denied")
        error_type = self.error_manager._categorize_error(error)
        self.assertEqual(error_type, ErrorType.PERMISSION)
    
    def test_categorize_error_unknown(self):
        """Test error categorization for unknown errors."""
        error = RuntimeError("Unknown error")
        error_type = self.error_manager._categorize_error(error)
        self.assertEqual(error_type, ErrorType.UNKNOWN)
    
    def test_should_retry_retryable_error(self):
        """Test retry decision for retryable errors."""
        self.test_item.retry_count = 1
        should_retry = self.error_manager._should_retry(self.test_item, ErrorType.DATABASE_CONSTRAINT)
        self.assertTrue(should_retry)
    
    def test_should_retry_max_retries_exceeded(self):
        """Test retry decision when max retries exceeded."""
        self.test_item.retry_count = 3
        should_retry = self.error_manager._should_retry(self.test_item, ErrorType.DATABASE_CONSTRAINT)
        self.assertFalse(should_retry)
    
    def test_should_retry_non_retryable_error(self):
        """Test retry decision for non-retryable errors."""
        self.test_item.retry_count = 0
        should_retry = self.error_manager._should_retry(self.test_item, ErrorType.VALIDATION)
        self.assertFalse(should_retry)
    
    def test_calculate_retry_delay(self):
        """Test retry delay calculation with exponential backoff."""
        delay1 = self.error_manager.calculate_retry_delay(0)
        delay2 = self.error_manager.calculate_retry_delay(1)
        delay3 = self.error_manager.calculate_retry_delay(2)
        
        self.assertEqual(delay1, 0.1)
        self.assertEqual(delay2, 0.2)
        self.assertEqual(delay3, 0.4)
    
    def test_calculate_retry_delay_max_limit(self):
        """Test retry delay respects maximum limit."""
        manager = ErrorRecoveryManager(base_delay=10.0, max_delay=30.0)
        delay = manager.calculate_retry_delay(5)  # Would be 320 without limit
        self.assertEqual(delay, 30.0)
    
    def test_handle_error_retryable(self):
        """Test handling retryable error."""
        error = IntegrityError("Duplicate key")
        
        updated_item = self.error_manager.handle_error(self.test_item, error)
        
        self.assertEqual(updated_item.status, ProcessingStatus.RETRY)
        self.assertEqual(updated_item.error_type, ErrorType.DATABASE_CONSTRAINT)
        self.assertEqual(updated_item.error_message, "Duplicate key")
        self.assertEqual(updated_item.retry_count, 1)
        self.assertEqual(len(self.error_manager.error_log), 1)
    
    def test_handle_error_non_retryable(self):
        """Test handling non-retryable error."""
        error = ValidationError("Invalid data")
        
        updated_item = self.error_manager.handle_error(self.test_item, error)
        
        self.assertEqual(updated_item.status, ProcessingStatus.FAILED)
        self.assertEqual(updated_item.error_type, ErrorType.VALIDATION)
        self.assertEqual(updated_item.error_message, "Invalid data")
        self.assertEqual(len(self.error_manager.error_log), 1)
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        # Add some errors
        self.error_manager.handle_error(self.test_item, IntegrityError("Error 1"))
        item2 = ProcessingItem(id="item2", data={})
        self.error_manager.handle_error(item2, ValidationError("Error 2"))
        
        summary = self.error_manager.get_error_summary()
        
        self.assertEqual(summary['total_errors'], 2)
        self.assertIn('database_constraint', summary['error_counts'])
        self.assertIn('validation', summary['error_counts'])
        self.assertEqual(len(summary['recent_errors']), 2)


class BatchProcessorTests(TestCase):
    """Test cases for BatchProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.progress_tracker = ProgressTracker(total_items=10, description="Test Batch")
        self.error_manager = ErrorRecoveryManager(max_retries=1, base_delay=0.01)
        self.batch_processor = BatchProcessor(
            batch_size=3,
            progress_tracker=self.progress_tracker,
            error_manager=self.error_manager
        )
        
        # Create test items
        self.test_items = [
            ProcessingItem(id=f"item_{i}", data={"value": i})
            for i in range(10)
        ]
    
    def test_initialization(self):
        """Test BatchProcessor initialization."""
        self.assertEqual(self.batch_processor.batch_size, 3)
        self.assertEqual(self.batch_processor.progress_tracker, self.progress_tracker)
        self.assertEqual(self.batch_processor.error_manager, self.error_manager)
        self.assertEqual(len(self.batch_processor.batch_results), 0)
    
    def test_create_batches(self):
        """Test batch creation from items."""
        batches = list(self.batch_processor._create_batches(self.test_items))
        
        self.assertEqual(len(batches), 4)  # 10 items with batch size 3
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[1]), 3)
        self.assertEqual(len(batches[2]), 3)
        self.assertEqual(len(batches[3]), 1)
    
    @patch('process_management.migration_infrastructure.transaction')
    def test_process_batch_success(self, mock_transaction):
        """Test successful batch processing."""
        # Mock transaction management
        mock_savepoint = Mock()
        mock_transaction.atomic.return_value.__enter__ = Mock()
        mock_transaction.atomic.return_value.__exit__ = Mock()
        mock_transaction.savepoint.return_value = mock_savepoint
        
        # Create a simple processor function
        def processor_func(item):
            return f"processed_{item.id}"
        
        batch_items = self.test_items[:3]
        result = self.batch_processor._process_batch("test_batch", batch_items, processor_func)
        
        self.assertEqual(result.batch_id, "test_batch")
        self.assertEqual(result.total_items, 3)
        self.assertEqual(len(result.successful_items), 3)
        self.assertEqual(len(result.failed_items), 0)
        self.assertEqual(len(result.skipped_items), 0)
        
        # Verify transaction commit was called
        mock_transaction.savepoint_commit.assert_called_once_with(mock_savepoint)
    
    @patch('process_management.migration_infrastructure.transaction')
    def test_process_batch_with_errors(self, mock_transaction):
        """Test batch processing with some errors."""
        # Mock transaction management
        mock_savepoint = Mock()
        mock_transaction.atomic.return_value.__enter__ = Mock()
        mock_transaction.atomic.return_value.__exit__ = Mock()
        mock_transaction.savepoint.return_value = mock_savepoint
        
        # Create a processor function that fails on certain items
        def processor_func(item):
            if item.data["value"] == 1:
                raise ValueError("Test error")
            return f"processed_{item.id}"
        
        batch_items = self.test_items[:3]
        result = self.batch_processor._process_batch("test_batch", batch_items, processor_func)
        
        self.assertEqual(result.batch_id, "test_batch")
        self.assertEqual(result.total_items, 3)
        self.assertEqual(len(result.successful_items), 2)
        self.assertEqual(len(result.failed_items), 1)
        
        # Check that the failed item has error information
        failed_item = result.failed_items[0]
        self.assertEqual(failed_item.id, "item_1")
        self.assertEqual(failed_item.status, ProcessingStatus.FAILED)
        self.assertIsNotNone(failed_item.error_message)
    
    @patch('process_management.migration_infrastructure.transaction')
    def test_process_batch_skip_already_processed(self, mock_transaction):
        """Test that already processed items are skipped."""
        # Mock transaction management
        mock_savepoint = Mock()
        mock_transaction.atomic.return_value.__enter__ = Mock()
        mock_transaction.atomic.return_value.__exit__ = Mock()
        mock_transaction.savepoint.return_value = mock_savepoint
        
        # Mark one item as already successful
        self.test_items[1].status = ProcessingStatus.SUCCESS
        
        def processor_func(item):
            return f"processed_{item.id}"
        
        batch_items = self.test_items[:3]
        result = self.batch_processor._process_batch("test_batch", batch_items, processor_func)
        
        self.assertEqual(len(result.successful_items), 2)
        self.assertEqual(len(result.skipped_items), 1)
        self.assertEqual(result.skipped_items[0].id, "item_1")
    
    @patch('process_management.migration_infrastructure.transaction')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_process_batch_with_retry(self, mock_sleep, mock_transaction):
        """Test batch processing with retry logic."""
        # Mock transaction management
        mock_savepoint = Mock()
        mock_transaction.atomic.return_value.__enter__ = Mock()
        mock_transaction.atomic.return_value.__exit__ = Mock()
        mock_transaction.savepoint.return_value = mock_savepoint
        
        # Create a processor function that fails first time but succeeds on retry
        call_count = {}
        
        def processor_func(item):
            item_id = item.id
            call_count[item_id] = call_count.get(item_id, 0) + 1
            
            if item_id == "item_1" and call_count[item_id] == 1:
                raise IntegrityError("First attempt fails")
            return f"processed_{item.id}"
        
        batch_items = self.test_items[:3]
        result = self.batch_processor._process_batch("test_batch", batch_items, processor_func)
        
        # Should have 3 successful items (including the retried one)
        self.assertEqual(len(result.successful_items), 3)
        self.assertEqual(len(result.failed_items), 0)
        
        # Verify sleep was called for retry delay
        mock_sleep.assert_called()
    
    def test_process_items_full_workflow(self):
        """Test complete item processing workflow."""
        def processor_func(item):
            # Simulate some processing
            if item.data["value"] == 5:
                raise ValueError("Simulated error")
            return f"processed_{item.id}"
        
        with patch('process_management.migration_infrastructure.transaction') as mock_transaction:
            # Mock transaction management
            mock_savepoint = Mock()
            mock_transaction.atomic.return_value.__enter__ = Mock()
            mock_transaction.atomic.return_value.__exit__ = Mock()
            mock_transaction.savepoint.return_value = mock_savepoint
            
            results = self.batch_processor.process_items(self.test_items, processor_func)
        
        # Should have 4 batches (10 items with batch size 3)
        self.assertEqual(len(results), 4)
        
        # Check overall statistics
        self.assertEqual(self.batch_processor.total_processed, 10)
        self.assertEqual(self.batch_processor.total_successful, 9)  # All except item_5
        self.assertEqual(self.batch_processor.total_failed, 1)
        
        # Check progress tracker was updated
        self.assertEqual(self.progress_tracker.processed_items, 10)
        self.assertEqual(self.progress_tracker.successful_items, 9)
        self.assertEqual(self.progress_tracker.failed_items, 1)
    
    def test_get_processing_summary(self):
        """Test getting processing summary."""
        # Process some items first
        def processor_func(item):
            return f"processed_{item.id}"
        
        with patch('process_management.migration_infrastructure.transaction') as mock_transaction:
            mock_savepoint = Mock()
            mock_transaction.atomic.return_value.__enter__ = Mock()
            mock_transaction.atomic.return_value.__exit__ = Mock()
            mock_transaction.savepoint.return_value = mock_savepoint
            
            self.batch_processor.process_items(self.test_items[:5], processor_func)
        
        summary = self.batch_processor.get_processing_summary()
        
        self.assertEqual(summary['total_items'], 5)
        self.assertEqual(summary['successful_items'], 5)
        self.assertEqual(summary['failed_items'], 0)
        self.assertEqual(summary['success_rate'], 100.0)
        self.assertIn('total_processing_time', summary)
        self.assertIn('average_batch_time', summary)
        self.assertIn('items_per_second', summary)
    
    def test_get_failed_items(self):
        """Test getting failed items across all batches."""
        def processor_func(item):
            if item.data["value"] in [2, 7]:
                raise ValueError("Simulated error")
            return f"processed_{item.id}"
        
        with patch('process_management.migration_infrastructure.transaction') as mock_transaction:
            mock_savepoint = Mock()
            mock_transaction.atomic.return_value.__enter__ = Mock()
            mock_transaction.atomic.return_value.__exit__ = Mock()
            mock_transaction.savepoint.return_value = mock_savepoint
            
            self.batch_processor.process_items(self.test_items, processor_func)
        
        failed_items = self.batch_processor.get_failed_items()
        
        self.assertEqual(len(failed_items), 2)
        failed_ids = [item.id for item in failed_items]
        self.assertIn("item_2", failed_ids)
        self.assertIn("item_7", failed_ids)


class ProcessingItemTests(TestCase):
    """Test cases for ProcessingItem dataclass."""
    
    def test_processing_item_creation(self):
        """Test ProcessingItem creation and default values."""
        item = ProcessingItem(id="test_item", data={"key": "value"})
        
        self.assertEqual(item.id, "test_item")
        self.assertEqual(item.data, {"key": "value"})
        self.assertEqual(item.status, ProcessingStatus.PENDING)
        self.assertIsNone(item.error_message)
        self.assertIsNone(item.error_type)
        self.assertEqual(item.retry_count, 0)
        self.assertIsNone(item.processing_time)
        self.assertIsNotNone(item.created_at)
    
    def test_processing_item_with_custom_values(self):
        """Test ProcessingItem with custom values."""
        custom_time = timezone.now()
        item = ProcessingItem(
            id="custom_item",
            data={"custom": "data"},
            status=ProcessingStatus.PROCESSING,
            error_message="Custom error",
            error_type=ErrorType.VALIDATION,
            retry_count=2,
            processing_time=1.5,
            created_at=custom_time
        )
        
        self.assertEqual(item.id, "custom_item")
        self.assertEqual(item.status, ProcessingStatus.PROCESSING)
        self.assertEqual(item.error_message, "Custom error")
        self.assertEqual(item.error_type, ErrorType.VALIDATION)
        self.assertEqual(item.retry_count, 2)
        self.assertEqual(item.processing_time, 1.5)
        self.assertEqual(item.created_at, custom_time)


class BatchResultTests(TestCase):
    """Test cases for BatchResult dataclass."""
    
    def test_batch_result_creation(self):
        """Test BatchResult creation and default values."""
        result = BatchResult(batch_id="test_batch", total_items=10)
        
        self.assertEqual(result.batch_id, "test_batch")
        self.assertEqual(result.total_items, 10)
        self.assertEqual(len(result.successful_items), 0)
        self.assertEqual(len(result.failed_items), 0)
        self.assertEqual(len(result.skipped_items), 0)
        self.assertEqual(result.processing_time, 0.0)
        self.assertEqual(len(result.error_summary), 0)
    
    def test_batch_result_with_items(self):
        """Test BatchResult with processing items."""
        successful_item = ProcessingItem(id="success", data={}, status=ProcessingStatus.SUCCESS)
        failed_item = ProcessingItem(id="failed", data={}, status=ProcessingStatus.FAILED)
        skipped_item = ProcessingItem(id="skipped", data={}, status=ProcessingStatus.SKIPPED)
        
        result = BatchResult(
            batch_id="test_batch",
            total_items=3,
            successful_items=[successful_item],
            failed_items=[failed_item],
            skipped_items=[skipped_item],
            processing_time=2.5,
            error_summary={ErrorType.VALIDATION: 1}
        )
        
        self.assertEqual(len(result.successful_items), 1)
        self.assertEqual(len(result.failed_items), 1)
        self.assertEqual(len(result.skipped_items), 1)
        self.assertEqual(result.processing_time, 2.5)
        self.assertEqual(result.error_summary[ErrorType.VALIDATION], 1)


if __name__ == '__main__':
    unittest.main()