from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import CreditPack

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
        auth0_domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        callback_url = settings.AUTH0_CALLBACK_URL
        
        auth_url = f'https://{auth0_domain}/authorize'
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email'
        }
        
        return redirect(f'{auth_url}?{"&".join(f"{k}={v}" for k, v in params.items())}')

class Auth0SignupView(View):
    """Handle Auth0 signup."""
    def get(self, request):
        auth0_domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        callback_url = settings.AUTH0_CALLBACK_URL
        
        auth_url = f'https://{auth0_domain}/authorize'
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email',
            'screen_hint': 'signup'
        }
        
        return redirect(f'{auth_url}?{"&".join(f"{k}={v}" for k, v in params.items())}')

class Auth0CallbackView(View):
    """Handle Auth0 callback."""
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return redirect('home')
            
        # TODO: Implement Auth0 token exchange and user creation/login
        return redirect('dashboard')

@method_decorator(require_http_methods(['POST']), name='dispatch')
class UploadImageView(View):
    """Handle image uploads."""
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
            
        # TODO: Implement image upload and vectorization
        return JsonResponse({'message': 'Upload endpoint'})
