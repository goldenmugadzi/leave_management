from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class TokenRefreshMiddleware:
    """
    Middleware to refresh tokens that are about to expire.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if token is about to expire and refresh it
        if request.user.is_authenticated:
            try:
                token = Token.objects.get(user=request.user)
                # Get token age
                token_age = timezone.now() - token.created
                # If token is more than 23 hours old, refresh it
                if token_age > timedelta(hours=23):
                    token.delete()
                    Token.objects.create(user=request.user)
            except Token.DoesNotExist:
                pass
                
        response = self.get_response(request)
        return response
