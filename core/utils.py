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
    try:
        # Debug: Print settings
        print("DEBUG: Settings check")
        print(f"DEBUG: VECTORIZER_API_ID = '{settings.VECTORIZER_API_ID}'")
        
        # Reset file pointer to beginning
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        # Prepare the API request - using exact format from example
        url = 'https://vectorizer.ai/api/v1/vectorize'
        
        # Set up the request data exactly like the example
        response = requests.post(
            url,
            files={'image': image_file},
            data={
                'mode': 'test_preview' if is_preview else 'test',
            },
            auth=('vky26ievrqbhpxl', '1ed3s7q1na0r1cbviki4v4st6kktkir6buaihas8ls0ef4mfpg2v')
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response headers: {dict(response.headers)}")
        
        if response.status_code == requests.codes.ok:
            vector_data = response.content.decode('utf-8')
            preview_data = f"data:image/svg+xml;base64,{base64.b64encode(response.content).decode('utf-8')}"
            
            return {
                'success': True,
                'vector_data': vector_data,
                'preview_data': preview_data,
                'credits_remaining': float(user.credits),
                'free_previews_remaining': user.free_previews_remaining
            }
        else:
            print(f"DEBUG: Error response content: {response.content.decode('utf-8')}")
            try:
                error_data = response.json()
                print(f"DEBUG: Error data: {error_data}")
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"DEBUG: Error message: {error_message}")
                return {'error': error_message}
            except Exception as e:
                print(f"DEBUG: Error parsing response: {str(e)}")
                return {'error': f"API Error: Status {response.status_code}"}
            
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in vectorize_image: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return {'error': f"Vectorization error: {str(e)}"}

def create_teaser_preview(image_file):
    """Create a blurred preview of the image for logged-out users."""
    try:
        # Open the image using Pillow
        img = Image.open(image_file)
        
        # Check image dimensions
        width, height = img.size
        pixels = width * height
        max_pixels = 3000000  # 3 megapixels limit
        
        if pixels > max_pixels:
            # Calculate new dimensions while maintaining aspect ratio
            ratio = (max_pixels / pixels) ** 0.5
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Apply Gaussian blur
        blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
        
        # Convert to base64
        buffered = BytesIO()
        blurred.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'preview_data': f'data:image/png;base64,{img_str}'
        }
    except Exception as e:
        return {'error': str(e)} 