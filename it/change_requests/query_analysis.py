"""
Query analysis utilities for performance optimization
"""
import time
import logging
from django.db import connection
from django.conf import settings
from django.utils import timezone
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Utility class for analyzing and optimizing database queries.
    """
    
    def __init__(self):
        self.query_log = []
        self.slow_queries = []
        self.threshold_ms = 100  # Default threshold for slow queries
    
    def log_query(self, query, execution_time_ms, params=None):
        """Log a query with its execution time"""
        query_info = {
            'query': query,
            'execution_time_ms': execution_time_ms,
            'params': params,
            'timestamp': timezone.now(),
            'is_slow': execution_time_ms > self.threshold_ms
        }
        
        self.query_log.append(query_info)
        
        if query_info['is_slow']:
            self.slow_queries.append(query_info)
            logger.warning(f"Slow query detected: {execution_time_ms}ms - {query[:100]}...")
    
    def get_slow_queries(self):
        """Get all slow queries"""
        return self.slow_queries
    
    def get_query_stats(self):
        """Get query statistics"""
        if not self.query_log:
            return {}
        
        total_queries = len(self.query_log)
        slow_queries = len(self.slow_queries)
        avg_time = sum(q['execution_time_ms'] for q in self.query_log) / total_queries
        
        return {
            'total_queries': total_queries,
            'slow_queries': slow_queries,
            'slow_query_percentage': (slow_queries / total_queries) * 100,
            'average_execution_time_ms': round(avg_time, 2),
            'threshold_ms': self.threshold_ms
        }
    
    def clear_log(self):
        """Clear the query log"""
        self.query_log = []
        self.slow_queries = []


# Global query analyzer instance
query_analyzer = QueryAnalyzer()


@contextmanager
def analyze_queries():
    """
    Context manager to analyze queries within a block of code.
    """
    initial_query_count = len(connection.queries)
    start_time = time.time()
    
    try:
        yield query_analyzer
    finally:
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Log new queries
        new_queries = connection.queries[initial_query_count:]
        for query_info in new_queries:
            query_analyzer.log_query(
                query_info['sql'],
                float(query_info['time']) * 1000,  # Convert to milliseconds
                query_info.get('params')
            )


def analyze_queryset_performance(queryset, description="Query"):
    """
    Analyze the performance of a queryset.
    
    Args:
        queryset: Django queryset to analyze
        description: Description of the query for logging
        
    Returns:
        dict: Performance analysis results
    """
    with analyze_queries() as analyzer:
        start_time = time.time()
        
        # Force evaluation of the queryset
        results = list(queryset)
        
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Get query statistics
        stats = analyzer.get_query_stats()
        
        analysis = {
            'description': description,
            'execution_time_ms': round(execution_time_ms, 2),
            'result_count': len(results),
            'query_count': stats.get('total_queries', 0),
            'slow_queries': stats.get('slow_queries', 0),
            'average_query_time_ms': stats.get('average_execution_time_ms', 0),
            'is_optimized': stats.get('slow_queries', 0) == 0
        }
        
        logger.info(f"Query analysis for '{description}': {analysis}")
        return analysis


def suggest_query_optimizations(queryset, common_patterns=True):
    """
    Suggest optimizations for a queryset.
    
    Args:
        queryset: Django queryset to analyze
        common_patterns: Whether to check for common optimization patterns
        
    Returns:
        list: List of optimization suggestions
    """
    suggestions = []
    
    # Check for common optimization patterns
    if common_patterns:
        # Check for select_related opportunities
        if hasattr(queryset, 'query') and queryset.query.select_related:
            suggestions.append("✅ select_related is already being used")
        else:
            suggestions.append("💡 Consider using select_related() for foreign key relationships")
        
        # Check for prefetch_related opportunities
        if hasattr(queryset, 'query') and queryset.query.prefetch_related:
            suggestions.append("✅ prefetch_related is already being used")
        else:
            suggestions.append("💡 Consider using prefetch_related() for reverse foreign key relationships")
        
        # Check for only() usage
        if hasattr(queryset, 'query') and queryset.query.deferred_loading:
            suggestions.append("✅ only() is being used to limit fields")
        else:
            suggestions.append("💡 Consider using only() to limit fields if you don't need all fields")
        
        # Check for proper ordering
        if hasattr(queryset, 'query') and queryset.query.order_by:
            suggestions.append("✅ Ordering is specified")
        else:
            suggestions.append("💡 Consider adding explicit ordering for consistent results")
    
    return suggestions


def benchmark_query_variations(queryset, variations):
    """
    Benchmark different variations of a query to find the optimal one.
    
    Args:
        queryset: Base Django queryset
        variations: List of queryset variations to test
        
    Returns:
        dict: Benchmark results
    """
    results = {}
    
    for i, variation in enumerate(variations):
        description = f"Variation {i+1}"
        analysis = analyze_queryset_performance(variation, description)
        results[description] = analysis
    
    # Find the best performing variation
    best_variation = min(results.items(), key=lambda x: x[1]['execution_time_ms'])
    
    return {
        'results': results,
        'best_variation': best_variation[0],
        'best_time_ms': best_variation[1]['execution_time_ms']
    }


def get_database_index_suggestions(model_class, common_queries):
    """
    Suggest database indexes based on common query patterns.
    
    Args:
        model_class: Django model class
        common_queries: List of common query patterns
        
    Returns:
        list: List of index suggestions
    """
    suggestions = []
    
    for query_pattern in common_queries:
        if 'filter' in query_pattern:
            # Extract field names from filter patterns
            fields = []
            if 'region' in query_pattern:
                fields.append('region')
            if 'is_deleted' in query_pattern:
                fields.append('is_deleted')
            if 'created_at' in query_pattern:
                fields.append('created_at')
            if 'change_type' in query_pattern:
                fields.append('change_type')
            
            if fields:
                suggestions.append({
                    'fields': fields,
                    'description': f"Composite index for: {', '.join(fields)}",
                    'query_pattern': query_pattern
                })
    
    return suggestions


# Performance monitoring decorator
def monitor_performance(threshold_ms=100):
    """
    Decorator to monitor function performance.
    
    Args:
        threshold_ms: Threshold in milliseconds for slow operations
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time_ms = (time.time() - start_time) * 1000
                
                if execution_time_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation detected: {func.__name__} took {execution_time_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                
                return result
                
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Error in {func.__name__} after {execution_time_ms:.2f}ms: {e}"
                )
                raise
        
        return wrapper
    return decorator
