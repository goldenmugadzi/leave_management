"""
Cursor-based pagination utilities for better performance
"""
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import json


class CursorPaginator:
    """
    Cursor-based pagination for better performance with large datasets.
    Uses created_at timestamp as cursor for consistent ordering.
    """
    
    def __init__(self, queryset, page_size=25, cursor_field='created_at'):
        self.queryset = queryset
        self.page_size = page_size
        self.cursor_field = cursor_field
        
    def paginate(self, cursor=None, direction='next'):
        """
        Paginate queryset using cursor-based approach.
        
        Args:
            cursor: Base64 encoded cursor string (timestamp)
            direction: 'next' or 'prev' for pagination direction
            
        Returns:
            dict: {
                'data': list of objects,
                'next_cursor': next page cursor,
                'prev_cursor': previous page cursor,
                'has_next': boolean,
                'has_prev': boolean,
                'total_count': total count (if requested)
            }
        """
        queryset = self.queryset.order_by(f'-{self.cursor_field}')
        
        # Decode cursor if provided
        cursor_timestamp = None
        if cursor:
            try:
                cursor_timestamp = self._decode_cursor(cursor)
            except (ValueError, TypeError):
                # Invalid cursor, start from beginning
                cursor_timestamp = None
        
        # Apply cursor filter
        if cursor_timestamp:
            if direction == 'next':
                queryset = queryset.filter(**{f'{self.cursor_field}__lt': cursor_timestamp})
            else:  # prev
                queryset = queryset.filter(**{f'{self.cursor_field}__gt': cursor_timestamp})
                queryset = queryset.order_by(f'{self.cursor_field}')  # Reverse order for prev
        
        # Get one extra item to check if there are more pages
        page_items = list(queryset[:self.page_size + 1])
        
        has_next = len(page_items) > self.page_size
        if has_next:
            page_items = page_items[:self.page_size]
        
        # Generate cursors
        next_cursor = None
        prev_cursor = None
        
        if page_items:
            if has_next:
                next_cursor = self._encode_cursor(getattr(page_items[-1], self.cursor_field))
            
            if cursor_timestamp:
                prev_cursor = self._encode_cursor(getattr(page_items[0], self.cursor_field))
        
        return {
            'data': page_items,
            'next_cursor': next_cursor,
            'prev_cursor': prev_cursor,
            'has_next': has_next,
            'has_prev': cursor_timestamp is not None,
            'total_count': None  # Not calculated for performance
        }
    
    def _encode_cursor(self, timestamp):
        """Encode timestamp to base64 cursor"""
        import base64
        cursor_data = {
            'timestamp': timestamp.isoformat(),
            'field': self.cursor_field
        }
        return base64.b64encode(json.dumps(cursor_data).encode()).decode()
    
    def _decode_cursor(self, cursor):
        """Decode base64 cursor to timestamp"""
        import base64
        cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
        return datetime.fromisoformat(cursor_data['timestamp'])


class OptimizedPaginator(Paginator):
    """
    Optimized Django Paginator with count caching and performance improvements.
    """
    
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        super().__init__(object_list, per_page, orphans, allow_empty_first_page)
        self._count = None
    
    @property
    def count(self):
        """
        Override count to use cached value and optimize for large datasets.
        """
        if self._count is None:
            # For very large datasets, we can skip count calculation
            # and just estimate based on current page
            try:
                self._count = self.object_list.count()
            except Exception:
                # Fallback to estimation
                self._count = 1000  # Conservative estimate
        return self._count
    
    def get_page(self, number):
        """
        Override get_page to use optimized pagination.
        """
        try:
            return super().get_page(number)
        except Exception:
            # Fallback to first page if there's an issue
            return self.page(1)


def get_paginated_data(queryset, page=1, per_page=25, use_cursor=False, cursor=None):
    """
    Get paginated data with optimized pagination.
    
    Args:
        queryset: Django queryset
        page: Page number (for offset pagination)
        per_page: Items per page
        use_cursor: Whether to use cursor-based pagination
        cursor: Cursor for cursor-based pagination
        
    Returns:
        dict: Paginated data with metadata
    """
    if use_cursor:
        paginator = CursorPaginator(queryset, per_page)
        result = paginator.paginate(cursor)
        
        return {
            'data': result['data'],
            'pagination': {
                'type': 'cursor',
                'next_cursor': result['next_cursor'],
                'prev_cursor': result['prev_cursor'],
                'has_next': result['has_next'],
                'has_prev': result['has_prev'],
            }
        }
    else:
        paginator = OptimizedPaginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        return {
            'data': list(page_obj),
            'pagination': {
                'type': 'offset',
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_count': paginator.count,
            }
        }
