import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Database configuration class for Supabase-only backend."""
    
    # Supabase Configuration (only backend we use now)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Application Settings
    APP_ENV = os.getenv('APP_ENV', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # User Roles (matches NEW_SCHEMA.sql)
    USER_ROLES = [
        'super_admin',
        'organization_owner', 
        'accountant',
        'member'
    ]
    
    # Account Types (matches NEW_SCHEMA.sql)
    ACCOUNT_TYPES = [
        'asset',
        'liability',
        'equity',
        'revenue',
        'expense'
    ]
    
    @classmethod
    def validate_config(cls):
        """Validate that all required Supabase configuration is present."""
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
