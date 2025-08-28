"""
Performance monitoring utilities for dashboard enhancement feature.
Tracks API performance, database query counts, and system metrics.
"""

import time
import logging
from collections import defaultdict, deque
from threading import Lock
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# Performance monitoring logger
performance_logger = logging.getLogger('dashboard_performance')


class PerformanceTracker:
    """Thread-safe performance metrics tracker"""
    
    def __init__(self, max_history: int = 1000):
        self._metrics = defaultdict(lambda: {
            'response_times': deque(maxlen=max_history),
            'query_counts': deque(maxlen=max_history),
            'error_counts': 0,
            'total_requests': 0,
            'last_request': None
        })
        self._lock = Lock()
    
    def record_request(self, endpoint: str, response_time: float, 
                      query_count: int = None, success: bool = True):
        """Record a request's performance metrics"""
        with self._lock:
            metrics = self._metrics[endpoint]
            metrics['response_times'].append(response_time)
            if query_count is not None:
                metrics['query_counts'].append(query_count)
            metrics['total_requests'] += 1
            metrics['last_request'] = timezone.now()
            
            if not success:
                metrics['error_counts'] += 1
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get performance statistics for a specific endpoint"""
        with self._lock:
            metrics = self._metrics[endpoint]
            response_times = list(metrics['response_times'])
            query_counts = list(metrics['query_counts'])
            
            if not response_times:
                return {
                    'endpoint': endpoint,
                    'total_requests': 0,
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'error_rate': 0,
                    'avg_query_count': 0
                }
            
            return {
                'endpoint': endpoint,
                'total_requests': metrics['total_requests'],
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'error_rate': metrics['error_counts'] / metrics['total_requests'] * 100,
                'avg_query_count': sum(query_counts) / len(query_counts) if query_counts else 0,
                'last_request': metrics['last_request']
            }
    
    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get performance statistics for all endpoints"""
        with self._lock:
            return [
                self.get_endpoint_stats(endpoint) 
                for endpoint in self._metrics.keys()
            ]
    
    def get_slow_endpoints(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Get endpoints with average response time above threshold"""
        all_stats = self.get_all_stats()
        return [
            stats for stats in all_stats 
            if stats['avg_response_time'] > threshold
        ]
    
    def reset_metrics(self, endpoint: str = None):
        """Reset metrics for a specific endpoint or all endpoints"""
        with self._lock:
            if endpoint:
                if endpoint in self._metrics:
                    del self._metrics[endpoint]
            else:
                self._metrics.clear()


# Global performance tracker instance
performance_tracker = PerformanceTracker()


class DatabaseQueryMonitor:
    """Monitor database query performance"""
    
    @staticmethod
    def get_query_count():
        """Get current query count from Django connection"""
        return len(connection.queries)
    
    @staticmethod
    def log_slow_queries(threshold_ms: float = 100):
        """Log queries that exceed the threshold"""
        for query in connection.queries:
            time_ms = float(query['time']) * 1000
            if time_ms > threshold_ms:
                performance_logger.warning(
                    f"Slow database query detected: {time_ms:.2f}ms",
                    extra={
                        'query_time_ms': time_ms,
                        'sql': query['sql'][:500],  # Truncate long queries
                        'threshold_ms': threshold_ms
                    }
                )
    
    @staticmethod
    def analyze_query_patterns():
        """Analyze query patterns for optimization opportunities"""
        queries = connection.queries
        if not queries:
            return {}
        
        # Group queries by type
        query_types = defaultdict(list)
        for query in queries:
            sql = query['sql'].strip().upper()
            if sql.startswith('SELECT'):
                query_types['SELECT'].append(float(query['time']))
            elif sql.startswith('INSERT'):
                query_types['INSERT'].append(float(query['time']))
            elif sql.startswith('UPDATE'):
                query_types['UPDATE'].append(float(query['time']))
            elif sql.startswith('DELETE'):
                query_types['DELETE'].append(float(query['time']))
        
        # Calculate statistics
        analysis = {}
        for query_type, times in query_types.items():
            analysis[query_type] = {
                'count': len(times),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'min_time': min(times)
            }
        
        return analysis


class SystemMetricsCollector:
    """Collect system-level metrics"""
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage (if psutil is available)"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info()._asdict()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    @staticmethod
    def get_cpu_usage():
        """Get current CPU usage (if psutil is available)"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count': psutil.cpu_count()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    @staticmethod
    def log_system_metrics():
        """Log current system metrics"""
        memory_info = SystemMetricsCollector.get_memory_usage()
        cpu_info = SystemMetricsCollector.get_cpu_usage()
        
        performance_logger.info(
            "System metrics snapshot",
            extra={
                'memory_usage': memory_info,
                'cpu_usage': cpu_info,
                'timestamp': timezone.now().isoformat()
            }
        )


class AlertManager:
    """Manage performance alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            'response_time': 5.0,  # seconds
            'error_rate': 10.0,    # percentage
            'query_count': 50,     # queries per request
            'memory_usage': 80.0   # percentage
        }
        self.alert_cooldown = timedelta(minutes=5)
        self.last_alerts = {}
    
    def check_performance_alerts(self):
        """Check for performance issues and send alerts"""
        current_time = timezone.now()
        
        # Check endpoint performance
        slow_endpoints = performance_tracker.get_slow_endpoints(
            self.alert_thresholds['response_time']
        )
        
        for endpoint_stats in slow_endpoints:
            alert_key = f"slow_endpoint_{endpoint_stats['endpoint']}"
            
            if self._should_send_alert(alert_key, current_time):
                self._send_performance_alert(
                    alert_type="slow_endpoint",
                    message=f"Endpoint {endpoint_stats['endpoint']} is slow",
                    details=endpoint_stats
                )
                self.last_alerts[alert_key] = current_time
        
        # Check error rates
        for endpoint_stats in performance_tracker.get_all_stats():
            if endpoint_stats['error_rate'] > self.alert_thresholds['error_rate']:
                alert_key = f"high_error_rate_{endpoint_stats['endpoint']}"
                
                if self._should_send_alert(alert_key, current_time):
                    self._send_performance_alert(
                        alert_type="high_error_rate",
                        message=f"High error rate for {endpoint_stats['endpoint']}",
                        details=endpoint_stats
                    )
                    self.last_alerts[alert_key] = current_time
    
    def _should_send_alert(self, alert_key: str, current_time: datetime) -> bool:
        """Check if enough time has passed since last alert"""
        last_alert = self.last_alerts.get(alert_key)
        if not last_alert:
            return True
        return current_time - last_alert > self.alert_cooldown
    
    def _send_performance_alert(self, alert_type: str, message: str, details: Dict):
        """Send performance alert (log for now, could be extended to email/Slack)"""
        performance_logger.error(
            f"PERFORMANCE ALERT: {message}",
            extra={
                'alert_type': alert_type,
                'details': details,
                'timestamp': timezone.now().isoformat()
            }
        )


# Global alert manager instance
alert_manager = AlertManager()


def log_performance_summary():
    """Log a summary of performance metrics"""
    stats = performance_tracker.get_all_stats()
    
    if not stats:
        performance_logger.info("No performance data available")
        return
    
    # Calculate overall statistics
    total_requests = sum(s['total_requests'] for s in stats)
    avg_response_time = sum(s['avg_response_time'] * s['total_requests'] for s in stats) / total_requests if total_requests > 0 else 0
    avg_error_rate = sum(s['error_rate'] * s['total_requests'] for s in stats) / total_requests if total_requests > 0 else 0
    
    performance_logger.info(
        "Performance summary",
        extra={
            'total_endpoints': len(stats),
            'total_requests': total_requests,
            'overall_avg_response_time': avg_response_time,
            'overall_error_rate': avg_error_rate,
            'endpoint_stats': stats,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # Check for alerts
    alert_manager.check_performance_alerts()


def monitor_dashboard_health():
    """Comprehensive dashboard health check"""
    health_data = {
        'timestamp': timezone.now().isoformat(),
        'performance_stats': performance_tracker.get_all_stats(),
        'slow_endpoints': performance_tracker.get_slow_endpoints(),
        'query_analysis': DatabaseQueryMonitor.analyze_query_patterns(),
        'system_metrics': {
            'memory': SystemMetricsCollector.get_memory_usage(),
            'cpu': SystemMetricsCollector.get_cpu_usage()
        }
    }
    
    performance_logger.info(
        "Dashboard health check",
        extra=health_data
    )
    
    return health_data