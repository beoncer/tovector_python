from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import login, logout
from django.core.exceptions import SuspiciousOperation
from urllib.parse import urlencode
import requests
import json
from .models import CreditPack, User

def home(request):
    """Homepage view."""
    credit_packs = CreditPack.objects.filter(is_active=True)
    return render(request, 'core/index.html', {
        'credit_packs': credit_packs
    })

@login_required
def dashboard(request):
    """User dashboard view."""
    return render(request, 'core/dashboard.html')

def pricing(request):
    """Pricing page view."""
    credit_packs = CreditPack.objects.filter(is_active=True)
    return render(request, 'core/pricing.html', {
        'credit_packs': credit_packs
    })

def faq(request):
    """FAQ page view."""
    return render(request, 'core/faq.html')

def support(request):
    """Support page view."""
    return render(request, 'core/support.html')

def how_it_works(request):
    """How it works page view."""
    return render(request, 'core/how-it-works.html')

class Auth0LoginView(View):
    """Handle Auth0 login."""
    def get(self, request):
        # If no connection is specified, show the login page
        if not request.GET.get('connection'):
            return render(request, 'core/login.html', {
                'social_connections': settings.AUTH0_SOCIAL_CONNECTIONS
            })
            
        auth0_domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        callback_url = settings.AUTH0_CALLBACK_URL
        
        # Debug print statements
        print("Auth0 Settings:")
        print(f"Domain: {auth0_domain}")
        print(f"Client ID: {client_id}")
        print(f"Callback URL: {callback_url}")
        
        # Build the authorization URL
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email',
            'connection': request.GET.get('connection'),
        }
        
        # Remove None values from params
        params = {k: v for k, v in params.items() if v is not None}
        
        # Use urlencode to properly encode the parameters
        auth_url = f'https://{auth0_domain}/authorize?{urlencode(params)}'
        
        # Debug print final URL
        print(f"Final Auth URL: {auth_url}")
        
        return redirect(auth_url)

class Auth0SignupView(View):
    """Handle Auth0 signup."""
    def get(self, request):
        auth0_domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        callback_url = settings.AUTH0_CALLBACK_URL
        
        # Build the authorization URL with signup hint
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email',
            'screen_hint': 'signup'
        }
        
        # Use urlencode to properly encode the parameters
        auth_url = f'https://{auth0_domain}/authorize?{urlencode(params)}'
        
        return redirect(auth_url)

class Auth0LogoutView(View):
    """Handle Auth0 logout."""
    def get(self, request):
        # Clear the user's session
        logout(request)
        
        # Redirect to Auth0 logout endpoint
        params = {
            'client_id': settings.AUTH0_CLIENT_ID,
            'returnTo': request.build_absolute_uri('/'),
        }
        return redirect(f'https://{settings.AUTH0_DOMAIN}/v2/logout?{urlencode(params)}')

class Auth0CallbackView(View):
    """Handle Auth0 callback."""
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        if error:
            # Handle authentication error
            return render(request, 'core/auth_error.html', {
                'error': error,
                'error_description': error_description
            })
            
        if not code:
            return redirect('home')
            
        try:
            # Exchange the authorization code for tokens
            token_url = f'https://{settings.AUTH0_DOMAIN}/oauth/token'
            token_payload = {
                'client_id': settings.AUTH0_CLIENT_ID,
                'client_secret': settings.AUTH0_CLIENT_SECRET,
                'code': code,
                'redirect_uri': settings.AUTH0_CALLBACK_URL,
                'grant_type': 'authorization_code'
            }
            
            token_response = requests.post(token_url, json=token_payload)
            token_response.raise_for_status()  # Raise exception for bad status codes
            tokens = token_response.json()
            
            # Get user info from Auth0
            user_url = f'https://{settings.AUTH0_DOMAIN}/userinfo'
            user_response = requests.get(
                user_url,
                headers={'Authorization': f'Bearer {tokens["access_token"]}'}
            )
            user_response.raise_for_status()
            auth0_user = user_response.json()
            
            # Get or create user
            try:
                user = User.objects.get(email=auth0_user['email'])
            except User.DoesNotExist:
                user = User.objects.create(
                    email=auth0_user['email'],
                    username=auth0_user['email'],  # Use email as username
                    first_name=auth0_user.get('given_name', ''),
                    last_name=auth0_user.get('family_name', ''),
                    is_active=True
                )
                # Set unusable password since we're using Auth0
                user.set_unusable_password()
                user.save()
                
                # Initialize with free credits if specified
                if hasattr(settings, 'INITIAL_FREE_CREDITS'):
                    user.credits = settings.INITIAL_FREE_CREDITS
                    user.save()
            
            # Log the user in
            login(request, user)
            return redirect('core:dashboard')
            
        except requests.exceptions.RequestException as e:
            # Handle request errors
            return render(request, 'core/auth_error.html', {
                'error': 'Authentication Error',
                'error_description': str(e)
            })
        except Exception as e:
            # Handle other errors
            return render(request, 'core/auth_error.html', {
                'error': 'System Error',
                'error_description': 'An unexpected error occurred. Please try again.'
            })

@method_decorator(require_http_methods(['POST']), name='dispatch')
class UploadImageView(View):
    """Handle image uploads."""
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
            
        # TODO: Implement image upload and vectorization
        return JsonResponse({'message': 'Upload endpoint'})
