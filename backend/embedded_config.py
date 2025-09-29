"""
Embedded configuration for the accounting application
"""
import os

# Embedded environment variables from .env file
EMBEDDED_CONFIG = {
    'SUPABASE_URL': 'https://udfrgwtqbfcxtrvheqet.supabase.co',
    'SUPABASE_ANON_KEY': '***REMOVED***',
    'SUPABASE_SERVICE_ROLE_KEY': '***REMOVED***',
    'APP_ENV': 'production',
    'LOG_LEVEL': 'INFO',
    'MISTRAL_API_KEY': '***REMOVED***'
}

def setup_embedded_environment():
    """Setup environment variables from embedded config"""
    for key, value in EMBEDDED_CONFIG.items():
        if not os.getenv(key):  # Only set if not already set
            os.environ[key] = value

# Auto-setup when imported
setup_embedded_environment()
