from .settings import *
import os
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

# Print Auth0 settings for debugging
print("\nAuth0 Settings (Development):")
print(f"Domain: {os.getenv('AUTH0_DOMAIN')}")
print(f"Client ID: {os.getenv('AUTH0_CLIENT_ID')}")
print(f"Callback URL: {os.getenv('AUTH0_CALLBACK_URL')}\n") 