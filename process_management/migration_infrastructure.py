"""
Enhanced error handling and transaction management infrastructure for knowledge center migration.

This module provides robust infrastructure components for handling batch processing,
error recovery, progress tracking, and idempotent migration with resume capability.
"""
import time
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, Generator, Tuple
from dataclasses import dataclass, field
from enum import Enum
from django.db import transaction, DatabaseError, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError


class ErrorType(Enum):
    """Enumeration of different error types that can occur during migration."""
    DATABASE_CONSTRAINT = "database_constraint"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    TRANSACTION = "transaction"
    NETWORK = "network"
    PERMISSION = "permission"
    DATA_INTEGRITY = "data_integrity"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """Enumeration of processing statuses for items."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


@dataclass
class ProcessingItem:
    """Represents an item to be processed during migration."""
    id: str
    data: Dict[str, Any]
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None
    retry_count: int = 0
    processing_time: Optional[float] = None
    created_at: timezone.datetime = field(default_factory=timezone.now)


@dataclass
class BatchResult:
    """Results from processing a batch of items."""
    batch_id: str
    total_items: int
    successful_items: List[ProcessingItem] = field(default_factory=list)
    failed_items: List[ProcessingItem] = field(default_factory=list)
    skipped_items: List[ProcessingItem] = field(default_factory=list)
    processing_time: float = 0.0
    error_summary: Dict[ErrorType, int] = field(default_factory=dict)


class ProgressTracker:
    """
    Real-time progress monitoring for migration operations.
    
    Provides comprehensive progress tracking with percentage completion,
    time estimates, and detailed status reporting.
    """
    
    def __init__(self, total_items: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            description: Description of the operation being tracked
        """
        self.total_items = total_items
        self.description = description
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.skipped_items = 0
        self.start_time = timezone.now()
        self.last_update_time = self.start_time
        self.status_counts = {status: 0 for status in ProcessingStatus}
        self.error_counts = {error_type: 0 for error_type in ErrorType}
        
        # Progress callback for external monitoring
        self.progress_callback: Optional[Callable[[Dict], None]] = None
    
    def update_progress(self, items_processed: int = 1, status: ProcessingStatus = ProcessingStatus.SUCCESS,
                       error_type: Optional[ErrorType] = None, message: str = ""):
        """
        Update progress with processed items.
        
        Args:
            items_processed: Number of items processed in this update
            status: Status of the processed items
            error_type: Type of error if status is FAILED
            message: Optional message for this update
        """
        self.processed_items += items_processed
        self.status_counts[status] += items_processed
        
        if status == ProcessingStatus.SUCCESS:
            self.successful_items += items_processed
        elif status == ProcessingStatus.FAILED:
            self.failed_items += items_processed
            if error_type:
                self.error_counts[error_type] += items_processed
        elif status == ProcessingStatus.SKIPPED:
            self.skipped_items += items_processed
        
        self.last_update_time = timezone.now()
        
        # Call progress callback if set
        if self.progress_callback:
            self.progress_callback(self.get_progress_info())
    
    def get_progress_info(self) -> Dict[str, Any]:
        """
        Get comprehensive progress information.
        
        Returns:
            Dictionary containing detailed progress information
        """
        current_time = timezone.now()
        elapsed_time = (current_time - self.start_time).total_seconds()
        
        # Calculate percentage
        percentage = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
        
        # Calculate ETA
        eta_seconds = 0
        if self.processed_items > 0 and percentage < 100 and elapsed_time > 0:
            rate = self.processed_items / elapsed_time
            remaining_items = self.total_items - self.processed_items
            eta_seconds = remaining_items / rate if rate > 0 else 0
        
        # Calculate processing rate
        rate_per_second = self.processed_items / elapsed_time if elapsed_time > 0 else 0
        
        return {
            'description': self.description,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'skipped_items': self.skipped_items,
            'percentage': round(percentage, 2),
            'elapsed_time': elapsed_time,
            'eta_seconds': eta_seconds,
            'rate_per_second': round(rate_per_second, 2),
            'status_counts': dict(self.status_counts),
            'error_counts': {k.value: v for k, v in self.error_counts.items() if v > 0},
            'last_update': self.last_update_time.isoformat(),
        }
    
    def format_progress_message(self) -> str:
        """
        Format a human-readable progress message.
        
        Returns:
            Formatted progress string
        """
        info = self.get_progress_info()
        
        # Format ETA
        eta_str = ""
        if info['eta_seconds'] > 0:
            eta_minutes = int(info['eta_seconds'] / 60)
            eta_str = f" - ETA: {eta_minutes}m" if eta_minutes > 0 else f" - ETA: {int(info['eta_seconds'])}s"
        
        # Format rate
        rate_str = f" ({info['rate_per_second']:.1f}/s)" if info['rate_per_second'] > 0 else ""
        
        return (f"{info['description']}: {info['percentage']:.1f}% "
                f"({info['processed_items']}/{info['total_items']}){rate_str}{eta_str}")
    
    def set_progress_callback(self, callback: Callable[[Dict], None]):
        """
        Set a callback function to be called on progress updates.
        
        Args:
            callback: Function that accepts progress info dictionary
        """
        self.progress_callback = callback
    
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        return self.processed_items >= self.total_items
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get final processing summary.
        
        Returns:
            Dictionary containing processing summary
        """
        info = self.get_progress_info()
        return {
            'total_processed': self.processed_items,
            'successful': self.successful_items,
            'failed': self.failed_items,
            'skipped': self.skipped_items,
            'success_rate': (self.successful_items / self.processed_items * 100) if self.processed_items > 0 else 0,
            'total_time': info['elapsed_time'],
            'average_rate': info['rate_per_second'],
            'error_breakdown': info['error_counts'],
        }


class ErrorRecoveryManager:
    """
    Handles different types of errors gracefully with retry logic and recovery strategies.
    
    Provides intelligent error handling with configurable retry policies,
    error categorization, and recovery mechanisms.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize error recovery manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.error_log: List[Dict[str, Any]] = []
        self.recovery_strategies: Dict[ErrorType, Callable] = {
            ErrorType.DATABASE_CONSTRAINT: self._handle_database_constraint,
            ErrorType.FILE_SYSTEM: self._handle_file_system_error,
            ErrorType.VALIDATION: self._handle_validation_error,
            ErrorType.TRANSACTION: self._handle_transaction_error,
            ErrorType.NETWORK: self._handle_network_error,
            ErrorType.PERMISSION: self._handle_permission_error,
            ErrorType.DATA_INTEGRITY: self._handle_data_integrity_error,
        }
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, item: ProcessingItem, exception: Exception, 
                    context: Optional[Dict[str, Any]] = None) -> ProcessingItem:
        """
        Handle an error that occurred during item processing.
        
        Args:
            item: The processing item that failed
            exception: The exception that occurred
            context: Additional context information
            
        Returns:
            Updated processing item with error information
        """
        error_type = self._categorize_error(exception)
        error_info = {
            'item_id': item.id,
            'error_type': error_type.value,
            'error_message': str(exception),
            'exception_type': type(exception).__name__,
            'retry_count': item.retry_count,
            'timestamp': timezone.now().isoformat(),
            'context': context or {},
        }
        
        self.error_log.append(error_info)
        
        # Update item with error information
        item.error_type = error_type
        item.error_message = str(exception)
        
        # Determine if we should retry
        if self._should_retry(item, error_type):
            item.status = ProcessingStatus.RETRY
            item.retry_count += 1
            
            # Apply recovery strategy if available
            recovery_strategy = self.recovery_strategies.get(error_type)
            if recovery_strategy:
                try:
                    recovery_strategy(item, exception, context)
                except Exception as recovery_error:
                    self.logger.warning(f"Recovery strategy failed for {error_type}: {recovery_error}")
        else:
            item.status = ProcessingStatus.FAILED
        
        self.logger.error(f"Error processing item {item.id}: {exception}", exc_info=True)
        return item
    
    def _categorize_error(self, exception: Exception) -> ErrorType:
        """
        Categorize an exception into an error type.
        
        Args:
            exception: The exception to categorize
            
        Returns:
            Categorized error type
        """
        if isinstance(exception, IntegrityError):
            return ErrorType.DATABASE_CONSTRAINT
        elif isinstance(exception, DatabaseError):
            return ErrorType.TRANSACTION
        elif isinstance(exception, ValidationError):
            return ErrorType.VALIDATION
        elif isinstance(exception, (FileNotFoundError, PermissionError, OSError)):
            if isinstance(exception, PermissionError):
                return ErrorType.PERMISSION
            return ErrorType.FILE_SYSTEM
        elif "network" in str(exception).lower() or "connection" in str(exception).lower():
            return ErrorType.NETWORK
        else:
            return ErrorType.UNKNOWN
    
    def _should_retry(self, item: ProcessingItem, error_type: ErrorType) -> bool:
        """
        Determine if an item should be retried based on error type and retry count.
        
        Args:
            item: The processing item
            error_type: Type of error that occurred
            
        Returns:
            True if item should be retried
        """
        if item.retry_count >= self.max_retries:
            return False
        
        # Some errors should not be retried
        non_retryable_errors = {
            ErrorType.VALIDATION,
            ErrorType.PERMISSION,
            ErrorType.DATA_INTEGRITY,
        }
        
        return error_type not in non_retryable_errors
    
    def calculate_retry_delay(self, retry_count: int) -> float:
        """
        Calculate delay before retry using exponential backoff.
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (2 ** retry_count)
        return min(delay, self.max_delay)
    
    def _handle_database_constraint(self, item: ProcessingItem, exception: Exception, 
                                  context: Optional[Dict[str, Any]] = None):
        """Handle database constraint violations."""
        # For constraint violations, we might try to modify the data
        # This is a placeholder for specific constraint handling logic
        self.logger.info(f"Applying database constraint recovery for item {item.id}")
    
    def _handle_file_system_error(self, item: ProcessingItem, exception: Exception,
                                 context: Optional[Dict[str, Any]] = None):
        """Handle file system errors with comprehensive recovery strategies."""
        from process_management.file_system_handler import FileSystemErrorHandler
        
        # Initialize file system error handler if not already done
        if not hasattr(self, '_fs_error_handler'):
            self._fs_error_handler = FileSystemErrorHandler()
        
        # Extract file path from item data if available
        file_path = None
        if item.data and isinstance(item.data, dict):
            file_path = (item.data.get('file_path') or 
                        item.data.get('filepath') or 
                        item.data.get('filename'))
        
        if file_path:
            # Handle the file system error comprehensively
            error_result = self._fs_error_handler.handle_file_system_error(
                file_path, 
                context={'item_id': item.id, 'exception': str(exception)}
            )
            
            # Update item data with error handling results
            if not item.data:
                item.data = {}
            item.data['file_system_error'] = error_result
            
            self.logger.info(f"Applied file system error recovery for item {item.id}: {error_result.get('recovery_strategy', 'unknown')}")
        else:
            self.logger.warning(f"No file path found in item {item.id} for file system error recovery")
    
    def _handle_validation_error(self, item: ProcessingItem, exception: Exception,
                                context: Optional[Dict[str, Any]] = None):
        """Handle validation errors."""
        # For validation errors, we might try to sanitize data
        self.logger.info(f"Applying validation error recovery for item {item.id}")
    
    def _handle_transaction_error(self, item: ProcessingItem, exception: Exception,
                                 context: Optional[Dict[str, Any]] = None):
        """Handle transaction errors."""
        # For transaction errors, we might retry with a new transaction
        self.logger.info(f"Applying transaction error recovery for item {item.id}")
    
    def _handle_network_error(self, item: ProcessingItem, exception: Exception,
                             context: Optional[Dict[str, Any]] = None):
        """Handle network errors."""
        # For network errors, we might wait and retry
        self.logger.info(f"Applying network error recovery for item {item.id}")
    
    def _handle_permission_error(self, item: ProcessingItem, exception: Exception,
                                context: Optional[Dict[str, Any]] = None):
        """Handle permission errors."""
        # For permission errors, we might skip or use alternative access
        self.logger.info(f"Applying permission error recovery for item {item.id}")
    
    def _handle_data_integrity_error(self, item: ProcessingItem, exception: Exception,
                                    context: Optional[Dict[str, Any]] = None):
        """Handle data integrity errors."""
        # For data integrity errors, we might sanitize or skip
        self.logger.info(f"Applying data integrity error recovery for item {item.id}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all errors encountered.
        
        Returns:
            Dictionary containing error statistics and details
        """
        error_counts = {}
        for error in self.error_log:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'error_counts': error_counts,
            'recent_errors': self.error_log[-10:] if self.error_log else [],
            'error_rate': len(self.error_log) / max(1, len(self.error_log)),
        }


class BatchProcessor:
    """
    Processes items in manageable chunks with comprehensive error handling.
    
    Provides robust batch processing with transaction management,
    error recovery, and progress tracking.
    """
    
    def __init__(self, batch_size: int = 50, progress_tracker: Optional[ProgressTracker] = None,
                 error_manager: Optional[ErrorRecoveryManager] = None):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items to process in each batch
            progress_tracker: Optional progress tracker instance
            error_manager: Optional error recovery manager instance
        """
        self.batch_size = batch_size
        self.progress_tracker = progress_tracker
        self.error_manager = error_manager or ErrorRecoveryManager()
        self.batch_results: List[BatchResult] = []
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.total_skipped = 0
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
    
    def process_items(self, items: List[ProcessingItem], 
                     processor_func: Callable[[ProcessingItem], Any],
                     context: Optional[Dict[str, Any]] = None) -> List[BatchResult]:
        """
        Process a list of items in batches.
        
        Args:
            items: List of items to process
            processor_func: Function to process each item
            context: Additional context for processing
            
        Returns:
            List of batch results
        """
        self.logger.info(f"Starting batch processing of {len(items)} items with batch size {self.batch_size}")
        
        # Create batches
        batches = self._create_batches(items)
        
        for batch_index, batch_items in enumerate(batches):
            batch_id = f"batch_{batch_index + 1}"
            self.logger.info(f"Processing {batch_id} with {len(batch_items)} items")
            
            batch_result = self._process_batch(batch_id, batch_items, processor_func, context)
            self.batch_results.append(batch_result)
            
            # Update overall statistics
            self.total_processed += batch_result.total_items
            self.total_successful += len(batch_result.successful_items)
            self.total_failed += len(batch_result.failed_items)
            self.total_skipped += len(batch_result.skipped_items)
            
            # Update progress tracker
            if self.progress_tracker:
                for item in batch_result.successful_items:
                    self.progress_tracker.update_progress(1, ProcessingStatus.SUCCESS)
                for item in batch_result.failed_items:
                    self.progress_tracker.update_progress(1, ProcessingStatus.FAILED, item.error_type)
                for item in batch_result.skipped_items:
                    self.progress_tracker.update_progress(1, ProcessingStatus.SKIPPED)
        
        self.logger.info(f"Batch processing completed. Processed: {self.total_processed}, "
                        f"Successful: {self.total_successful}, Failed: {self.total_failed}, "
                        f"Skipped: {self.total_skipped}")
        
        return self.batch_results
    
    def _create_batches(self, items: List[ProcessingItem]) -> Generator[List[ProcessingItem], None, None]:
        """
        Create batches from a list of items.
        
        Args:
            items: List of items to batch
            
        Yields:
            Batches of items
        """
        for i in range(0, len(items), self.batch_size):
            yield items[i:i + self.batch_size]
    
    def _process_batch(self, batch_id: str, batch_items: List[ProcessingItem],
                      processor_func: Callable[[ProcessingItem], Any],
                      context: Optional[Dict[str, Any]] = None) -> BatchResult:
        """
        Process a single batch of items.
        
        Args:
            batch_id: Identifier for this batch
            batch_items: Items in this batch
            processor_func: Function to process each item
            context: Additional context for processing
            
        Returns:
            Batch processing result
        """
        start_time = time.time()
        batch_result = BatchResult(
            batch_id=batch_id,
            total_items=len(batch_items)
        )
        
        # Process items with transaction management
        with transaction.atomic():
            savepoint = transaction.savepoint()
            
            try:
                for item in batch_items:
                    try:
                        # Skip items that are already processed or should be skipped
                        if item.status in [ProcessingStatus.SUCCESS, ProcessingStatus.SKIPPED]:
                            batch_result.skipped_items.append(item)
                            continue
                        
                        # Process the item
                        item.status = ProcessingStatus.PROCESSING
                        item_start_time = time.time()
                        
                        result = processor_func(item)
                        
                        item.processing_time = time.time() - item_start_time
                        item.status = ProcessingStatus.SUCCESS
                        batch_result.successful_items.append(item)
                        
                    except Exception as e:
                        # Handle individual item error
                        item = self.error_manager.handle_error(item, e, context)
                        
                        if item.status == ProcessingStatus.RETRY:
                            # Add delay for retry
                            delay = self.error_manager.calculate_retry_delay(item.retry_count)
                            time.sleep(delay)
                            
                            # Try processing again
                            try:
                                item.status = ProcessingStatus.PROCESSING
                                result = processor_func(item)
                                item.status = ProcessingStatus.SUCCESS
                                batch_result.successful_items.append(item)
                            except Exception as retry_error:
                                item = self.error_manager.handle_error(item, retry_error, context)
                                batch_result.failed_items.append(item)
                        else:
                            batch_result.failed_items.append(item)
                
                # Commit the batch if we have any successful items
                if batch_result.successful_items:
                    transaction.savepoint_commit(savepoint)
                else:
                    transaction.savepoint_rollback(savepoint)
                    
            except Exception as batch_error:
                # Rollback the entire batch on critical error
                transaction.savepoint_rollback(savepoint)
                self.logger.error(f"Critical error in batch {batch_id}: {batch_error}")
                
                # Mark all items as failed
                for item in batch_items:
                    if item.status != ProcessingStatus.SUCCESS:
                        item = self.error_manager.handle_error(item, batch_error, context)
                        batch_result.failed_items.append(item)
        
        # Calculate batch statistics
        batch_result.processing_time = time.time() - start_time
        
        # Count errors by type
        for item in batch_result.failed_items:
            if item.error_type:
                batch_result.error_summary[item.error_type] = \
                    batch_result.error_summary.get(item.error_type, 0) + 1
        
        self.logger.info(f"Batch {batch_id} completed in {batch_result.processing_time:.2f}s. "
                        f"Success: {len(batch_result.successful_items)}, "
                        f"Failed: {len(batch_result.failed_items)}, "
                        f"Skipped: {len(batch_result.skipped_items)}")
        
        return batch_result
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive processing summary.
        
        Returns:
            Dictionary containing processing statistics
        """
        total_time = sum(batch.processing_time for batch in self.batch_results)
        
        return {
            'total_batches': len(self.batch_results),
            'total_items': self.total_processed,
            'successful_items': self.total_successful,
            'failed_items': self.total_failed,
            'skipped_items': self.total_skipped,
            'success_rate': (self.total_successful / self.total_processed * 100) if self.total_processed > 0 else 0,
            'total_processing_time': total_time,
            'average_batch_time': total_time / len(self.batch_results) if self.batch_results else 0,
            'items_per_second': self.total_processed / total_time if total_time > 0 else 0,
            'error_summary': self.error_manager.get_error_summary(),
        }
    
    def get_failed_items(self) -> List[ProcessingItem]:
        """
        Get all failed items across all batches.
        
        Returns:
            List of failed processing items
        """
        failed_items = []
        for batch_result in self.batch_results:
            failed_items.extend(batch_result.failed_items)
        return failed_items
    
    def get_retry_items(self) -> List[ProcessingItem]:
        """
        Get all items that should be retried.
        
        Returns:
            List of items marked for retry
        """
        retry_items = []
        for batch_result in self.batch_results:
            for item in batch_result.failed_items:
                if item.status == ProcessingStatus.RETRY:
                    retry_items.append(item)
        return retry_items


class CheckpointManager:
    """
    Manages migration checkpoints for idempotent migration and resume capability.
    
    Provides functionality to:
    - Create and manage migration checkpoints
    - Track individual item processing status
    - Detect already migrated items
    - Resume migrations from last checkpoint
    """
    
    def __init__(self, migration_id: str = None):
        """
        Initialize checkpoint manager.
        
        Args:
            migration_id: Optional migration ID. If not provided, generates a new one.
        """
        self.migration_id = migration_id or self._generate_migration_id()
        self.checkpoint = None
        self.logger = logging.getLogger(__name__)
    
    def _generate_migration_id(self) -> str:
        """Generate a unique migration ID."""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"migration_{timestamp}_{unique_id}"
    
    def create_checkpoint(self, total_items: int, config: Dict[str, Any]) -> 'MigrationCheckpoint':
        """
        Create a new migration checkpoint.
        
        Args:
            total_items: Total number of items to process
            config: Migration configuration
            
        Returns:
            Created MigrationCheckpoint instance
        """
        from process_management.models import MigrationCheckpoint
        
        self.checkpoint = MigrationCheckpoint.objects.create(
            migration_id=self.migration_id,
            total_items=total_items,
            batch_size=config.get('batch_size', 50),
            max_retries=config.get('max_retries', 3),
            error_threshold=config.get('error_threshold', 0.1),
            migration_config=config
        )
        
        self.logger.info(f"Created checkpoint for migration {self.migration_id} with {total_items} items")
        return self.checkpoint
    
    def get_or_create_checkpoint(self, total_items: int, config: Dict[str, Any]) -> 'MigrationCheckpoint':
        """
        Get existing checkpoint or create a new one.
        
        Args:
            total_items: Total number of items to process
            config: Migration configuration
            
        Returns:
            MigrationCheckpoint instance
        """
        from process_management.models import MigrationCheckpoint
        
        try:
            self.checkpoint = MigrationCheckpoint.objects.get(migration_id=self.migration_id)
            self.logger.info(f"Found existing checkpoint for migration {self.migration_id}")
        except MigrationCheckpoint.DoesNotExist:
            self.checkpoint = self.create_checkpoint(total_items, config)
        
        return self.checkpoint
    
    def find_resumable_migration(self) -> Optional['MigrationCheckpoint']:
        """
        Find the most recent resumable migration.
        
        Returns:
            MigrationCheckpoint instance if found, None otherwise
        """
        from process_management.models import MigrationCheckpoint
        
        resumable = MigrationCheckpoint.objects.filter(
            status__in=['started', 'in_progress', 'failed']
        ).order_by('-started_at').first()
        
        if resumable and resumable.can_resume():
            self.checkpoint = resumable
            self.migration_id = resumable.migration_id
            self.logger.info(f"Found resumable migration {self.migration_id}")
            return resumable
        
        return None
    
    def create_migration_items(self, processing_items: List[ProcessingItem]) -> List['MigrationItem']:
        """
        Create MigrationItem records for tracking individual items.
        
        Args:
            processing_items: List of ProcessingItem instances
            
        Returns:
            List of created MigrationItem instances
        """
        from process_management.models import MigrationItem
        
        if not self.checkpoint:
            raise ValueError("No checkpoint available. Call create_checkpoint first.")
        
        migration_items = []
        
        for item in processing_items:
            # Extract source information for idempotency checks
            source_info = self._extract_source_info(item)
            
            migration_item = MigrationItem(
                checkpoint=self.checkpoint,
                item_id=item.id,
                item_type=item.data.get('type', 'unknown'),
                source_filename=source_info.get('filename', ''),
                source_folder_path=source_info.get('folder_path', ''),
                source_identifier=source_info.get('identifier', ''),
                item_data=item.data
            )
            migration_items.append(migration_item)
        
        # Bulk create for efficiency
        created_items = MigrationItem.objects.bulk_create(migration_items, ignore_conflicts=True)
        self.logger.info(f"Created {len(created_items)} migration items")
        
        return created_items
    
    def _extract_source_info(self, item: ProcessingItem) -> Dict[str, str]:
        """
        Extract source information from processing item for idempotency checks.
        
        Args:
            item: ProcessingItem instance
            
        Returns:
            Dictionary with source information
        """
        source_info = {}
        
        if item.data.get('type') == 'process_candidate':
            candidate_data = item.data.get('candidate_data', {})
            # For process candidates, we use the process name and department as identifiers
            source_info['filename'] = candidate_data.get('name', '')
            source_info['folder_path'] = candidate_data.get('department', '')
            source_info['identifier'] = f"process_{candidate_data.get('process_code', '')}"
        
        elif item.data.get('type') == 'document':
            doc_data = item.data.get('document_data', {})
            source_info['filename'] = doc_data.get('filename', '')
            source_info['folder_path'] = doc_data.get('folder_path', '')
            source_info['identifier'] = doc_data.get('id', '')
        
        return source_info
    
    def get_already_migrated_items(self) -> List[str]:
        """
        Get list of item IDs that have already been successfully migrated.
        
        Returns:
            List of item IDs that are already migrated
        """
        if not self.checkpoint:
            return []
        
        from process_management.models import MigrationItem
        
        migrated_items = MigrationItem.objects.filter(
            checkpoint=self.checkpoint,
            status='completed'
        ).values_list('item_id', flat=True)
        
        return list(migrated_items)
    
    def check_item_already_migrated(self, filename: str, folder_path: str) -> bool:
        """
        Check if an item with the given filename and folder path has already been migrated.
        
        Args:
            filename: Source filename
            folder_path: Source folder path
            
        Returns:
            True if item has already been migrated
        """
        from process_management.models import MigrationItem
        
        # Check across all completed migrations, not just current checkpoint
        existing = MigrationItem.objects.filter(
            source_filename=filename,
            source_folder_path=folder_path,
            status='completed'
        ).first()
        
        if existing and existing.is_already_migrated():
            return True
        
        return False
    
    def update_item_status(self, item_id: str, status: str, **kwargs):
        """
        Update the status of a migration item.
        
        Args:
            item_id: ID of the item to update
            status: New status
            **kwargs: Additional fields to update
        """
        from process_management.models import MigrationItem
        
        try:
            migration_item = MigrationItem.objects.get(
                checkpoint=self.checkpoint,
                item_id=item_id
            )
            
            migration_item.status = status
            
            # Update additional fields
            for field, value in kwargs.items():
                if hasattr(migration_item, field):
                    setattr(migration_item, field, value)
            
            if status in ['completed', 'failed', 'skipped']:
                migration_item.processed_at = timezone.now()
            
            migration_item.save()
            
            # Update checkpoint progress
            if self.checkpoint:
                if status == 'completed':
                    self.checkpoint.update_progress(processed=1, successful=1)
                elif status == 'failed':
                    self.checkpoint.update_progress(processed=1, failed=1)
                elif status == 'skipped':
                    self.checkpoint.update_progress(processed=1, skipped=1)
            
        except MigrationItem.DoesNotExist:
            self.logger.warning(f"Migration item {item_id} not found for status update")
    
    def get_pending_items(self) -> List['MigrationItem']:
        """
        Get list of pending migration items for resume functionality.
        
        Returns:
            List of MigrationItem instances that are pending
        """
        from process_management.models import MigrationItem
        
        if not self.checkpoint:
            return []
        
        return list(MigrationItem.objects.filter(
            checkpoint=self.checkpoint,
            status='pending'
        ).order_by('created_at'))
    
    def mark_checkpoint_completed(self):
        """Mark the current checkpoint as completed."""
        if self.checkpoint:
            self.checkpoint.mark_completed()
            self.logger.info(f"Marked checkpoint {self.migration_id} as completed")
    
    def mark_checkpoint_failed(self, error_message: str, error_details: Dict = None):
        """Mark the current checkpoint as failed."""
        if self.checkpoint:
            self.checkpoint.mark_failed(error_message, error_details or {})
            self.logger.error(f"Marked checkpoint {self.migration_id} as failed: {error_message}")
    
    def get_checkpoint_summary(self) -> Dict[str, Any]:
        """
        Get summary information about the current checkpoint.
        
        Returns:
            Dictionary with checkpoint summary
        """
        if not self.checkpoint:
            return {}
        
        return {
            'migration_id': self.checkpoint.migration_id,
            'status': self.checkpoint.status,
            'total_items': self.checkpoint.total_items,
            'processed_items': self.checkpoint.processed_items,
            'successful_items': self.checkpoint.successful_items,
            'failed_items': self.checkpoint.failed_items,
            'skipped_items': self.checkpoint.skipped_items,
            'progress_percentage': self.checkpoint.get_progress_percentage(),
            'success_rate': self.checkpoint.get_success_rate(),
            'started_at': self.checkpoint.started_at,
            'last_updated': self.checkpoint.last_updated,
            'can_resume': self.checkpoint.can_resume(),
        }


class IdempotentMigrationManager:
    """
    Manages idempotent migration operations with resume capability.
    
    Combines checkpoint management with batch processing to provide
    robust migration functionality that can be safely resumed.
    """
    
    def __init__(self, migration_id: str = None, batch_size: int = 50):
        """
        Initialize idempotent migration manager.
        
        Args:
            migration_id: Optional migration ID for resume functionality
            batch_size: Batch size for processing
        """
        self.checkpoint_manager = CheckpointManager(migration_id)
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
    
    def prepare_migration(self, items: List[ProcessingItem], config: Dict[str, Any], 
                         skip_existing: bool = True) -> Tuple[List[ProcessingItem], 'MigrationCheckpoint']:
        """
        Prepare migration by creating checkpoint and filtering already migrated items.
        
        Args:
            items: List of items to process
            config: Migration configuration
            skip_existing: Whether to skip already migrated items
            
        Returns:
            Tuple of (filtered_items, checkpoint)
        """
        # Create or get checkpoint
        checkpoint = self.checkpoint_manager.get_or_create_checkpoint(len(items), config)
        
        # Filter out already migrated items if requested
        if skip_existing:
            filtered_items = []
            skipped_count = 0
            
            for item in items:
                source_info = self.checkpoint_manager._extract_source_info(item)
                
                if self.checkpoint_manager.check_item_already_migrated(
                    source_info.get('filename', ''),
                    source_info.get('folder_path', '')
                ):
                    skipped_count += 1
                    self.logger.debug(f"Skipping already migrated item: {item.id}")
                else:
                    filtered_items.append(item)
            
            if skipped_count > 0:
                self.logger.info(f"Skipped {skipped_count} already migrated items")
                # Update checkpoint with skipped items
                checkpoint.update_progress(skipped=skipped_count)
            
            items = filtered_items
        
        # Create migration items for tracking
        self.checkpoint_manager.create_migration_items(items)
        
        return items, checkpoint
    
    def resume_migration(self) -> Tuple[List[ProcessingItem], Optional['MigrationCheckpoint']]:
        """
        Resume a previous migration from checkpoint.
        
        Returns:
            Tuple of (pending_items, checkpoint) or ([], None) if no resumable migration
        """
        checkpoint = self.checkpoint_manager.find_resumable_migration()
        
        if not checkpoint:
            self.logger.info("No resumable migration found")
            return [], None
        
        # Get pending items
        pending_migration_items = self.checkpoint_manager.get_pending_items()
        
        # Convert MigrationItem back to ProcessingItem
        processing_items = []
        for migration_item in pending_migration_items:
            processing_item = ProcessingItem(
                id=migration_item.item_id,
                data=migration_item.item_data,
                status=ProcessingStatus.PENDING
            )
            processing_items.append(processing_item)
        
        self.logger.info(f"Resuming migration {checkpoint.migration_id} with {len(processing_items)} pending items")
        return processing_items, checkpoint
    
    def execute_idempotent_migration(self, items: List[ProcessingItem], 
                                   processor_func: Callable[[ProcessingItem], Any],
                                   config: Dict[str, Any],
                                   skip_existing: bool = True) -> Dict[str, Any]:
        """
        Execute migration with idempotent behavior and checkpoint tracking.
        
        Args:
            items: List of items to process
            processor_func: Function to process each item
            config: Migration configuration
            skip_existing: Whether to skip already migrated items
            
        Returns:
            Migration results dictionary
        """
        try:
            # Prepare migration
            filtered_items, checkpoint = self.prepare_migration(items, config, skip_existing)
            
            if not filtered_items:
                self.logger.info("No items to process after filtering")
                self.checkpoint_manager.mark_checkpoint_completed()
                return self._create_results_summary([], checkpoint)
            
            # Set up batch processor with checkpoint integration
            progress_tracker = ProgressTracker(len(filtered_items), "Idempotent Migration")
            error_manager = ErrorRecoveryManager(
                max_retries=config.get('max_retries', 3)
            )
            
            batch_processor = BatchProcessor(
                batch_size=self.batch_size,
                progress_tracker=progress_tracker,
                error_manager=error_manager
            )
            
            # Create enhanced processor function that updates checkpoints
            def checkpoint_aware_processor(item: ProcessingItem) -> Any:
                try:
                    # Update item status to processing
                    self.checkpoint_manager.update_item_status(item.id, 'processing')
                    
                    # Process the item
                    result = processor_func(item)
                    
                    # Update item status to completed
                    process_id = getattr(result, 'id', None) if hasattr(result, 'id') else None
                    self.checkpoint_manager.update_item_status(
                        item.id, 
                        'completed',
                        created_process_id=process_id
                    )
                    
                    return result
                    
                except Exception as e:
                    # Update item status to failed
                    self.checkpoint_manager.update_item_status(
                        item.id,
                        'failed',
                        error_message=str(e),
                        error_type=type(e).__name__
                    )
                    raise e
            
            # Execute batch processing
            batch_results = batch_processor.process_items(
                filtered_items,
                checkpoint_aware_processor,
                context=config
            )
            
            # Mark checkpoint as completed
            self.checkpoint_manager.mark_checkpoint_completed()
            
            return self._create_results_summary(batch_results, checkpoint)
            
        except Exception as e:
            # Mark checkpoint as failed
            self.checkpoint_manager.mark_checkpoint_failed(str(e), {'exception_type': type(e).__name__})
            raise e
    
    def _create_results_summary(self, batch_results: List, checkpoint: 'MigrationCheckpoint') -> Dict[str, Any]:
        """Create comprehensive results summary."""
        total_successful = sum(len(batch.successful_items) for batch in batch_results) if batch_results else 0
        total_failed = sum(len(batch.failed_items) for batch in batch_results) if batch_results else 0
        total_skipped = sum(len(batch.skipped_items) for batch in batch_results) if batch_results else 0
        
        return {
            'migration_id': checkpoint.migration_id if checkpoint else None,
            'checkpoint_summary': self.checkpoint_manager.get_checkpoint_summary(),
            'batch_results': {
                'total_batches': len(batch_results) if batch_results else 0,
                'successful_items': total_successful,
                'failed_items': total_failed,
                'skipped_items': total_skipped,
            },
            'can_resume': checkpoint.can_resume() if checkpoint else False,
        }