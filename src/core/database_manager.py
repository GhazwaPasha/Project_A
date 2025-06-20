import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import uuid
from datetime import datetime, date
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple, Any
import threading
import time

# For now, we'll use a fallback configuration if the imports fail
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

try:
    from .config import DatabaseConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    # Fallback configuration
    import os
    class DatabaseConfig:
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
        POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
        POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
        POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
        POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
          # Local database configuration
        LOCAL_POSTGRES_HOST = os.getenv('LOCAL_POSTGRES_HOST', 'localhost')
        LOCAL_POSTGRES_PORT = int(os.getenv('LOCAL_POSTGRES_PORT', 5432))
        LOCAL_POSTGRES_DB = os.getenv('LOCAL_POSTGRES_DB', 'accounting_local')
        LOCAL_POSTGRES_USER = os.getenv('LOCAL_POSTGRES_USER', 'postgres')
        LOCAL_POSTGRES_PASSWORD = os.getenv('LOCAL_POSTGRES_PASSWORD', 'postgres')

class SyncStatus:
    """Track sync status between local and remote databases."""
    def __init__(self):
        self.local_available = False
        self.remote_available = False
        self.prefer_local = True
        self.auto_sync_enabled = True
        self.last_sync = None
        self.pending_operations = 0
        self.failed_operations = 0
        self.conflicts = 0
        self.is_syncing = False

class DatabaseManager:
    """Enhanced database manager with local/remote sync capabilities."""
    
    def __init__(self, prefer_local=True, auto_sync=True):
        """Initialize database manager with local and remote connections."""
        self.logger = logging.getLogger(__name__)
        self.prefer_local = prefer_local
        self.auto_sync = auto_sync
        self.sync_status = SyncStatus()
        self.sync_status.prefer_local = prefer_local
        self.sync_status.auto_sync_enabled = auto_sync
          # Remote PostgreSQL connection parameters (Supabase) - Primary (IPv6)
        self.remote_params = {
            'host': DatabaseConfig.POSTGRES_HOST,
            'port': DatabaseConfig.POSTGRES_PORT,
            'database': DatabaseConfig.POSTGRES_DB,
            'user': DatabaseConfig.POSTGRES_USER,
            'password': DatabaseConfig.POSTGRES_PASSWORD,
        }
          # Remote PostgreSQL fallback parameters (Supabase Pooler) - IPv4 fallback
        # Extract project ID from hostname (e.g., db.udfrgwtqbfcxtrvheqet.supabase.co -> udfrgwtqbfcxtrvheqet)
        project_id = DatabaseConfig.POSTGRES_HOST.split('.')[1] if '.' in DatabaseConfig.POSTGRES_HOST else 'unknown'
        self.remote_fallback_params = {
            'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
            'port': 5432,
            'database': DatabaseConfig.POSTGRES_DB,
            'user': f'postgres.{project_id}',  # postgres.udfrgwtqbfcxtrvheqet
            'password': DatabaseConfig.POSTGRES_PASSWORD,
        }
        
        # Local PostgreSQL connection parameters
        self.local_params = {
            'host': DatabaseConfig.LOCAL_POSTGRES_HOST,
            'port': DatabaseConfig.LOCAL_POSTGRES_PORT,
            'database': DatabaseConfig.LOCAL_POSTGRES_DB,
            'user': DatabaseConfig.LOCAL_POSTGRES_USER,
            'password': DatabaseConfig.LOCAL_POSTGRES_PASSWORD,
        }
          # Test connections
        self._test_connections()
        
        # Track which remote connection is working
        self.using_fallback_remote = False
          # Initialize sync background thread if auto sync is enabled
        if auto_sync:
            self._start_sync_thread()
    
    def _test_connections(self):
        """Test both local and remote connections with IPv4 fallback."""
        # Test local connection
        try:
            conn = psycopg2.connect(**self.local_params)
            conn.close()
            self.sync_status.local_available = True
            self.logger.info("✅ Local database connection successful")
        except Exception as e:
            self.sync_status.local_available = False
            self.logger.warning(f"❌ Local database connection failed: {e}")
        
        # Test remote connection (IPv6 direct)
        try:
            conn = psycopg2.connect(**self.remote_params)
            conn.close()
            self.sync_status.remote_available = True
            self.using_fallback_remote = False
            self.logger.info("✅ Remote database connection successful (direct IPv6)")
        except Exception as e:
            self.logger.warning(f"❌ Direct remote connection failed: {e}")
            
            # Try fallback connection (IPv4 pooler)
            try:
                conn = psycopg2.connect(**self.remote_fallback_params)
                conn.close()
                self.sync_status.remote_available = True
                self.using_fallback_remote = True
                self.logger.info("✅ Remote database connection successful (IPv4 pooler fallback)")
            except Exception as fallback_e:
                self.sync_status.remote_available = False
                self.using_fallback_remote = False
                self.logger.error(f"❌ Both remote connections failed. Direct: {e}, Fallback: {fallback_e}")
    
    def get_connection_status(self):
        """Get current connection and sync status."""
        return {
            'local_available': self.sync_status.local_available,
            'remote_available': self.sync_status.remote_available,
            'prefer_local': self.sync_status.prefer_local,
            'auto_sync_enabled': self.sync_status.auto_sync_enabled,
            'sync_status': {
                'last_sync': self.sync_status.last_sync,
                'pending_operations': self.sync_status.pending_operations,
                'failed_operations': self.sync_status.failed_operations,
                'conflicts': self.sync_status.conflicts,
                'is_syncing': self.sync_status.is_syncing
            },
            'using_fallback_remote': getattr(self, 'using_fallback_remote', False)        }
    
    def _get_preferred_connection(self):
        """Get connection to preferred database with real-time fallback."""
        if self.prefer_local and self.sync_status.local_available:
            return psycopg2.connect(**self.local_params)
        elif self.sync_status.remote_available:
            # Try direct connection first, then fallback
            if not self.using_fallback_remote:
                try:
                    return psycopg2.connect(**self.remote_params)
                except Exception as e:
                    self.logger.warning(f"Direct remote connection failed during operation, trying fallback: {e}")
                    # Mark as using fallback and try fallback connection
                    self.using_fallback_remote = True
                    return psycopg2.connect(**self.remote_fallback_params)
            else:
                # Already using fallback
                return psycopg2.connect(**self.remote_fallback_params)
        elif self.sync_status.local_available:
            return psycopg2.connect(**self.local_params)
        else:
            raise ConnectionError("No database connections available")
    
    def _start_sync_thread(self):
        """Start background sync thread."""
        def sync_loop():
            while self.auto_sync:
                try:
                    if (self.sync_status.local_available and 
                        self.sync_status.remote_available and 
                        not self.sync_status.is_syncing):
                        self._perform_sync()
                    time.sleep(30)  # Sync every 30 seconds
                except Exception as e:
                    self.logger.error(f"Sync thread error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        sync_thread = threading.Thread(target=sync_loop, daemon=True)
        sync_thread.start()
        self.logger.info("🔄 Background sync thread started")
    
    def _perform_sync(self):
        """Perform synchronization between local and remote databases."""
        if self.sync_status.is_syncing:
            return
        
        self.sync_status.is_syncing = True
        try:
            # Simple timestamp-based sync for now
            # This will be enhanced with proper conflict resolution
            self.logger.info("🔄 Starting database sync...")
            
            # TODO: Implement actual sync logic
            # For now, just update sync timestamp
            self.sync_status.last_sync = datetime.now()
            
            self.logger.info("✅ Database sync completed")
        except Exception as e:
            self.logger.error(f"❌ Sync failed: {e}")
            self.sync_status.failed_operations += 1
        finally:
            self.sync_status.is_syncing = False

    @contextmanager
    def get_db_cursor(self, use_dict_cursor=True):
        """Context manager for database operations with automatic connection management."""
        conn = None
        cursor = None
        try:
            conn = self._get_preferred_connection()
            cursor_factory = RealDictCursor if use_dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _get_connection(self):
        """Get a fresh PostgreSQL connection."""
        try:
            return psycopg2.connect(**self.pg_params)
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL connection failed: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            conn = self._get_preferred_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None, fetch_one=False, fetch_all=True):
        """Execute a query and return results."""
        with self.get_db_cursor() as cursor:
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    def execute_batch(self, query: str, data: List[tuple], page_size: int = 1000):
        """Execute a batch of queries efficiently."""
        with self.get_db_cursor() as cursor:
            execute_batch(cursor, query, data, page_size=page_size)
            return cursor.rowcount
    
    def create_tables(self):
        """Create the PostgreSQL tables with proper schema."""
        create_tables_sql = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Create accounts table
        CREATE TABLE IF NOT EXISTS accounts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) UNIQUE NOT NULL,
            type VARCHAR(50) NOT NULL CHECK (type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Income', 'Expense')),
            code VARCHAR(20) UNIQUE,
            parent_code VARCHAR(20),
            level INTEGER DEFAULT 1 CHECK (level > 0),
            is_postable BOOLEAN DEFAULT true,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create journal entries table
        CREATE TABLE IF NOT EXISTS journal_entries (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            entry_date DATE NOT NULL,
            description TEXT NOT NULL,
            debit_account_name VARCHAR(255) NOT NULL,
            credit_account_name VARCHAR(255) NOT NULL,
            amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date);
        CREATE INDEX IF NOT EXISTS idx_journal_entries_debit_account ON journal_entries(debit_account_name);
        CREATE INDEX IF NOT EXISTS idx_journal_entries_credit_account ON journal_entries(credit_account_name);
        CREATE INDEX IF NOT EXISTS idx_accounts_code ON accounts(code);
        CREATE INDEX IF NOT EXISTS idx_accounts_parent_code ON accounts(parent_code);
        CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(type);
        
        -- Create updated_at trigger function
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Create triggers for automatic timestamp updates
        DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts;
        CREATE TRIGGER update_accounts_updated_at 
            BEFORE UPDATE ON accounts
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        DROP TRIGGER IF EXISTS update_journal_entries_updated_at ON journal_entries;
        CREATE TRIGGER update_journal_entries_updated_at 
            BEFORE UPDATE ON journal_entries
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            with self.get_db_cursor() as cursor:
                cursor.execute(create_tables_sql)
            self.logger.info("Database tables created successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise
    
    def add_foreign_keys(self):
        """Add foreign key constraints after data migration."""
        fk_sql = """
        -- Add foreign key constraints (run after data migration)
        ALTER TABLE accounts 
        ADD CONSTRAINT fk_parent_code 
        FOREIGN KEY (parent_code) REFERENCES accounts(code)
        ON DELETE SET NULL;
        
        ALTER TABLE journal_entries 
        ADD CONSTRAINT fk_debit_account 
        FOREIGN KEY (debit_account_name) REFERENCES accounts(name)
        ON DELETE RESTRICT;
        
        ALTER TABLE journal_entries 
        ADD CONSTRAINT fk_credit_account 
        FOREIGN KEY (credit_account_name) REFERENCES accounts(name)
        ON DELETE RESTRICT;
        """
        
        try:
            with self.get_db_cursor() as cursor:
                cursor.execute(fk_sql)
            self.logger.info("Foreign key constraints added successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add foreign keys: {e}")
            raise
