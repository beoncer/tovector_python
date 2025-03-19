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
from .models import CreditPack, User, Transaction
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from decimal import Decimal

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
    """
    View function for the pricing page.
    Displays available credit packs for purchase.
    """
    credit_packs = CreditPack.objects.filter(is_active=True)
    return render(request, 'core/pricing.html', {
        'credit_packs': credit_packs,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
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

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook handler for Stripe events.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        # Verify webhook signature and extract event
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle specific event types
    if event.type == 'checkout.session.completed':
        session = event.data.object
        
        try:
            # Get user and credit pack from metadata
            user_id = session.metadata.get('user_id')
            credit_pack_id = session.metadata.get('credit_pack_id')
            
            user = User.objects.get(id=user_id)
            credit_pack = CreditPack.objects.get(id=credit_pack_id)
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                transaction_type='PURCHASE',
                credit_pack=credit_pack,
                credits_amount=credit_pack.credits,
                amount_paid=credit_pack.price,
                status='COMPLETED',
                stripe_payment_id=session.payment_intent
            )
            
            # Add credits and free previews to user's account
            user.credits += Decimal(str(credit_pack.credits))
            user.free_previews_remaining += credit_pack.free_previews
            user.save()
            
            # Send confirmation email (you can implement this later)
            
        except (User.DoesNotExist, CreditPack.DoesNotExist, Exception) as e:
            # Log the error but return 200 to acknowledge receipt
            print(f"Error processing webhook: {str(e)}")
            return HttpResponse(status=200)

    return HttpResponse(status=200)

@login_required
@require_http_methods(['POST'])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for credit pack purchase.
    """
    try:
        data = json.loads(request.body)
        pack_id = data.get('packId')
        
        if not pack_id:
            return JsonResponse({'error': 'Pack ID is required'}, status=400)
            
        credit_pack = CreditPack.objects.get(id=pack_id, is_active=True)
        
        # Set the Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(credit_pack.price * 100),  # Convert to cents
                    'product_data': {
                        'name': credit_pack.name,
                        'description': f'{credit_pack.credits} credits + {credit_pack.free_previews} free previews',
                    },
                },
                'quantity': 1,
            }],
            metadata={
                'credit_pack_id': str(credit_pack.id),
                'user_id': str(request.user.id),
            },
            mode='payment',
            success_url=request.build_absolute_uri(reverse('core:checkout_success')),
            cancel_url=request.build_absolute_uri(reverse('core:checkout_cancel')),
            customer_email=request.user.email,
        )
        
        return JsonResponse({
            'sessionId': checkout_session.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except CreditPack.DoesNotExist:
        return JsonResponse({'error': 'Credit pack not found'}, status=404)
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")  # Add debug logging
        return JsonResponse({'error': str(e)}, status=400)

def checkout_success(request):
    """
    Handle successful checkout.
    """
    return render(request, 'core/checkout_success.html')

def checkout_cancel(request):
    """
    Handle cancelled checkout.
    """
    return render(request, 'core/checkout_cancel.html')
