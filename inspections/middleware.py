"""
Middleware for logging API requests
"""
import time
import traceback
from django.utils.deprecation import MiddlewareMixin


class APIRequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming API requests and responses
    """
    
    def process_request(self, request):
        """Log incoming request"""
        # Only log API requests (not static files, admin, etc.)
        if self._should_log_request(request):
            request._start_time = time.time()
            
            user_info = "Anonymous"
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"User: {request.user.username} (ID: {request.user.id})"
            
            method = request.method
            path = request.get_full_path()
            ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
            query_params = dict(request.GET.items())
            
            # Check for authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            auth_present = "Yes" if auth_header else "No"
            auth_type = auth_header.split(' ')[0] if auth_header and ' ' in auth_header else "None"
            
            print(
                f"[MIDDLEWARE REQUEST] {method} {path} | "
                f"{user_info} | "
                f"IP: {ip_address} | "
                f"Auth: {auth_present} ({auth_type}) | "
                f"Query: {query_params}"
            )
        
        return None
    
    def process_response(self, request, response):
        """Log response after request is processed"""
        if self._should_log_request(request) and hasattr(request, '_start_time'):
            duration_ms = (time.time() - request._start_time) * 1000
            status_code = response.status_code
            
            method = request.method
            path = request.get_full_path()
            
            user_info = "Anonymous"
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"User: {request.user.username}"
            
            print(
                f"[MIDDLEWARE RESPONSE] {method} {path} | "
                f"{user_info} | "
                f"Status: {status_code} | "
                f"Duration: {duration_ms:.2f}ms"
            )
            
            # Log 4xx and 5xx errors more prominently
            if status_code >= 400:
                print(
                    f"[MIDDLEWARE ERROR] {method} {path} | "
                    f"Status: {status_code} | "
                    f"User: {user_info}"
                )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing"""
        if self._should_log_request(request):
            method = request.method
            path = request.get_full_path()
            user_info = "Anonymous"
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"User: {request.user.username} (ID: {request.user.id})"
            
            print(
                f"[MIDDLEWARE EXCEPTION] {method} {path} | "
                f"{user_info} | "
                f"Exception: {type(exception).__name__}: {str(exception)}"
            )
            print(f"[MIDDLEWARE TRACEBACK]\n{traceback.format_exc()}")
        
        return None
    
    def _should_log_request(self, request):
        """Determine if this request should be logged"""
        path = request.path
        
        # Don't log:
        # - Static files
        # - Media files
        # - Admin interface
        # - Health checks
        exclude_patterns = [
            '/static/',
            '/media/',
            '/admin/',
            '/health/',
            '/favicon.ico',
            '/__debug__/',
        ]
        
        # Only log API endpoints and inspections URLs
        include_patterns = [
            '/api/',
            '/inspections/',
            '/auth/',
        ]
        
        # Check if it should be excluded
        if any(exclude in path for exclude in exclude_patterns):
            return False
        
        # Check if it should be included
        if any(include in path for include in include_patterns):
            return True
        
        return False

