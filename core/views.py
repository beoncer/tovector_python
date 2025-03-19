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
from .models import CreditPack, User, Transaction, Vectorization
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from decimal import Decimal
import time

def home(request):
    """Homepage view."""
    credit_packs = CreditPack.objects.filter(is_active=True)
    return render(request, 'core/index.html', {
        'credit_packs': credit_packs
    })

@login_required
def dashboard(request):
    """User dashboard view."""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    vectorizations = Vectorization.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'core/dashboard.html', {
        'transactions': transactions,
        'vectorizations': vectorizations,
    })

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
        # Clear any existing session
        request.session.flush()
        logout(request)
        
        # If no connection is specified, show the login page
        if not request.GET.get('connection'):
            return render(request, 'core/login.html', {
                'social_connections': settings.AUTH0_SOCIAL_CONNECTIONS
            })
            
        auth0_domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        callback_url = f'https://{request.get_host()}/callback/'
        
        # Debug print statements
        print("\nAuth0 Login Settings:")
        print(f"Domain: {auth0_domain}")
        print(f"Client ID: {client_id}")
        print(f"Callback URL: {callback_url}")
        print(f"Connection: {request.GET.get('connection')}")
        
        # Build the authorization URL
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email',
            'connection': request.GET.get('connection'),
            'prompt': 'login',  # Force login prompt
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
        callback_url = f'https://{request.get_host()}/callback/'
        
        # Debug print statements
        print("\nAuth0 Signup Settings:")
        print(f"Domain: {auth0_domain}")
        print(f"Client ID: {client_id}")
        print(f"Callback URL: {callback_url}")
        
        # Build the authorization URL with signup hint
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email',
            'screen_hint': 'signup',
            'prompt': 'login'
        }
        
        # Use urlencode to properly encode the parameters
        auth_url = f'https://{auth0_domain}/authorize?{urlencode(params)}'
        
        # Debug print final URL
        print(f"Final Signup URL: {auth_url}")
        
        return redirect(auth_url)

class Auth0LogoutView(View):
    """Handle Auth0 logout."""
    def get(self, request):
        # Clear the Django session
        request.session.flush()
        
        # Clear the user's session
        logout(request)
        
        # Get the domain
        domain = request.get_host()
        
        # Build the return URL - always use HTTPS
        return_to = f'https://{domain}/'
        
        # Build Auth0 logout URL with proper parameters
        params = {
            'client_id': settings.AUTH0_CLIENT_ID,
            'returnTo': return_to,
        }
        
        # Build the Auth0 logout URL with properly encoded parameters
        auth0_logout_url = f'https://{settings.AUTH0_DOMAIN}/v2/logout?{urlencode(params)}'
        
        print("\nAuth0 Logout Settings:")
        print(f"Domain: {settings.AUTH0_DOMAIN}")
        print(f"Client ID: {settings.AUTH0_CLIENT_ID}")
        print(f"Domain: {domain}")
        print(f"Return URL: {return_to}")
        print(f"Logout URL: {auth0_logout_url}")
        
        # Set no-cache headers to prevent browser caching
        response = redirect(auth0_logout_url)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response

class Auth0CallbackView(View):
    """Handle Auth0 callback."""
    def get(self, request):
        code = request.GET.get('code', None)
        if not code:
            return render(request, 'core/error.html', {
                'error': 'No authorization code received'
            })

        try:
            # Get token from Auth0
            token_url = f'https://{settings.AUTH0_DOMAIN}/oauth/token'
            token_payload = {
                'client_id': settings.AUTH0_CLIENT_ID,
                'client_secret': settings.AUTH0_CLIENT_SECRET,
                'code': code,
                'redirect_uri': f'https://{request.get_host()}/callback/',
                'grant_type': 'authorization_code',
            }
            
            # Debug print token request details
            print("\nToken Request Details:")
            print(f"URL: {token_url}")
            print(f"Client ID: {settings.AUTH0_CLIENT_ID}")
            print(f"Redirect URI: {token_payload['redirect_uri']}")
            print(f"Code: {code}")
            
            token_response = requests.post(token_url, json=token_payload)
            
            # Debug print token response
            print("\nToken Response:")
            print(f"Status Code: {token_response.status_code}")
            print(f"Response: {token_response.text}")
            
            if token_response.status_code != 200:
                error_data = token_response.json()
                error_message = error_data.get('error_description', 'Failed to authenticate with Auth0')
                print(f"\nAuth0 Error: {error_message}")
                return render(request, 'core/error.html', {
                    'error': error_message
                })
            
            token_data = token_response.json()

            # Get user info from Auth0
            user_url = f'https://{settings.AUTH0_DOMAIN}/userinfo'
            user_response = requests.get(
                user_url,
                headers={'Authorization': f'Bearer {token_data["access_token"]}'}
            )
            
            if user_response.status_code != 200:
                print(f"\nUser Info Error: {user_response.text}")
                return render(request, 'core/error.html', {
                    'error': 'Failed to get user information'
                })
                
            user_info = user_response.json()
            print(f"\nUser Info: {user_info}")

            # Get or create user
            email = user_info['email']
            try:
                user = User.objects.get(email=email)
                created = False
            except User.DoesNotExist:
                # Generate a unique username from the email
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                
                # Keep trying until we find a unique username
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create the user with the unique username
                user = User.objects.create(
                    username=username,
                    email=email,
                    is_active=True,
                    credits=settings.INITIAL_FREE_CREDITS
                )
                
                # Update user's profile information if available
                if user_info.get('given_name'):
                    user.first_name = user_info['given_name']
                if user_info.get('family_name'):
                    user.last_name = user_info['family_name']
                user.save()
                
                created = True

            # Clear any existing session first
            request.session.flush()
            
            # Login user
            login(request, user)
            
            # Set session expiry to browser close
            request.session.set_expiry(0)
            
            # Store tokens in session
            request.session['access_token'] = token_data['access_token']
            request.session['id_token'] = token_data['id_token']
            request.session['auth_time'] = int(time.time())
            
            # If this is a new user, initialize their credits
            if created:
                user.credits = settings.INITIAL_FREE_CREDITS
                user.save()
            
            return redirect('core:dashboard')

        except requests.exceptions.RequestException as e:
            print(f"\nRequest Error: {e}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return render(request, 'core/error.html', {
                'error': 'Failed to authenticate. Please ensure your Auth0 configuration is correct.'
            })
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            return render(request, 'core/error.html', {
                'error': 'An unexpected error occurred'
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

@login_required
@require_http_methods(['POST'])
def update_account(request):
    """Update user account information."""
    user = request.user
    user.company_name = request.POST.get('company_name', '')
    user.billing_address = request.POST.get('billing_address', '')
    user.vat_id = request.POST.get('vat_id', '')
    user.save()
    
    return JsonResponse({'status': 'success'})

@login_required
def download_invoice(request, transaction_id):
    """Handle invoice downloads for transactions."""
    try:
        # Ensure the transaction belongs to the requesting user
        transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        
        # For now, return a simple text response
        # TODO: Implement proper PDF invoice generation
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="invoice_{transaction_id}.txt"'
        
        # Write invoice content
        content = [
            f"INVOICE #{transaction.id}",
            "=" * 40,
            f"Date: {transaction.created_at.strftime('%Y-%m-%d')}",
            f"Transaction Type: {transaction.transaction_type}",
            f"Credits: {transaction.credits_amount}",
            f"Amount: ${transaction.amount_paid}",
            f"Status: {transaction.status}",
            "=" * 40,
            f"Customer: {request.user.email}",
            f"Company: {request.user.company_name or 'N/A'}",
            f"VAT ID: {request.user.vat_id or 'N/A'}",
            f"Billing Address: {request.user.billing_address or 'N/A'}"
        ]
        
        response.write('\n'.join(content))
        return response
        
    except Transaction.DoesNotExist:
        return render(request, 'core/error.html', {
            'error': 'Invoice not found'
        })
