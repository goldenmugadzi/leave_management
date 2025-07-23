# your_app/middleware.py
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class LimitConcurrentSessionsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                # Get all sessions for the user
                user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
                user_sessions = [session for session in user_sessions if str(request.user.id) == session.get_decoded().get('_auth_user_id')]

                # Define the session limit
                session_limit = getattr(settings, 'SESSION_LIMIT', 1)

                # If the number of sessions exceeds the limit, delete the oldest sessions
                if len(user_sessions) > session_limit:
                    user_sessions.sort(key=lambda session: session.expire_date)
                    for session in user_sessions[:-session_limit]:
                        session.delete()
            except Exception as e:
                # Log the error but don't disrupt the user experience
                logger.error(f"Error in LimitConcurrentSessionsMiddleware: {e}")
                
class SessionErrorSessionMiddleware(SessionMiddleware):
    def process_response(self, request, response):
        try:
            return super().process_response(request, response)
        except Exception as e:
            # Log the error for debugging
            logger.error(f"Session error: {e}")
            
            # Only redirect to login for specific session-related errors
            # Don't redirect for every exception as this causes login loops
            if 'session' in str(e).lower() or 'corrupt' in str(e).lower():
                # Clear the corrupted session
                try:
                    request.session.flush()
                except:
                    pass
                return HttpResponseRedirect(reverse('login'))
            
            # For other errors, try to continue normally
            return response