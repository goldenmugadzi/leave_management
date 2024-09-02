from datetime import datetime, timedelta
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

class InactiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            session_key = request.session.session_key
            session = Session.objects.get(session_key=session_key)
            last_activity = session.get_decoded().get('last_activity')
            if last_activity:
                last_activity = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S.%f')
                if (datetime.now() - last_activity).total_seconds() > 3600:  # 10 minutes
                    # Log out the user and store the current page in the session
                    request.session['logout_page'] = request.path
                    logout(request)
                    return HttpResponseRedirect('/accounts/login/?session_expired=True')
            # Update the last activity timestamp
            session.get_decoded()['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            session.save()
        response = self.get_response(request)
        return response