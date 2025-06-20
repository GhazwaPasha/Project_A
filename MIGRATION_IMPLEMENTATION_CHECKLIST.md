# PostgreSQL Migration Implementation Checklist

## Pre-Migration Tasks

### [ ] 1. Environment Setup
- [ ] Create Supabase project at https://supabase.com
- [ ] Configure PostgreSQL database in Supabase
- [ ] Obtain connection credentials and API keys
- [ ] Set up development environment with new dependencies

### [ ] 2. Backup Current System
- [ ] Export all SQLite data using existing tools
- [ ] Create full database backup
- [ ] Document current system state

## Code Changes Required

### [ ] 3. Database Connection Layer (`src/core/database_manager.py`)

```python
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from supabase import create_client, Client
from typing import List, Dict, Optional, Tuple, Any
import uuid
from datetime import datetime, date
import logging
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Centralized database management with PostgreSQL and Supabase."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase configuration. Check environment variables.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self._pg_conn = None
        
        # PostgreSQL connection params
        self.pg_params = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
        }
        
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_db_cursor(self, use_dict_cursor=True):
        """Context manager for database operations."""
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
        return psycopg2.connect(**self.pg_params)
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_db_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
```

### [ ] 4. Updated AccountingSystem Class (`src/core/accounting_system.py`)

**Key methods that need updating:**

#### [ ] 4.1 Connection Management
```python
class AccountingSystem:
    def __init__(self, db_config=None):
        """Initialize with PostgreSQL database manager."""
        self.db_manager = DatabaseManager()
        self._test_connection()
        self._ensure_tables_exist()
    
    def _test_connection(self):
        """Test database connection on startup."""
        if not self.db_manager.test_connection():
            raise ConnectionError("Failed to connect to PostgreSQL database")
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist."""
        with self.db_manager.get_db_cursor() as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('accounts', 'journal_entries')
            """)
            existing_tables = {row['table_name'] for row in cursor.fetchall()}
            
            if 'accounts' not in existing_tables or 'journal_entries' not in existing_tables:
                self._create_tables()
```

#### [ ] 4.2 Account Resolution (Updated)
```python
def resolve_account(self, account_input):
    """Resolve account with PostgreSQL-optimized queries."""
    if not account_input:
        return None, None, None
    
    search_term = account_input.lower().strip()
    
    with self.db_manager.get_db_cursor() as cursor:
        # Exact match first
        cursor.execute("""
            SELECT name, type, code 
            FROM accounts 
            WHERE (LOWER(name) = %s OR code = %s) AND is_postable = true
        """, (search_term, account_input))
        
        result = cursor.fetchone()
        if result:
            return result['name'], result['type'], result['code']
        
        # Fuzzy matching with PostgreSQL features
        cursor.execute("""
            SELECT name, type, code,
                   similarity(LOWER(name), %s) as sim_score
            FROM accounts 
            WHERE is_postable = true
            AND (
                LOWER(name) ILIKE %s OR 
                LOWER(name) ILIKE %s OR
                code ILIKE %s
            )
            ORDER BY sim_score DESC, length(name)
            LIMIT 1
        """, (search_term, f"{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
        result = cursor.fetchone()
        if result:
            return result['name'], result['type'], result['code']
            
    return None, None, None
```

#### [ ] 4.3 Journal Entry Operations
```python
def add_journal_entry(self, date, description, debit_account, credit_account, amount):
    """Add journal entry with proper PostgreSQL types."""
    # Resolve accounts
    debit_name, debit_type, debit_code = self.resolve_account(debit_account)
    credit_name, credit_type, credit_code = self.resolve_account(credit_account)
    
    if not debit_name or not credit_name:
        raise ValueError("Invalid account names provided")
    
    # Convert date string to date object if needed
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    
    with self.db_manager.get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO journal_entries 
            (entry_date, description, debit_account_name, credit_account_name, amount)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (date, description, debit_name, credit_name, float(amount)))
        
        result = cursor.fetchone()
        return str(result['id'])

def get_ledger(self, account_name, from_date=None, to_date=None):
    """Get ledger with optimized PostgreSQL query."""
    with self.db_manager.get_db_cursor() as cursor:
        query = """
            SELECT entry_date, description, debit_account_name, credit_account_name, amount
            FROM journal_entries
            WHERE (debit_account_name = %s OR credit_account_name = %s)
        """
        params = [account_name, account_name]
        
        if from_date and to_date:
            query += " AND entry_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
        
        query += " ORDER BY entry_date, created_at"
        
        cursor.execute(query, params)
        return cursor.fetchall()
```

#### [ ] 4.4 Trial Balance with PostgreSQL Features
```python
def get_trial_balance(self, from_date=None, to_date=None):
    """Enhanced trial balance using PostgreSQL window functions."""
    with self.db_manager.get_db_cursor() as cursor:
        query = """
        WITH account_balances AS (
            SELECT 
                a.name,
                a.type,
                a.code,
                COALESCE(SUM(
                    CASE 
                        WHEN je.debit_account_name = a.name THEN
                            CASE 
                                WHEN a.type IN ('Asset', 'Expense') THEN je.amount
                                ELSE -je.amount
                            END
                        WHEN je.credit_account_name = a.name THEN
                            CASE 
                                WHEN a.type IN ('Asset', 'Expense') THEN -je.amount
                                ELSE je.amount
                            END
                        ELSE 0
                    END
                ), 0) as balance
            FROM accounts a
            LEFT JOIN journal_entries je ON (
                je.debit_account_name = a.name OR je.credit_account_name = a.name
            )
        """
        
        params = []
        if from_date and to_date:
            query += " AND je.entry_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
        
        query += """
            GROUP BY a.name, a.type, a.code
            ORDER BY a.code
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to dictionary format expected by UI
        return {row['name']: float(row['balance']) for row in results}
```

### [ ] 5. Batch Operations Optimization
```python
def add_journal_entries_batch(self, entries):
    """Optimized batch insert using PostgreSQL execute_batch."""
    with self.db_manager.get_db_cursor() as cursor:
        insert_data = []
        for entry in entries:
            # Validate and resolve accounts
            debit_name, _, _ = self.resolve_account(entry['debit_account'])
            credit_name, _, _ = self.resolve_account(entry['credit_account'])
            
            if not debit_name or not credit_name:
                continue
            
            insert_data.append((
                entry['date'],
                entry['description'],
                debit_name,
                credit_name,
                float(entry['amount'])
            ))
        
        if insert_data:
            execute_batch(
                cursor,
                """
                INSERT INTO journal_entries 
                (entry_date, description, debit_account_name, credit_account_name, amount)
                VALUES (%s, %s, %s, %s, %s)
                """,
                insert_data,
                page_size=1000
            )
        
        return len(insert_data)
```

### [ ] 6. Configuration Files

#### [ ] 6.1 Environment Configuration (`.env`)
```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# PostgreSQL Direct Connection
POSTGRES_HOST=db.your-project-id.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
```

#### [ ] 6.2 Updated Requirements (`requirements.txt`)
```
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
PyQt6-sip==13.6.0
openai==1.12.0
requests==2.31.0
pandas>=2.0.0
psycopg2-binary>=2.9.9
supabase>=2.3.0
python-dotenv>=1.0.0
```

### [ ] 7. Data Migration Script (`tools/migrate_to_postgresql.py`)
```python
#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL/Supabase
"""
import sqlite3
import sys
import os
from datetime import datetime
import csv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.database_manager import DatabaseManager

def export_sqlite_data():
    """Export data from SQLite to CSV files."""
    sqlite_path = 'accounting.db'
    if not os.path.exists(sqlite_path):
        print(f"SQLite database {sqlite_path} not found!")
        return False
    
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Export accounts
    print("Exporting accounts...")
    cursor.execute("SELECT name, type, code, parent_code, level, is_postable, description FROM accounts")
    accounts = cursor.fetchall()
    
    with open('accounts_export.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'type', 'code', 'parent_code', 'level', 'is_postable', 'description'])
        writer.writerows(accounts)
    
    # Export journal entries
    print("Exporting journal entries...")
    cursor.execute("SELECT date, description, debit_account, credit_account, amount FROM journal_entries ORDER BY date")
    entries = cursor.fetchall()
    
    with open('journal_entries_export.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'description', 'debit_account', 'credit_account', 'amount'])
        writer.writerows(entries)
    
    conn.close()
    print(f"Exported {len(accounts)} accounts and {len(entries)} journal entries")
    return True

def import_to_postgresql():
    """Import data to PostgreSQL."""
    db_manager = DatabaseManager()
    
    if not db_manager.test_connection():
        print("Failed to connect to PostgreSQL!")
        return False
    
    print("Importing accounts...")
    with open('accounts_export.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        accounts_imported = 0
        
        for row in reader:
            try:
                with db_manager.get_db_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO accounts (name, type, code, parent_code, level, is_postable, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO NOTHING
                    """, (
                        row['name'], row['type'], row['code'] or None, 
                        row['parent_code'] or None, int(row['level']), 
                        bool(int(row['is_postable'])), row['description']
                    ))
                accounts_imported += 1
            except Exception as e:
                print(f"Error importing account {row['name']}: {e}")
    
    print(f"Imported {accounts_imported} accounts")
    
    print("Importing journal entries...")
    with open('journal_entries_export.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        entries_imported = 0
        
        for row in reader:
            try:
                with db_manager.get_db_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO journal_entries (entry_date, description, debit_account_name, credit_account_name, amount)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        row['date'], row['description'], 
                        row['debit_account'], row['credit_account'], 
                        float(row['amount'])
                    ))
                entries_imported += 1
            except Exception as e:
                print(f"Error importing journal entry: {e}")
    
    print(f"Imported {entries_imported} journal entries")
    return True

if __name__ == "__main__":
    print("Starting migration from SQLite to PostgreSQL...")
    
    if export_sqlite_data():
        if import_to_postgresql():
            print("Migration completed successfully!")
        else:
            print("Migration failed during import phase")
    else:
        print("Migration failed during export phase")
```

## Testing Checklist

### [ ] 8. Unit Tests
- [ ] Test database connection and configuration
- [ ] Test account resolution and fuzzy matching
- [ ] Test journal entry CRUD operations
- [ ] Test trial balance calculations
- [ ] Test batch operations

### [ ] 9. Integration Tests
- [ ] Test complete workflows (add account → add entries → generate reports)
- [ ] Test data migration accuracy
- [ ] Test performance with larger datasets

### [ ] 10. UI Testing
- [ ] Verify all forms work with new database layer
- [ ] Test error handling and user feedback
- [ ] Test report generation and export functions

## Deployment Checklist

### [ ] 11. Production Setup
- [ ] Set up production Supabase project
- [ ] Configure production environment variables
- [ ] Set up database backups and monitoring
- [ ] Test production deployment

### [ ] 12. Rollback Plan
- [ ] Document rollback procedures
- [ ] Keep SQLite backups accessible
- [ ] Test rollback process in staging environment

## Post-Migration Tasks

### [ ] 13. Performance Monitoring
- [ ] Monitor query performance
- [ ] Track application response times  
- [ ] Monitor database resource usage

### [ ] 14. Documentation Updates
- [ ] Update installation instructions
- [ ] Update configuration documentation
- [ ] Create troubleshooting guide

This checklist ensures a systematic approach to the PostgreSQL migration with minimal risk and maximum reliability.
