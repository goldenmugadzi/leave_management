# your_app/middleware.py
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

User = get_user_model()

class LimitConcurrentSessionsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
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