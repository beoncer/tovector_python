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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from .utils import create_teaser_preview, vectorize_image
import traceback
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

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
            # For Facebook login, use sub as unique identifier if email is not available
            if 'email' in user_info:
                user_identifier = user_info['email']
            else:
                user_identifier = user_info['sub']  # Facebook user ID

            try:
                user = User.objects.get(email=user_identifier)
                created = False
                print(f"\nFound existing user: {user.email}")
            except User.DoesNotExist:
                print("\nCreating new user...")
                # Generate a unique username from the name or sub
                base_username = user_info.get('nickname', user_info['sub']).lower().replace(' ', '_')
                username = base_username
                counter = 1
                
                # Keep trying until we find a unique username
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                print(f"Generated username: {username}")
                
                try:
                    # Create new user with Auth0 data
                    user = User.objects.create_user(
                        username=username,
                        email=user_identifier,  # Use sub as email for Facebook users
                        first_name=user_info.get('given_name', ''),
                        last_name=user_info.get('family_name', ''),
                        is_active=True
                    )
                    created = True
                    
                    # Set initial credits for new users
                    user.credits = settings.INITIAL_FREE_CREDITS
                    user.save()
                    
                    print(f"\nSuccessfully created new user: {user.email}")
                except Exception as e:
                    print(f"\nError creating user: {str(e)}")
                    raise

            try:
                # Clear any existing session first
                request.session.flush()
                
                # Login user
                login(request, user)
                print("\nSuccessfully logged in user")
                
                # Set session expiry to browser close
                request.session.set_expiry(0)
                
                # Store tokens in session
                request.session['access_token'] = token_data['access_token']
                request.session['id_token'] = token_data['id_token']
                request.session['auth_time'] = int(time.time())
                print("\nSuccessfully stored tokens in session")
                
                # If this is a new user, initialize their credits
                if created:
                    user.credits = settings.INITIAL_FREE_CREDITS
                    user.save()
                    print("\nInitialized credits for new user")
                
                return redirect('core:dashboard')
                
            except Exception as e:
                print(f"\nError during login/session setup: {str(e)}")
                raise

        except requests.exceptions.RequestException as e:
            print(f"\nRequest Error: {e}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return render(request, 'core/error.html', {
                'error': 'Failed to authenticate. Please ensure your Auth0 configuration is correct.'
            })
        except Exception as e:
            print(f"\nError in Auth0 callback: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return render(request, 'core/error.html', {
                'error': 'An unexpected error occurred during authentication'
            })

@require_http_methods(['POST'])
def upload(request):
    """Handle initial file upload and return preview cost information."""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        image = request.FILES['image']
        
        # Validate file type
        if not image.content_type.startswith('image/'):
            return JsonResponse({'error': 'Invalid file type. Please upload an image.'}, status=400)
        
        # Validate file size (30MB limit)
        if image.size > 30 * 1024 * 1024:
            return JsonResponse({'error': 'File size exceeds 30MB limit.'}, status=400)
        
        # For logged-out users, return teaser preview
        if not request.user.is_authenticated:
            try:
                preview_result = create_teaser_preview(image)
                if 'error' in preview_result:
                    return JsonResponse({'error': preview_result['error']}, status=400)
                
                return JsonResponse({
                    'success': True,
                    'preview_data': preview_result['preview_data'],
                    'requires_login': True,
                    'login_url': reverse('core:login'),
                    'signup_url': reverse('core:signup')
                })
            except Exception as e:
                print(f"Error creating teaser preview: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return JsonResponse({'error': 'Error processing image'}, status=500)
        
        # For logged-in users, store the image temporarily and return preview cost information
        try:
            # Ensure the temp directory exists
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate a unique filename
            ext = os.path.splitext(image.name)[1]
            temp_filename = f"temp/{uuid.uuid4()}{ext}"
            
            # Save the file temporarily
            try:
                path = default_storage.save(temp_filename, ContentFile(image.read()))
                print(f"Saved temporary file to: {path}")
            except Exception as e:
                print(f"Error saving temporary file: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return JsonResponse({'error': 'Error saving uploaded file'}, status=500)
            
            # Calculate preview cost
            preview_cost = 0 if request.user.free_previews_remaining > 0 else 0.2
            
            # Create a temporary preview
            try:
                # Reset file pointer before creating preview
                image.seek(0)
                preview_result = create_teaser_preview(image)
                if 'error' in preview_result:
                    # Clean up the temporary file
                    default_storage.delete(path)
                    return JsonResponse({'error': preview_result['error']}, status=400)
            except Exception as e:
                print(f"Error creating preview: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                # Clean up the temporary file
                default_storage.delete(path)
                return JsonResponse({'error': 'Error creating preview'}, status=500)
            
            return JsonResponse({
                'success': True,
                'preview_data': preview_result['preview_data'],
                'requires_login': False,
                'preview_cost': preview_cost,
                'credits_balance': float(request.user.credits),
                'free_previews': request.user.free_previews_remaining,
                'temp_file_path': path  # Store the path for later use
            })
        except Exception as e:
            print(f"Error processing image for logged-in user: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': 'Error processing image'}, status=500)
            
    except Exception as e:
        print(f"Unexpected error in upload view: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook handler for Stripe events.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    stripe.api_key = settings.STRIPE_SECRET_KEY

    print("\nReceived Stripe webhook:")
    print(f"Signature: {sig_header}")
    print(f"Payload: {payload.decode('utf-8')}")

    try:
        # Verify webhook signature and extract event
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        print(f"\nVerified webhook signature for event: {event.type}")
    except ValueError as e:
        print(f"\nInvalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"\nInvalid signature: {str(e)}")
        return HttpResponse(status=400)

    # Handle specific event types
    if event.type == 'checkout.session.completed':
        session = event.data.object
        print(f"\nProcessing checkout.session.completed event:")
        print(f"Session ID: {session.id}")
        print(f"Payment Intent: {session.payment_intent}")
        print(f"Metadata: {session.metadata}")
        
        try:
            # Get user and credit pack from metadata
            user_id = session.metadata.get('user_id')
            credit_pack_id = session.metadata.get('credit_pack_id')
            
            print(f"\nLooking up user {user_id} and credit pack {credit_pack_id}")
            
            user = User.objects.get(id=user_id)
            credit_pack = CreditPack.objects.get(id=credit_pack_id)
            
            print(f"Found user: {user.email}")
            print(f"Found credit pack: {credit_pack.name}")
            
            # Create transaction record
            transaction = Transaction.objects.create(
                user=user,
                transaction_type='PURCHASE',
                credit_pack=credit_pack,
                credits_amount=credit_pack.credits,
                amount_paid=credit_pack.price,
                status='COMPLETED',
                stripe_payment_id=session.payment_intent
            )
            print(f"Created transaction: {transaction.id}")
            
            # Add credits and free previews to user's account
            user.credits += Decimal(str(credit_pack.credits))
            user.free_previews_remaining += credit_pack.free_previews
            user.save()
            
            print(f"Updated user credits: {user.credits}")
            print(f"Updated free previews: {user.free_previews_remaining}")
            
        except (User.DoesNotExist, CreditPack.DoesNotExist, Exception) as e:
            print(f"\nError processing webhook: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
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
        
        # Check if user's email is actually an Auth0 sub ID (for Facebook logins)
        user_email = request.user.email
        if '|' in user_email:  # This indicates it's an Auth0 sub ID
            # Create a placeholder email using the sub ID
            sub_id = user_email.split('|')[1]
            user_email = f'facebook_{sub_id}@placeholder.com'
        
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
            customer_email=user_email,
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

@login_required
def checkout_success(request):
    """Handle successful checkout."""
    print("\nCheckout Success View:")
    print(f"User: {request.user.email}")
    print(f"Current credits: {request.user.credits}")
    
    # Get the latest transaction for this user
    latest_transaction = Transaction.objects.filter(
        user=request.user,
        transaction_type='PURCHASE'
    ).order_by('-created_at').first()
    
    if latest_transaction:
        print(f"Latest transaction: {latest_transaction.id}")
        print(f"Transaction status: {latest_transaction.status}")
        print(f"Credits amount: {latest_transaction.credits_amount}")
        print(f"Credit pack: {latest_transaction.credit_pack.name}")
        
        # Check if credits were actually added
        if latest_transaction.status == 'COMPLETED':
            print("Transaction is completed, checking credit update...")
            # Refresh user from database to get latest state
            request.user.refresh_from_db()
            print(f"Updated credits: {request.user.credits}")
            
            return render(request, 'core/checkout_success.html', {
                'transaction': latest_transaction,
                'credits_added': latest_transaction.credits_amount,
                'new_balance': request.user.credits,
                'credit_pack': latest_transaction.credit_pack
            })
        else:
            print("Transaction is not completed yet")
            return render(request, 'core/checkout_success.html', {
                'transaction': latest_transaction,
                'status': 'pending'
            })
    else:
        print("No recent transactions found")
        return render(request, 'core/checkout_success.html', {
            'status': 'no_transaction'
        })

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
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file."
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Set font
        p.setFont("Helvetica-Bold", 24)
        
        # Draw the logo text (since we're using a text-based logo for now)
        p.drawString(1*inch, 10*inch, "ToVector.ai")
        
        # Add invoice details
        p.setFont("Helvetica-Bold", 16)
        p.drawString(1*inch, 9*inch, f"INVOICE #{transaction.invoice_number}")
        
        # Add date
        p.setFont("Helvetica", 12)
        p.drawString(1*inch, 8.5*inch, f"Date: {transaction.created_at.strftime('%Y-%m-%d')}")
        
        # Add billing information
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, 7.5*inch, "BILLING INFORMATION")
        p.setFont("Helvetica", 12)
        p.drawString(1*inch, 7*inch, f"Customer: {request.user.get_full_name() or request.user.email}")
        p.drawString(1*inch, 6.7*inch, f"Company: {request.user.company_name or 'N/A'}")
        p.drawString(1*inch, 6.4*inch, f"VAT ID: {request.user.vat_id or 'N/A'}")
        
        # Handle multi-line billing address
        billing_address = request.user.billing_address or 'N/A'
        y_position = 6.1
        for line in billing_address.split('\n'):
            p.drawString(1*inch, y_position*inch, f"Billing Address: {line}")
            y_position -= 0.3
        
        # Add transaction details
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1*inch, 5*inch, "TRANSACTION DETAILS")
        p.setFont("Helvetica", 12)
        p.drawString(1*inch, 4.5*inch, f"Transaction Type: {transaction.transaction_type}")
        p.drawString(1*inch, 4.2*inch, f"Credits: {transaction.credits_amount}")
        p.drawString(1*inch, 3.9*inch, f"Amount: ${transaction.amount_paid:.2f} USD")
        p.drawString(1*inch, 3.6*inch, f"Status: {transaction.status}")
        p.drawString(1*inch, 3.3*inch, f"Payment ID: {transaction.stripe_payment_id}")
        
        # Add footer
        p.setFont("Helvetica", 10)
        p.drawString(1*inch, 1*inch, "ToVector.ai - Making vectorization simple")
        p.drawString(1*inch, 0.75*inch, "Contact: support@tovector.ai")
        
        # Draw horizontal lines
        p.setStrokeColor(colors.black)
        p.line(1*inch, 7.7*inch, 7.5*inch, 7.7*inch)  # Below "BILLING INFORMATION"
        p.line(1*inch, 5.2*inch, 7.5*inch, 5.2*inch)  # Below "TRANSACTION DETAILS"
        
        # Close the PDF object cleanly
        p.showPage()
        p.save()
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create the HTTP response with PDF content
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.invoice_number}.pdf"'
        response.write(pdf)
        
        return response
        
    except Transaction.DoesNotExist:
        return render(request, 'core/error.html', {
            'error': 'Invoice not found'
        })

@require_http_methods(['POST'])
def vectorize(request):
    """Process the image and return vectorization results."""
    try:
        # Check for either direct file upload or temporary file path
        if 'image' not in request.FILES and 'temp_file_path' not in request.POST:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        # Get the image either from uploaded files or temporary storage
        if 'image' in request.FILES:
            image = request.FILES['image']
        else:
            temp_path = request.POST['temp_file_path']
            try:
                if not default_storage.exists(temp_path):
                    return JsonResponse({'error': 'Temporary file not found'}, status=400)
                image = default_storage.open(temp_path)
            except Exception as e:
                print(f"Error accessing temporary file: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return JsonResponse({'error': 'Error accessing uploaded file'}, status=500)
        
        # Validate file type
        if not image.content_type.startswith('image/'):
            return JsonResponse({'error': 'Invalid file type. Please upload an image.'}, status=400)
        
        # Validate file size (30MB limit)
        if image.size > 30 * 1024 * 1024:
            return JsonResponse({'error': 'File size exceeds 30MB limit.'}, status=400)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required',
                'requires_login': True,
                'login_url': reverse('core:login'),
                'signup_url': reverse('core:signup')
            }, status=401)
        
        # Check credits based on action
        action = request.POST.get('action', 'vectorize')
        cost = 0.2 if action == 'preview' else 1.0
        
        if request.user.free_previews_remaining > 0 and action == 'preview':
            cost = 0
        elif float(request.user.credits) < cost:
            return JsonResponse({
                'error': 'Insufficient credits',
                'required_credits': cost,
                'current_credits': float(request.user.credits)
            }, status=402)
        
        try:
            # Process the image
            result = vectorize_image(image)
            if 'error' in result:
                return JsonResponse({'error': result['error']}, status=400)
            
            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                amount=cost,
                transaction_type='preview' if action == 'preview' else 'vectorize'
            )
            
            # Update user credits and free previews
            request.user.credits -= cost
            if action == 'preview' and request.user.free_previews_remaining > 0:
                request.user.free_previews_remaining -= 1
            request.user.save()
            
            # Create vectorization record
            Vectorization.objects.create(
                user=request.user,
                original_image=image.name,
                vector_data=result['vector_data'],
                preview_data=result['preview_data'],
                cost=cost
            )
            
            # Clean up temporary file if it exists
            if 'temp_file_path' in request.POST:
                try:
                    default_storage.delete(request.POST['temp_file_path'])
                except Exception as e:
                    print(f"Error deleting temporary file: {str(e)}")
                    # Don't fail the request if cleanup fails
            
            return JsonResponse({
                'success': True,
                'vector_data': result['vector_data'],
                'preview_data': result['preview_data'],
                'credits_balance': float(request.user.credits),
                'free_previews': request.user.free_previews_remaining
            })
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': 'Error processing image'}, status=500)
            
    except Exception as e:
        print(f"Unexpected error in vectorize view: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
