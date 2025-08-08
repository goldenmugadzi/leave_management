# Pagination Configuration for Comparative Schedules
# Stage 2 Optimization: Memory Protection & Performance

# Maximum limits to prevent memory exhaustion
MAX_PAGE_SIZE = 100         # Absolute maximum items per page
DEFAULT_PAGE_SIZE = 50      # Default page size for new requests
DATATABLE_MAX_SIZE = 100    # Maximum for DataTable requests
DATATABLE_DEFAULT_SIZE = 25 # Default for DataTable requests

# Large dataset handling
LARGE_DATASET_THRESHOLD = 1000  # When to use cursor pagination
CURSOR_PAGE_SIZE = 50           # Page size for cursor-based pagination

# Memory monitoring thresholds
MEMORY_WARNING_THRESHOLD = 500  # MB - Log warning
MEMORY_CRITICAL_THRESHOLD = 800 # MB - Force smaller page sizes

# Cache settings for pagination
PAGINATION_CACHE_TIMEOUT = 300  # 5 minutes
MAX_CACHED_PAGES = 10          # Maximum pages to cache per query

# Special handling for different data types
PAGINATION_LIMITS = {
    'pr_items': {
        'max_size': 100,
        'default_size': 50,
        'warning_threshold': 200,  # Items count
    },
    'bids': {
        'max_size': 100,
        'default_size': 25,
        'warning_threshold': 100,
    },
    'schedules': {
        'max_size': 50,
        'default_size': 25,
        'warning_threshold': 100,
    },
    'compliance': {
        'max_size': 50,
        'default_size': 25,
        'warning_threshold': 75,
    },
    'committee': {
        'max_size': 30,
        'default_size': 20,
        'warning_threshold': 50,
    }
}

def get_safe_page_size(requested_size, data_type='default', total_items=0):
    """
    Get safe page size with validation and memory protection
    
    Args:
        requested_size: Size requested by client
        data_type: Type of data being paginated
        total_items: Total number of items in dataset
    
    Returns:
        Safe page size within limits
    """
    limits = PAGINATION_LIMITS.get(data_type, {
        'max_size': MAX_PAGE_SIZE,
        'default_size': DEFAULT_PAGE_SIZE,
        'warning_threshold': 100
    })
    
    # Use default if no request or invalid request
    if not requested_size or requested_size <= 0:
        return limits['default_size']
    
    # Enforce maximum limit
    safe_size = min(requested_size, limits['max_size'])
    
    # Dynamic adjustment for large datasets
    if total_items > LARGE_DATASET_THRESHOLD:
        # Reduce page size for very large datasets
        safe_size = min(safe_size, CURSOR_PAGE_SIZE)
    
    return safe_size

def get_pagination_info(page, page_size, total_items):
    """
    Get comprehensive pagination information
    
    Returns dict with pagination metadata and warnings
    """
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 1
    
    info = {
        'current_page': page,
        'page_size': page_size,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
        'start_index': (page - 1) * page_size + 1 if total_items > 0 else 0,
        'end_index': min(page * page_size, total_items),
        'warnings': []
    }
    
    # Add warnings for potentially problematic scenarios
    if total_items > LARGE_DATASET_THRESHOLD:
        info['warnings'].append(f'Large dataset ({total_items} items) - consider using filters')
    
    if page_size > 50:
        info['warnings'].append(f'Large page size ({page_size}) may impact performance')
    
    if total_pages > 100:
        info['warnings'].append(f'Many pages ({total_pages}) - consider more specific search criteria')
    
    return info 