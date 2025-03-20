import os
import requests
from django.conf import settings
from decimal import Decimal
from .models import User, Transaction, Vectorization
from PIL import Image, ImageFilter
from io import BytesIO
import base64

def vectorize_image(user: User, image_file, is_preview: bool = False) -> dict:
    """
    Vectorize an image using the Vectorizer.ai API.
    
    Args:
        user (User): The user requesting vectorization
        image_file: The image file to vectorize
        is_preview (bool): Whether this is a preview request
    
    Returns:
        dict: API response containing the vectorized result
    """
    # Check if user has enough credits
    if not is_preview and user.credits < Decimal('1.0'):
        return {
            'error': 'Insufficient credits',
            'credits_required': 1,
            'credits_available': user.credits
        }
    
    # For preview, check if user has free previews or enough credits
    if is_preview:
        if user.free_previews_remaining > 0:
            preview_cost = 0
        else:
            preview_cost = Decimal('0.2')
            if user.credits < preview_cost:
                return {
                    'error': 'Insufficient credits for preview',
                    'credits_required': preview_cost,
                    'credits_available': user.credits
                }
    
    # Prepare the API request
    url = 'https://vectorizer.ai/api/v1/vectorize'
    auth = (settings.VECTORIZER_API_ID, settings.VECTORIZER_API_SECRET)
    
    # Prepare the files and data
    files = {'image': image_file}
    data = {
        'mode': 'test_preview' if is_preview else 'test',  # Use test mode for development
        'format': 'svg'
    }
    
    try:
        # Make the API request
        response = requests.post(url, auth=auth, files=files, data=data)
        response.raise_for_status()
        
        # Process successful response
        if response.status_code == 200:
            # Create transaction record
            if is_preview:
                if user.free_previews_remaining > 0:
                    user.free_previews_remaining -= 1
                else:
                    user.credits -= preview_cost
                transaction_type = 'PREVIEW'
                credits_used = preview_cost
            else:
                user.credits -= Decimal('1.0')
                transaction_type = 'VECTORIZATION'
                credits_used = Decimal('1.0')
            
            user.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                credits_amount=credits_used,
                status='COMPLETED'
            )
            
            # Create vectorization record
            vectorization = Vectorization.objects.create(
                user=user,
                filename=getattr(image_file, 'name', 'unknown'),
                credits_used=credits_used,
                status='COMPLETED',
                result_url=''  # We'll need to implement file storage for the result
            )
            
            return {
                'success': True,
                'svg_content': response.content,
                'credits_used': credits_used,
                'credits_remaining': user.credits,
                'free_previews_remaining': user.free_previews_remaining,
                'vectorization_id': vectorization.id
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'error': f'API request failed: {str(e)}',
            'status_code': getattr(e.response, 'status_code', None)
        }
    
    return {'error': 'Unknown error occurred'}

def create_teaser_preview(image_file) -> dict:
    """
    Create a blurred preview of the uploaded image for logged-out users.
    
    Args:
        image_file: The uploaded image file
    
    Returns:
        dict: Response containing the blurred preview or error message
    """
    try:
        # Open the image using Pillow
        img = Image.open(image_file)
        
        # Check image dimensions (3MP limit)
        if (img.width * img.height) > (3 * 1000000):  # 3 million pixels
            return {
                'error': 'Image too large. Maximum size is 3 megapixels.',
                'width': img.width,
                'height': img.height
            }
        
        # Resize if the image is too large (preserve aspect ratio)
        max_dimension = 800
        if img.width > max_dimension or img.height > max_dimension:
            ratio = min(max_dimension / img.width, max_dimension / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create a heavily blurred version
        blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
        
        # Add "Login to unlock" text overlay
        # (This is a placeholder - in practice, you'd want to use JS/CSS for the overlay)
        
        # Convert to base64 for sending to frontend
        buffered = BytesIO()
        blurred.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'success': True,
            'preview_data': f'data:image/png;base64,{img_str}',
            'width': img.width,
            'height': img.height
        }
        
    except Exception as e:
        return {
            'error': f'Error processing image: {str(e)}'
        } 