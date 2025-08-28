"""
Monitoring dashboard views for performance metrics and logging.
Provides endpoints to view performance data and system health.
"""

import json
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from .monitoring import (
    performance_tracker, monitor_dashboard_health, 
    DatabaseQueryMonitor, SystemMetricsCollector
)
from .logging_utils import DashboardLogger, log_api_performance


@login_required
@log_api_performance("monitoring_dashboard")
def monitoring_dashboard(request):
    """Main monitoring dashboard view"""
    # Check if user has permission to view monitoring data
    can_view_monitoring = (
        request.user.is_superuser or 
        request.user.is_staff or
        hasattr(request.user, 'get_user_role_for_application') and
        request.user.get_user_role_for_application("general_dashboards")
    )
    
    if not can_view_monitoring:
        DashboardLogger.log_permission_check(
            user=request.user,
            resource="monitoring_dashboard",
            permission="view",
            granted=False,
            reason="User lacks monitoring permissions"
        )
        return render(request, 'general_dashboards/access_denied.html')
    
    # Log access
    DashboardLogger.log_user_action(
        user=request.user,
        action="view_monitoring_dashboard",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # Get performance data
    performance_stats = performance_tracker.get_all_stats()
    slow_endpoints = performance_tracker.get_slow_endpoints(threshold=2.0)
    health_data = monitor_dashboard_health()
    
    context = {
        'performance_stats': performance_stats,
        'slow_endpoints': slow_endpoints,
        'health_data': health_data,
        'total_endpoints': len(performance_stats),
        'total_requests': sum(s['total_requests'] for s in performance_stats),
        'avg_response_time': (
            sum(s['avg_response_time'] * s['total_requests'] for s in performance_stats) /
            sum(s['total_requests'] for s in performance_stats)
            if sum(s['total_requests'] for s in performance_stats) > 0 else 0
        )
    }
    
    return render(request, 'general_dashboards/monitoring_dashboard.html', context)


@csrf_exempt
@require_http_methods(["GET"])
@log_api_performance("api_performance_stats")
def api_performance_stats(request):
    """API endpoint to get performance statistics"""
    try:
        # Get query parameters
        endpoint = request.GET.get('endpoint')
        include_slow = request.GET.get('include_slow', 'false').lower() == 'true'
        threshold = float(request.GET.get('threshold', 2.0))
        
        if endpoint:
            # Get stats for specific endpoint
            stats = performance_tracker.get_endpoint_stats(endpoint)
            return JsonResponse({
                'success': True,
                'data': stats
            })
        else:
            # Get all stats
            all_stats = performance_tracker.get_all_stats()
            response_data = {
                'success': True,
                'data': {
                    'all_endpoints': all_stats,
                    'summary': {
                        'total_endpoints': len(all_stats),
                        'total_requests': sum(s['total_requests'] for s in all_stats)
                    }
                }
            }
            
            if include_slow:
                response_data['data']['slow_endpoints'] = performance_tracker.get_slow_endpoints(threshold)
            
            return JsonResponse(response_data)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
@log_api_performance("system_health")
def system_health(request):
    """API endpoint to get system health information"""
    try:
        health_data = monitor_dashboard_health()
        
        # Add additional health checks
        health_data['database_queries'] = DatabaseQueryMonitor.analyze_query_patterns()
        health_data['system_resources'] = {
            'memory': SystemMetricsCollector.get_memory_usage(),
            'cpu': SystemMetricsCollector.get_cpu_usage()
        }
        
        return JsonResponse({
            'success': True,
            'data': health_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        })


@csrf_exempt
@require_http_methods(["POST"])
@log_api_performance("reset_performance_metrics")
def reset_performance_metrics(request):
    """API endpoint to reset performance metrics"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        })
    
    # Check permissions
    can_reset = request.user.is_superuser or request.user.is_staff
    
    DashboardLogger.log_permission_check(
        user=request.user,
        resource="performance_metrics_reset",
        permission="admin",
        granted=can_reset,
        reason="Superuser or staff required"
    )
    
    if not can_reset:
        return JsonResponse({
            'success': False,
            'error': 'Insufficient permissions'
        })
    
    try:
        data = json.loads(request.body) if request.body else {}
        endpoint = data.get('endpoint')
        
        # Log the reset action
        DashboardLogger.log_user_action(
            user=request.user,
            action="reset_performance_metrics",
            details={'endpoint': endpoint} if endpoint else {'scope': 'all'},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Reset metrics
        performance_tracker.reset_metrics(endpoint)
        
        return JsonResponse({
            'success': True,
            'message': f'Performance metrics reset for {endpoint or "all endpoints"}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
@log_api_performance("query_performance")
def query_performance(request):
    """API endpoint to get database query performance data"""
    try:
        # Analyze current query patterns
        query_analysis = DatabaseQueryMonitor.analyze_query_patterns()
        
        # Log slow queries
        DatabaseQueryMonitor.log_slow_queries(threshold_ms=100)
        
        return JsonResponse({
            'success': True,
            'data': {
                'query_analysis': query_analysis,
                'total_queries': sum(analysis['count'] for analysis in query_analysis.values()),
                'total_time': sum(analysis['total_time'] for analysis in query_analysis.values()),
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
@log_api_performance("error_logs")
def error_logs(request):
    """API endpoint to get recent error information"""
    try:
        # This would typically read from log files or a logging database
        # For now, return performance data with error information
        
        all_stats = performance_tracker.get_all_stats()
        error_data = []
        
        for stats in all_stats:
            if stats['error_rate'] > 0:
                error_data.append({
                    'endpoint': stats['endpoint'],
                    'error_rate': stats['error_rate'],
                    'total_requests': stats['total_requests'],
                    'error_count': int(stats['error_rate'] * stats['total_requests'] / 100)
                })
        
        return JsonResponse({
            'success': True,
            'data': {
                'endpoints_with_errors': error_data,
                'total_error_count': sum(item['error_count'] for item in error_data),
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
def monitoring_status(request):
    """Simple status endpoint for monitoring system health"""
    try:
        # Basic health check
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': 'healthy',  # Could add actual DB health check
                'logging': 'healthy',
                'performance_tracking': 'healthy'
            }
        }
        
        # Check if there are any critical performance issues
        slow_endpoints = performance_tracker.get_slow_endpoints(threshold=10.0)  # Very slow threshold
        if slow_endpoints:
            health_data['status'] = 'degraded'
            health_data['issues'] = [f"Slow endpoint: {ep['endpoint']}" for ep in slow_endpoints]
        
        return JsonResponse(health_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        })