"""
Shared Database Manager
Manages a single Supabase client instance to prevent connection leaks and improve performance.
"""

import logging
from typing import Optional, Any
import threading
from .config import DatabaseConfig

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class SharedDatabaseManager:
    """Singleton database manager with connection pooling."""
    
    _instance = None
    _lock = threading.Lock()
    _shared_client = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger(__name__)
            self._initialized = True
            self._connection_count = 0
    
    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Get the shared Supabase client instance."""
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        if cls._shared_client is None:
            with cls._lock:
                if cls._shared_client is None:
                    try:
                        # Validate configuration
                        DatabaseConfig.validate_config()
                        
                        # Create shared client
                        cls._shared_client = create_client(
                            DatabaseConfig.SUPABASE_URL,
                            DatabaseConfig.SUPABASE_ANON_KEY
                        )
                        
                        logging.getLogger(__name__).info("✅ Shared Supabase client created")
                    except Exception as e:
                        logging.getLogger(__name__).error(f"❌ Failed to create shared Supabase client: {e}")
                        raise
        
        # Track connection usage
        instance = cls()
        instance._connection_count += 1
        
        return cls._shared_client
    
    @classmethod
    def close_client(cls):
        """Close the shared Supabase client."""
        if cls._shared_client:
            with cls._lock:
                if cls._shared_client:
                    try:
                        # Note: Supabase client doesn't have a close method in Python SDK
                        # But we can clear the reference to allow garbage collection
                        cls._shared_client = None
                        logging.getLogger(__name__).info("✅ Shared Supabase client closed")
                    except Exception as e:
                        logging.getLogger(__name__).error(f"❌ Error closing shared Supabase client: {e}")
    
    @classmethod
    def get_connection_count(cls) -> int:
        """Get the current connection usage count."""
        instance = cls()
        return instance._connection_count
    
    @classmethod
    def reset_connection_count(cls):
        """Reset the connection usage count."""
        instance = cls()
        instance._connection_count = 0


# Convenience function for easy access
def get_shared_client():
    """Get the shared Supabase client instance."""
    return SharedDatabaseManager.get_client()


def close_shared_client():
    """Close the shared Supabase client."""
    SharedDatabaseManager.close_client() 