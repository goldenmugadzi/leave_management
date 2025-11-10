"""
Custom decorators for inspections app
Includes rate limiting decorators for API endpoints
"""

from functools import wraps
from django_ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework import status


def rate_limit_download(func):
    """
    Rate limit decorator for download endpoints
    Limit: 100 requests per minute per user
    """
    @wraps(func)
    @ratelimit(key='user', rate='100/m', method='GET', block=False)
    def wrapped(request, *args, **kwargs):
        # Check if rate limit was exceeded
        if getattr(request, 'limited', False):
            return Response(
                {
                    'success': False,
                    'error': {
                        'message': 'Rate limit exceeded. Please try again later.',
                        'code': 'RATE_LIMIT_EXCEEDED'
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        return func(request, *args, **kwargs)
    return wrapped


def rate_limit_upload(func):
    """
    Rate limit decorator for upload endpoints
    Limit: 50 requests per minute per user
    """
    @wraps(func)
    @ratelimit(key='user', rate='50/m', method='POST', block=False)
    def wrapped(request, *args, **kwargs):
        # Check if rate limit was exceeded
        if getattr(request, 'limited', False):
            return Response(
                {
                    'success': False,
                    'error': {
                        'message': 'Rate limit exceeded. Please try again later.',
                        'code': 'RATE_LIMIT_EXCEEDED'
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        return func(request, *args, **kwargs)
    return wrapped

