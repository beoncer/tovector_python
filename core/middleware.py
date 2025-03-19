from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
import time

class Auth0Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Public paths that don't require authentication
        public_paths = [
            '/login/',
            '/signup/',
            '/callback/',
            '/logout/',
            '/',
            '/how-it-works/',
            '/pricing/',
            '/support/',
            '/faq/',
            '/static/',
            '/favicon.ico',
            '/webhook/stripe/',
        ]

        # Check if the path is public
        if any(request.path.startswith(path) for path in public_paths):
            return self.get_response(request)

        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Clear any existing session
            request.session.flush()
            return redirect('core:login')

        # Verify session is valid
        if not self._is_session_valid(request):
            # Clear invalid session
            request.session.flush()
            return redirect('core:login')

        response = self.get_response(request)
        return response

    def _is_session_valid(self, request):
        """Check if the current session is valid."""
        # Check if we have the necessary tokens
        if not all(key in request.session for key in ['access_token', 'id_token', 'auth_time']):
            return False

        # Check session age (24 hours)
        session_age = time.time() - request.session.get('auth_time', 0)
        if session_age > 86400:  # 24 hours in seconds
            return False

        return True 