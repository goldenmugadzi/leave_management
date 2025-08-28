"""
Logging and monitoring utilities for dashboard enhancement feature.
Provides structured logging for data operations, performance monitoring, and user actions.
"""

import logging
import time
import json
from functools import wraps
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from typing import Dict, Any, Optional


# Configure dashboard-specific logger
dashboard_logger = logging.getLogger('dashboard_enhancement')


class DashboardLogger:
    """Centralized logging utility for dashboard operations"""
    
    @staticmethod
    def log_data_update(user: User, table: str, operation: str, data: Dict[str, Any], 
                       success: bool = True, error: str = None, execution_time: float = None):
        """
        Log data update operations with structured information
        
        Args:
            user: User performing the operation
            table: Table/model being updated
            operation: Type of operation (create, update, delete)
            data: Data being modified
            success: Whether operation succeeded
            error: Error message if operation failed
            execution_time: Time taken for operation in seconds
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'table': table,
            'operation': operation,
            'success': success,
            'execution_time_seconds': execution_time,
            'data': DashboardLogger._sanitize_data(data)
        }
        
        if error:
            log_data['error'] = str(error)
        
        if success:
            dashboard_logger.info(f"Data update successful", extra=log_data)
        else:
            dashboard_logger.error(f"Data update failed: {error}", extra=log_data)
    
    @staticmethod
    def log_validation_error(user: User, table: str, field: str, value: Any, 
                           error_message: str, validation_rules: Dict[str, Any] = None):
        """
        Log validation errors with detailed context
        
        Args:
            user: User who triggered validation
            table: Table/model being validated
            field: Field that failed validation
            value: Value that failed validation
            error_message: Validation error message
            validation_rules: Rules that were applied
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'table': table,
            'field': field,
            'attempted_value': DashboardLogger._sanitize_value(value),
            'error_message': error_message,
            'validation_rules': validation_rules or {}
        }
        
        dashboard_logger.warning(f"Validation error in {table}.{field}", extra=log_data)
    
    @staticmethod
    def log_user_action(user: User, action: str, details: Dict[str, Any] = None, 
                       ip_address: str = None, user_agent: str = None):
        """
        Log user actions for audit trail
        
        Args:
            user: User performing the action
            action: Description of action performed
            details: Additional action details
            ip_address: User's IP address
            user_agent: User's browser/client info
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'action': action,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details or {}
        }
        
        dashboard_logger.info(f"User action: {action}", extra=log_data)
    
    @staticmethod
    def log_permission_check(user: User, resource: str, permission: str, 
                           granted: bool, reason: str = None):
        """
        Log permission checks for security monitoring
        
        Args:
            user: User requesting access
            resource: Resource being accessed
            permission: Permission being checked
            granted: Whether permission was granted
            reason: Reason for grant/denial
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'resource': resource,
            'permission': permission,
            'granted': granted,
            'reason': reason
        }
        
        level = logging.INFO if granted else logging.WARNING
        message = f"Permission {'granted' if granted else 'denied'} for {resource}"
        dashboard_logger.log(level, message, extra=log_data)
    
    @staticmethod
    def log_performance_metric(endpoint: str, method: str, execution_time: float,
                             query_count: int = None, cache_hits: int = None,
                             user: User = None, status_code: int = None):
        """
        Log performance metrics for API endpoints
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            execution_time: Total execution time in seconds
            query_count: Number of database queries
            cache_hits: Number of cache hits
            user: User making the request
            status_code: HTTP response status code
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'execution_time_seconds': execution_time,
            'query_count': query_count,
            'cache_hits': cache_hits,
            'user_id': user.id if user else None,
            'status_code': status_code
        }
        
        # Determine log level based on performance
        if execution_time > 5.0:  # Slow requests
            level = logging.WARNING
            message = f"Slow API response: {endpoint} took {execution_time:.2f}s"
        elif execution_time > 2.0:
            level = logging.INFO
            message = f"API response: {endpoint} took {execution_time:.2f}s"
        else:
            level = logging.DEBUG
            message = f"API response: {endpoint} took {execution_time:.2f}s"
        
        dashboard_logger.log(level, message, extra=log_data)
    
    @staticmethod
    def log_auto_calculation(table: str, record_id: Any, calculation_type: str,
                           input_values: Dict[str, Any], result: Any, user: User = None):
        """
        Log automatic calculations (e.g., revenue lost totals, percentage adjustments)
        
        Args:
            table: Table where calculation occurred
            record_id: ID of the record
            calculation_type: Type of calculation performed
            input_values: Values used in calculation
            result: Calculated result
            user: User who triggered the calculation
        """
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'table': table,
            'record_id': str(record_id),
            'calculation_type': calculation_type,
            'input_values': DashboardLogger._sanitize_data(input_values),
            'result': DashboardLogger._sanitize_value(result),
            'user_id': user.id if user else None
        }
        
        dashboard_logger.info(f"Auto-calculation: {calculation_type} in {table}", extra=log_data)
    
    @staticmethod
    def _sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for logging (convert Decimal, datetime, etc.)"""
        if not isinstance(data, dict):
            return DashboardLogger._sanitize_value(data)
        
        sanitized = {}
        for key, value in data.items():
            sanitized[key] = DashboardLogger._sanitize_value(value)
        return sanitized
    
    @staticmethod
    def _sanitize_value(value: Any) -> Any:
        """Sanitize individual values for JSON serialization"""
        if isinstance(value, Decimal):
            return float(value)
        elif hasattr(value, 'isoformat'):  # datetime objects
            return value.isoformat()
        elif hasattr(value, '__dict__'):  # Model instances
            return str(value)
        else:
            return value


def log_api_performance(endpoint_name: str = None):
    """
    Decorator to automatically log API endpoint performance
    
    Args:
        endpoint_name: Custom name for the endpoint (defaults to function name)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            method = getattr(request, 'method', 'UNKNOWN')
            user = getattr(request, 'user', None)
            
            try:
                # Execute the view function
                response = func(request, *args, **kwargs)
                execution_time = time.time() - start_time
                status_code = getattr(response, 'status_code', None)
                
                # Log successful execution
                DashboardLogger.log_performance_metric(
                    endpoint=endpoint,
                    method=method,
                    execution_time=execution_time,
                    user=user,
                    status_code=status_code
                )
                
                return response
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log failed execution
                DashboardLogger.log_performance_metric(
                    endpoint=endpoint,
                    method=method,
                    execution_time=execution_time,
                    user=user,
                    status_code=500
                )
                
                # Log the error details
                dashboard_logger.error(
                    f"API endpoint error: {endpoint}",
                    extra={
                        'endpoint': endpoint,
                        'method': method,
                        'error': str(e),
                        'user_id': user.id if user and hasattr(user, 'id') else None,
                        'execution_time_seconds': execution_time
                    }
                )
                
                raise  # Re-raise the exception
        
        return wrapper
    return decorator


def log_data_operation(operation_type: str):
    """
    Decorator to automatically log data operations
    
    Args:
        operation_type: Type of operation (create, update, delete, etc.)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Try to extract user from args (typically request.user)
            user = None
            for arg in args:
                if hasattr(arg, 'user'):
                    user = arg.user
                    break
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful operation
                DashboardLogger.log_data_update(
                    user=user,
                    table=func.__name__,
                    operation=operation_type,
                    data={'function': func.__name__, 'args_count': len(args)},
                    success=True,
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log failed operation
                DashboardLogger.log_data_update(
                    user=user,
                    table=func.__name__,
                    operation=operation_type,
                    data={'function': func.__name__, 'args_count': len(args)},
                    success=False,
                    error=str(e),
                    execution_time=execution_time
                )
                
                raise  # Re-raise the exception
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Context manager for monitoring performance of code blocks"""
    
    def __init__(self, operation_name: str, user: User = None, 
                 log_threshold: float = 1.0):
        """
        Initialize performance monitor
        
        Args:
            operation_name: Name of the operation being monitored
            user: User performing the operation
            log_threshold: Minimum execution time (seconds) to log
        """
        self.operation_name = operation_name
        self.user = user
        self.log_threshold = log_threshold
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        
        if execution_time >= self.log_threshold:
            if exc_type is None:
                # Successful execution
                dashboard_logger.info(
                    f"Performance: {self.operation_name} completed in {execution_time:.3f}s",
                    extra={
                        'operation': self.operation_name,
                        'execution_time_seconds': execution_time,
                        'user_id': self.user.id if self.user else None,
                        'success': True
                    }
                )
            else:
                # Failed execution
                dashboard_logger.warning(
                    f"Performance: {self.operation_name} failed after {execution_time:.3f}s",
                    extra={
                        'operation': self.operation_name,
                        'execution_time_seconds': execution_time,
                        'user_id': self.user.id if self.user else None,
                        'success': False,
                        'error': str(exc_val)
                    }
                )