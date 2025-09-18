"""
Example usage of the migration infrastructure components.

This file demonstrates how to use the BatchProcessor, ErrorRecoveryManager,
and ProgressTracker together for robust migration processing.
"""
import time
from typing import List, Any
from django.db import IntegrityError

from migration_infrastructure import (
    BatchProcessor, ErrorRecoveryManager, ProgressTracker,
    ProcessingItem, ProcessingStatus, ErrorType
)


def example_migration_with_infrastructure():
    """
    Example of how to use the migration infrastructure components together.
    
    This demonstrates the complete workflow for processing migration items
    with comprehensive error handling and progress tracking.
    """
    print("=== Migration Infrastructure Example ===\n")
    
    # Step 1: Create sample data to migrate
    sample_data = [
        {"id": f"item_{i}", "name": f"Process {i}", "value": i}
        for i in range(20)
    ]
    
    # Convert to ProcessingItems
    processing_items = [
        ProcessingItem(id=item["id"], data=item)
        for item in sample_data
    ]
    
    print(f"Created {len(processing_items)} items to process")
    
    # Step 2: Set up infrastructure components
    progress_tracker = ProgressTracker(
        total_items=len(processing_items),
        description="Sample Migration"
    )
    
    error_manager = ErrorRecoveryManager(
        max_retries=2,
        base_delay=0.1,  # Short delay for example
        max_delay=1.0
    )
    
    batch_processor = BatchProcessor(
        batch_size=5,
        progress_tracker=progress_tracker,
        error_manager=error_manager
    )
    
    # Step 3: Define processing function with some simulated errors
    def process_migration_item(item: ProcessingItem) -> Any:
        """
        Simulate processing a migration item with potential errors.
        
        Args:
            item: The item to process
            
        Returns:
            Processing result
            
        Raises:
            Various exceptions to demonstrate error handling
        """
        data = item.data
        
        # Simulate different types of errors for demonstration
        if data["value"] == 5:
            raise IntegrityError("Simulated database constraint violation")
        elif data["value"] == 10:
            raise FileNotFoundError("Simulated file not found")
        elif data["value"] == 15:
            raise ValueError("Simulated validation error")
        
        # Simulate processing time
        time.sleep(0.01)
        
        # Return successful result
        return {
            "processed_id": item.id,
            "processed_name": data["name"],
            "status": "success"
        }
    
    # Step 4: Set up progress callback for real-time monitoring
    def progress_callback(progress_info):
        """Callback function to display progress updates."""
        print(f"Progress: {progress_info['percentage']:.1f}% - "
              f"{progress_info['successful_items']} successful, "
              f"{progress_info['failed_items']} failed")
    
    progress_tracker.set_progress_callback(progress_callback)
    
    # Step 5: Process the items
    print("\nStarting batch processing...")
    start_time = time.time()
    
    try:
        # Mock transaction for example
        class MockTransaction:
            def atomic(self):
                return self
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def savepoint(self):
                return 'mock_savepoint'
            def savepoint_commit(self, sp):
                print(f"  ✓ Committed batch savepoint: {sp}")
            def savepoint_rollback(self, sp):
                print(f"  ✗ Rolled back batch savepoint: {sp}")
        
        # Replace transaction for example
        import process_management.migration_infrastructure as mi
        mi.transaction = MockTransaction()
        
        batch_results = batch_processor.process_items(
            processing_items,
            process_migration_item
        )
        
        processing_time = time.time() - start_time
        
        # Step 6: Display results
        print(f"\nProcessing completed in {processing_time:.2f} seconds")
        print(f"Processed {len(batch_results)} batches")
        
        # Overall statistics
        summary = batch_processor.get_processing_summary()
        print(f"\n=== Processing Summary ===")
        print(f"Total items: {summary['total_items']}")
        print(f"Successful: {summary['successful_items']}")
        print(f"Failed: {summary['failed_items']}")
        print(f"Skipped: {summary['skipped_items']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Processing rate: {summary['items_per_second']:.1f} items/second")
        
        # Error analysis
        error_summary = error_manager.get_error_summary()
        if error_summary['total_errors'] > 0:
            print(f"\n=== Error Analysis ===")
            print(f"Total errors: {error_summary['total_errors']}")
            print("Error breakdown:")
            for error_type, count in error_summary['error_counts'].items():
                print(f"  {error_type}: {count}")
        
        # Failed items details
        failed_items = batch_processor.get_failed_items()
        if failed_items:
            print(f"\n=== Failed Items ===")
            for item in failed_items:
                print(f"  {item.id}: {item.error_message} ({item.error_type.value})")
        
        # Progress tracker final summary
        progress_summary = progress_tracker.get_summary()
        print(f"\n=== Progress Summary ===")
        print(f"Total time: {progress_summary['total_time']:.2f} seconds")
        print(f"Average rate: {progress_summary['average_rate']:.1f} items/second")
        print(f"Final success rate: {progress_summary['success_rate']:.1f}%")
        
        return batch_results
        
    except Exception as e:
        print(f"\nCritical error during processing: {e}")
        raise


def example_error_recovery_strategies():
    """
    Example demonstrating different error recovery strategies.
    """
    print("\n=== Error Recovery Strategies Example ===\n")
    
    error_manager = ErrorRecoveryManager(max_retries=3, base_delay=0.1)
    
    # Test different error types
    test_cases = [
        (IntegrityError("Duplicate key"), "Database constraint violation"),
        (FileNotFoundError("File missing"), "File system error"),
        (ValueError("Invalid data"), "Validation error"),
        (PermissionError("Access denied"), "Permission error"),
    ]
    
    for i, (error, description) in enumerate(test_cases):
        print(f"Testing {description}...")
        
        test_item = ProcessingItem(id=f"test_item_{i}", data={"test": "data"})
        updated_item = error_manager.handle_error(test_item, error)
        
        print(f"  Error type: {updated_item.error_type.value}")
        print(f"  Status: {updated_item.status.value}")
        print(f"  Retry count: {updated_item.retry_count}")
        
        if updated_item.status == ProcessingStatus.RETRY:
            delay = error_manager.calculate_retry_delay(updated_item.retry_count)
            print(f"  Next retry delay: {delay:.2f} seconds")
        
        print()
    
    # Show error summary
    error_summary = error_manager.get_error_summary()
    print("Error Summary:")
    print(f"  Total errors handled: {error_summary['total_errors']}")
    print(f"  Error types: {list(error_summary['error_counts'].keys())}")


def example_progress_tracking():
    """
    Example demonstrating progress tracking capabilities.
    """
    print("\n=== Progress Tracking Example ===\n")
    
    tracker = ProgressTracker(total_items=50, description="Sample Task")
    
    # Simulate processing with different outcomes
    for i in range(50):
        time.sleep(0.02)  # Simulate work
        
        if i % 10 == 0:
            # Simulate some failures
            tracker.update_progress(1, ProcessingStatus.FAILED, ErrorType.VALIDATION)
        elif i % 15 == 0:
            # Simulate some skipped items
            tracker.update_progress(1, ProcessingStatus.SKIPPED)
        else:
            # Most items succeed
            tracker.update_progress(1, ProcessingStatus.SUCCESS)
        
        # Show progress every 10 items
        if (i + 1) % 10 == 0:
            print(tracker.format_progress_message())
    
    # Final summary
    print("\nFinal Summary:")
    summary = tracker.get_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    """Run examples when script is executed directly."""
    
    # Set up Django environment
    import os
    import sys
    import django
    
    # Add project root to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configure Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
    django.setup()
    
    # Run examples
    try:
        example_migration_with_infrastructure()
        example_error_recovery_strategies()
        example_progress_tracking()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()