import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Vectorizer.ai API credentials
VECTORIZER_API_ID = 'vky26ievrqbhpxl'  # Your API ID
VECTORIZER_API_SECRET = '1ed3s7q1na0r1cbviki4v4st6kktkir6buaihas8ls0ef4mfpg2v'  # Your API Secret 