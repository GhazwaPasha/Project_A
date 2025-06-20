import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import uuid
from datetime import datetime, date
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple, Any

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

class DatabaseManager:
    """Centralized database management with PostgreSQL and optional Supabase integration."""
    
    def __init__(self, use_supabase=True):
        """Initialize database manager with PostgreSQL and optional Supabase."""
        self.logger = logging.getLogger(__name__)
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE
        
        # PostgreSQL connection parameters
        self.pg_params = {
            'host': DatabaseConfig.POSTGRES_HOST,
            'port': DatabaseConfig.POSTGRES_PORT,
            'database': DatabaseConfig.POSTGRES_DB,
            'user': DatabaseConfig.POSTGRES_USER,
            'password': DatabaseConfig.POSTGRES_PASSWORD,
        }
        
        # Initialize Supabase client if available and requested
        self.supabase = None
        if self.use_supabase and DatabaseConfig.SUPABASE_URL and DatabaseConfig.SUPABASE_ANON_KEY:
            try:
                self.supabase = create_client(
                    DatabaseConfig.SUPABASE_URL, 
                    DatabaseConfig.SUPABASE_ANON_KEY
                )
                self.logger.info("Supabase client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Supabase client: {e}")
                self.supabase = None
        
        # Test connection on initialization
        if not self.test_connection():
            raise ConnectionError("Failed to establish database connection")
    
    @contextmanager
    def get_db_cursor(self, use_dict_cursor=True):
        """Context manager for database operations with automatic connection management."""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
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
            with self.get_db_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
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
