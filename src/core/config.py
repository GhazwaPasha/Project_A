import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Database configuration class for PostgreSQL and Supabase."""
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Direct PostgreSQL connection (for advanced operations)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
      # Local PostgreSQL database configuration
    LOCAL_POSTGRES_HOST = os.getenv('LOCAL_POSTGRES_HOST', 'localhost')
    LOCAL_POSTGRES_PORT = int(os.getenv('LOCAL_POSTGRES_PORT', 5432))
    LOCAL_POSTGRES_DB = os.getenv('LOCAL_POSTGRES_DB', 'accounting_local')
    LOCAL_POSTGRES_USER = os.getenv('LOCAL_POSTGRES_USER', 'postgres')
    LOCAL_POSTGRES_PASSWORD = os.getenv('LOCAL_POSTGRES_PASSWORD', 'postgres')
    
    # Application Settings
    APP_ENV = os.getenv('APP_ENV', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present."""
        required_vars = [
            'SUPABASE_URL', 'SUPABASE_ANON_KEY', 'POSTGRES_HOST',
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD'
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
