"""
Memory Monitoring Utilities for Comparative Schedules
Stage 2 Optimization: Memory Protection & Performance
"""

import psutil
import logging
from django.conf import settings
from .pagination_config import MEMORY_WARNING_THRESHOLD, MEMORY_CRITICAL_THRESHOLD

logger = logging.getLogger(__name__)

def get_memory_usage():
    """
    Get current memory usage in MB
    
    Returns:
        dict: Memory usage statistics
    """
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'total_mb': psutil.virtual_memory().total / 1024 / 1024
        }
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return {
            'rss_mb': 0,
            'vms_mb': 0,
            'percent': 0,
            'available_mb': 0,
            'total_mb': 0,
            'error': str(e)
        }

def check_memory_limits(operation_name="operation"):
    """
    Check if memory usage is within safe limits
    
    Args:
        operation_name: Name of the operation being checked
        
    Returns:
        dict: Memory status and recommendations
    """
    memory_stats = get_memory_usage()
    rss_mb = memory_stats['rss_mb']
    
    status = {
        'memory_mb': rss_mb,
        'status': 'ok',
        'warnings': [],
        'should_reduce_page_size': False,
        'recommended_page_size': None
    }
    
    if rss_mb > MEMORY_CRITICAL_THRESHOLD:
        status['status'] = 'critical'
        status['warnings'].append(f"Critical memory usage: {rss_mb:.1f}MB")
        status['should_reduce_page_size'] = True
        status['recommended_page_size'] = 10  # Very small page size
        logger.critical(f"Critical memory usage ({rss_mb:.1f}MB) during {operation_name}")
        
    elif rss_mb > MEMORY_WARNING_THRESHOLD:
        status['status'] = 'warning'
        status['warnings'].append(f"High memory usage: {rss_mb:.1f}MB")
        status['should_reduce_page_size'] = True
        status['recommended_page_size'] = 25  # Reduced page size
        logger.warning(f"High memory usage ({rss_mb:.1f}MB) during {operation_name}")
    
    return status

def memory_efficient_queryset_iterator(queryset, chunk_size=100):
    """
    Memory-efficient iterator for large querysets using cursor pagination
    
    Args:
        queryset: Django queryset to iterate
        chunk_size: Size of each chunk
        
    Yields:
        Objects from the queryset in chunks
    """
    # Get the model and primary key field
    model = queryset.model
    pk_field = model._meta.pk.name
    
    # Start with the first chunk
    last_pk = 0
    
    while True:
        # Get next chunk using cursor-based pagination
        chunk = list(queryset.filter(**{f'{pk_field}__gt': last_pk}).order_by(pk_field)[:chunk_size])
        
        if not chunk:
            break
            
        # Yield each object in the chunk
        for obj in chunk:
            yield obj
            
        # Update cursor for next iteration
        last_pk = getattr(chunk[-1], pk_field)
        
        # Memory check after each chunk
        memory_status = check_memory_limits(f"cursor_pagination_chunk_{last_pk}")
        if memory_status['should_reduce_page_size']:
            # Reduce chunk size if memory pressure detected
            chunk_size = max(10, chunk_size // 2)
            logger.info(f"Reduced chunk size to {chunk_size} due to memory pressure")

def get_optimized_page_size_for_memory(requested_size, data_type='default'):
    """
    Get page size optimized for current memory conditions
    
    Args:
        requested_size: Originally requested page size
        data_type: Type of data being paginated
        
    Returns:
        int: Optimized page size
    """
    memory_status = check_memory_limits("pagination_request")
    
    if memory_status['should_reduce_page_size']:
        recommended_size = memory_status['recommended_page_size']
        optimized_size = min(requested_size, recommended_size)
        logger.info(f"Page size reduced from {requested_size} to {optimized_size} due to memory pressure")
        return optimized_size
    
    return requested_size

class MemoryMonitoringMiddleware:
    """
    Middleware to monitor memory usage during requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check memory before request
        start_memory = get_memory_usage()
        
        response = self.get_response(request)
        
        # Check memory after request
        end_memory = get_memory_usage()
        
        # Calculate memory delta
        memory_delta = end_memory['rss_mb'] - start_memory['rss_mb']
        
        # Log significant memory increases
        if memory_delta > 50:  # More than 50MB increase
            logger.warning(f"Significant memory increase ({memory_delta:.1f}MB) for {request.path}")
        
        # Add memory info to response headers (for debugging)
        if settings.DEBUG:
            response['X-Memory-Usage'] = f"{end_memory['rss_mb']:.1f}MB"
            response['X-Memory-Delta'] = f"{memory_delta:.1f}MB"
        
        return response 