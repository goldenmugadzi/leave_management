from datetime import datetime, timedelta
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.conf import settings

class InactiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get the session timeout from settings (default 30 minutes)
            session_timeout = getattr(settings, 'SESSION_COOKIE_AGE', 1800)  # 1800 seconds = 30 minutes
            
            try:
                # Get last activity from session
                last_activity = request.session.get('last_activity')
                
                if last_activity:
                    # Parse the datetime string
                    if isinstance(last_activity, str):
                        last_activity = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S.%f')
                    
                    # Check if session has expired based on inactivity
                    if (datetime.now() - last_activity).total_seconds() > session_timeout:
                        # Store the current page before logout
                        request.session['logout_page'] = request.path
                        logout(request)
                        return HttpResponseRedirect('/accounts/login/?session_expired=True')
                
                # Update the last activity timestamp in session
                request.session['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                request.session.modified = True  # Ensure session is saved
                
            except Exception as e:
                # If there's any error with session handling, just update last activity
                request.session['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                request.session.modified = True
        
        response = self.get_response(request)
        return response