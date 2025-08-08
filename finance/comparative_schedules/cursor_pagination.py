"""
Cursor-Based Pagination for Large Datasets
Stage 2 Optimization: Memory-Efficient Large Data Handling
"""

from django.http import JsonResponse
from django.core.paginator import Paginator
from .memory_monitor import check_memory_limits, memory_efficient_queryset_iterator
from .pagination_config import LARGE_DATASET_THRESHOLD, CURSOR_PAGE_SIZE
import logging

logger = logging.getLogger(__name__)

class CursorPaginator:
    """
    Memory-efficient cursor-based paginator for large datasets
    """
    
    def __init__(self, queryset, page_size=CURSOR_PAGE_SIZE, order_by='id'):
        self.queryset = queryset
        self.page_size = page_size
        self.order_by = order_by
        self.total_count = None
        
    def get_page(self, cursor=None, direction='next'):
        """
        Get a page of results using cursor-based pagination
        
        Args:
            cursor: The cursor value (usually a primary key)
            direction: 'next' or 'previous'
            
        Returns:
            dict: Page data with cursor information
        """
        # Build the query based on cursor and direction
        if cursor:
            if direction == 'next':
                filtered_queryset = self.queryset.filter(**{f'{self.order_by}__gt': cursor})
            else:  # previous
                filtered_queryset = self.queryset.filter(**{f'{self.order_by}__lt': cursor}).order_by(f'-{self.order_by}')
        else:
            filtered_queryset = self.queryset
            
        # Always order by the cursor field
        if direction != 'previous':
            filtered_queryset = filtered_queryset.order_by(self.order_by)
        
        # Get one extra item to check if there are more pages
        items = list(filtered_queryset[:self.page_size + 1])
        
        # Check if there are more items
        has_more = len(items) > self.page_size
        if has_more:
            items = items[:self.page_size]  # Remove the extra item
        
        # If direction was previous, reverse the order back
        if direction == 'previous':
            items.reverse()
        
        # Determine cursors for next/previous pages
        next_cursor = None
        previous_cursor = None
        
        if items:
            if has_more and direction == 'next':
                next_cursor = getattr(items[-1], self.order_by)
            if cursor and direction == 'next':
                previous_cursor = getattr(items[0], self.order_by)
            elif has_more and direction == 'previous':
                previous_cursor = getattr(items[0], self.order_by)
                next_cursor = getattr(items[-1], self.order_by)
        
        return {
            'items': items,
            'has_next': has_more if direction == 'next' else bool(cursor),
            'has_previous': bool(cursor) if direction == 'next' else has_more,
            'next_cursor': next_cursor,
            'previous_cursor': previous_cursor,
            'page_size': len(items),
            'cursor_field': self.order_by
        }
    
    def get_total_count(self):
        """
        Get total count (cached after first call)
        """
        if self.total_count is None:
            self.total_count = self.queryset.count()
        return self.total_count

def paginate_large_dataset(queryset, request, data_type='default', serializer_func=None):
    """
    Intelligently paginate datasets - uses cursor pagination for large datasets
    
    Args:
        queryset: Django queryset to paginate
        request: HTTP request object
        data_type: Type of data for pagination limits
        serializer_func: Function to serialize each item
        
    Returns:
        JsonResponse with paginated data
    """
    # Check memory status first
    memory_status = check_memory_limits(f"paginate_{data_type}")
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    requested_page_size = int(request.GET.get('page_size', 50))
    cursor = request.GET.get('cursor')
    direction = request.GET.get('direction', 'next')
    use_cursor = request.GET.get('use_cursor', 'auto').lower()
    
    # Get total count for decision making
    total_count = queryset.count()
    
    # Decide pagination strategy
    should_use_cursor = (
        use_cursor == 'true' or 
        (use_cursor == 'auto' and total_count > LARGE_DATASET_THRESHOLD) or
        memory_status['should_reduce_page_size']
    )
    
    if should_use_cursor:
        # Use cursor-based pagination for large datasets
        logger.info(f"Using cursor pagination for {data_type} with {total_count} items")
        
        # Adjust page size based on memory pressure
        if memory_status['should_reduce_page_size']:
            page_size = min(requested_page_size, memory_status['recommended_page_size'])
        else:
            page_size = min(requested_page_size, CURSOR_PAGE_SIZE)
        
        paginator = CursorPaginator(queryset, page_size)
        page_data = paginator.get_page(cursor, direction)
        
        # Serialize items
        if serializer_func:
            serialized_items = [serializer_func(item) for item in page_data['items']]
        else:
            serialized_items = list(page_data['items'].values())
        
        return JsonResponse({
            'success': True,
            'data': serialized_items,
            'pagination': {
                'type': 'cursor',
                'page_size': page_data['page_size'],
                'has_next': page_data['has_next'],
                'has_previous': page_data['has_previous'],
                'next_cursor': page_data['next_cursor'],
                'previous_cursor': page_data['previous_cursor'],
                'cursor_field': page_data['cursor_field'],
                'total_count': total_count,
                'estimated_pages': (total_count + page_size - 1) // page_size
            },
            'performance_info': {
                'pagination_type': 'cursor',
                'memory_optimized': memory_status['should_reduce_page_size'],
                'memory_status': memory_status['status'],
                'total_items': total_count
            }
        })
    
    else:
        # Use traditional pagination for smaller datasets
        logger.info(f"Using traditional pagination for {data_type} with {total_count} items")
        
        from .pagination_config import get_safe_page_size, get_pagination_info
        
        page_size = get_safe_page_size(requested_page_size, data_type, total_count)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize items
        if serializer_func:
            serialized_items = [serializer_func(item) for item in page_obj]
        else:
            serialized_items = list(page_obj.object_list.values())
        
        pagination_info = get_pagination_info(page, page_size, total_count)
        
        return JsonResponse({
            'success': True,
            'data': serialized_items,
            'pagination': {
                'type': 'traditional',
                **pagination_info
            },
            'performance_info': {
                'pagination_type': 'traditional',
                'memory_optimized': requested_page_size != page_size,
                'memory_status': memory_status['status'],
                'total_items': total_count
            }
        })

def get_cursor_pagination_response(items, cursor_info, total_count, data_type):
    """
    Helper function to create standardized cursor pagination responses
    """
    return {
        'success': True,
        'data': items,
        'pagination': {
            'type': 'cursor',
            'page_size': len(items),
            'has_next': cursor_info['has_next'],
            'has_previous': cursor_info['has_previous'], 
            'next_cursor': cursor_info['next_cursor'],
            'previous_cursor': cursor_info['previous_cursor'],
            'cursor_field': cursor_info['cursor_field'],
            'total_count': total_count,
            'data_type': data_type
        },
        'usage_hints': {
            'next_page_url': f"?cursor={cursor_info['next_cursor']}&direction=next" if cursor_info['has_next'] else None,
            'previous_page_url': f"?cursor={cursor_info['previous_cursor']}&direction=previous" if cursor_info['has_previous'] else None,
            'force_cursor_pagination': "?use_cursor=true",
            'force_traditional_pagination': "?use_cursor=false"
        }
    } 