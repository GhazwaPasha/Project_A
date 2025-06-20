"""
PostgreSQL-only Accounting System
Clean implementation without SQLite dependencies.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
import logging
from typing import List, Dict, Optional, Tuple, Any

from .database_manager import DatabaseManager

class AccountingSystemPostgreSQL:
    """
    PostgreSQL-only Accounting System with multi-tenant support.
    """
    
    def __init__(self, organization_id=None, user_id=None):
        """Initialize with PostgreSQL and multi-tenant context."""
        self.logger = logging.getLogger(__name__)
        self.organization_id = organization_id
        self.user_id = user_id
        
        # Initialize database manager with organization context
        self.db_manager = DatabaseManager(
            organization_id=organization_id,
            user_id=user_id
        )
        
        # Ensure database is properly set up
        if not self.db_manager.test_connection():
            raise Exception("Failed to connect to PostgreSQL database")
        
        # Ensure tables exist
        self.db_manager.create_tables()
        self.logger.info(f"PostgreSQL Accounting System initialized for org: {organization_id}")
    
    def test_connection(self) -> bool:
        """Test database connection."""
        return self.db_manager.test_connection()
    
    def _ensure_organization_context(self):
        """Ensure organization context is set for operations."""
        if not self.organization_id:
            raise ValueError("Organization context required for multi-tenant operations")
    
    # Account Management
    def create_account(self, name, account_type, code=None, parent_code=None, is_postable=True, description=None):
        """Create a new account with organization context."""
        self._ensure_organization_context()
        
        with self.db_manager.get_db_cursor() as cursor:# Generate code if not provided
            if not code:
                cursor.execute("SELECT COALESCE(MAX(CAST(code AS INTEGER)), 0) + 1 as next_code FROM accounts WHERE code ~ '^[0-9]+$'")
                code = str(cursor.fetchone()['next_code'])
            
            # Calculate level based on parent            level = 1
            if parent_code:
                cursor.execute("SELECT level FROM accounts WHERE code = %s", (parent_code,))
                result = cursor.fetchone()
                if result:
                    level = result['level'] + 1
            
            # Insert account
            cursor.execute("""
                INSERT INTO accounts (name, type, code, parent_code, level, is_postable, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (name, account_type, code, parent_code, level, is_postable, description))
            
            self.logger.info(f"Created account: {name} ({code})")
            return code
    
    def get_all_accounts(self):
        """Get all accounts."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description 
                FROM accounts 
                ORDER BY code NULLS LAST, name
            """)
            return cursor.fetchall()
    
    def get_postable_accounts(self):
        """Get only accounts that can have transactions posted to them."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description 
                FROM accounts 
                WHERE is_postable = TRUE 
                ORDER BY code NULLS LAST, name
            """)
            return cursor.fetchall()
    
    def get_parent_accounts(self, max_level):
        """Get potential parent accounts up to a maximum level."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description 
                FROM accounts 
                WHERE level <= %s 
                ORDER BY level, code NULLS LAST, name
            """, (max_level,))
            return cursor.fetchall()
    
    def get_children_accounts(self, parent_code):
        """Get all child accounts of a given parent."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description 
                FROM accounts 
                WHERE parent_code = %s 
                ORDER BY code NULLS LAST, name
            """, (parent_code,))
            return cursor.fetchall()
    
    def is_account_postable(self, account_name_or_code):
        """Check if an account is postable (can have transactions)."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT is_postable FROM accounts 
                WHERE name = %s OR code = %s
            """, (account_name_or_code, account_name_or_code))
            result = cursor.fetchone()
            return result['is_postable'] if result else False
    
    def get_account_by_name(self, name):
        """Get account details by name."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description 
                FROM accounts 
                WHERE name = %s
            """, (name,))
            return cursor.fetchone()
    
    def get_account_by_code(self, code):
        """Get account details by code."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description 
                FROM accounts 
                WHERE code = %s            """, (code,))
            return cursor.fetchone()
    
    def update_account(self, code, **kwargs):
        """Update an account."""
        if not kwargs:
            return
        with self.db_manager.get_db_cursor() as cursor:
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['name', 'type', 'parent_code', 'is_postable', 'description']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if set_clauses:
                values.append(code)
                query = f"UPDATE accounts SET {', '.join(set_clauses)} WHERE code = %s"
                cursor.execute(query, values)
                self.logger.info(f"Updated account {code}")
                
    def delete_account(self, code):
        """Delete an account (if no transactions exist)."""
        with self.db_manager.get_db_cursor() as cursor:
            # Check for existing transactions
            cursor.execute("""
                SELECT COUNT(*) as count FROM journal_entries 
                WHERE debit_account_name = %s OR credit_account_name = %s
            """, (code, code))
            
            if cursor.fetchone()['count'] > 0:
                raise Exception("Cannot delete account with existing transactions")
            
            cursor.execute("DELETE FROM accounts WHERE code = %s", (code,))
            self.logger.info(f"Deleted account {code}")
    
    # Journal Entry Management
    def add_journal_entry(self, date, description, debit_account, credit_account, amount):
        """Add a journal entry with UI-compatible signature."""
        if date is None:
            date = datetime.now().date()
        
        entry_id = str(uuid.uuid4())
        
        # Clean and convert amount to Decimal
        try:
            # Remove common formatting characters
            if isinstance(amount, str):
                # Remove currency symbols, commas, and extra whitespace
                cleaned_amount = amount.replace('$', '').replace(',', '').strip()
                if not cleaned_amount:
                    raise ValueError("Empty amount")
                amount_decimal = Decimal(cleaned_amount)
            elif amount is None:
                raise ValueError("Amount cannot be None")
            else:
                amount_decimal = Decimal(str(amount))
            
            # Ensure positive amount
            if amount_decimal <= 0:
                raise ValueError("Amount must be positive")
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid amount format: '{amount}'. Please enter a valid numeric amount.") from e
        except Exception as e:
            self.logger.error(f"Unexpected error in decimal conversion: {e}")
            raise ValueError(f"Invalid amount format: '{amount}'. Please enter a valid numeric amount.") from e
        
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO journal_entries (id, debit_account_name, credit_account_name, amount, description, entry_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (entry_id, debit_account, credit_account, amount_decimal, description, date))
            
            self.logger.info(f"Added journal entry: {debit_account} -> {credit_account}, Amount: {amount_decimal}")
            return entry_id
    
    def get_journal_entries(self, limit=None, account_filter=None):
        """Get journal entries with optional filtering."""
        with self.db_manager.get_db_cursor() as cursor:
            query = """
                SELECT id, debit_account_name, credit_account_name, amount, description, entry_date, created_at
                FROM journal_entries
            """
            params = []
            
            if account_filter:
                query += " WHERE debit_account_name = %s OR credit_account_name = %s"
                params.extend([account_filter, account_filter])
            
            query += " ORDER BY entry_date DESC, created_at DESC"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_journal_entries_by_date_range(self, from_date, to_date):
        """Get journal entries within a specific date range."""
        with self.db_manager.get_db_cursor() as cursor:
            query = """
                SELECT id, debit_account_name, credit_account_name, amount, description, entry_date, created_at
                FROM journal_entries
                WHERE entry_date BETWEEN %s AND %s
                ORDER BY entry_date DESC, created_at DESC
            """
            cursor.execute(query, (from_date, to_date))
            return cursor.fetchall()
    
    def update_journal_entry(self, entry_id, **kwargs):
        """Update a journal entry."""
        if not kwargs:
            return
        
        with self.db_manager.get_db_cursor() as cursor:
            set_clauses = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['debit_account', 'credit_account', 'amount', 'description', 'date']:
                    if key == 'debit_account':
                        set_clauses.append("debit_account_name = %s")
                    elif key == 'credit_account':
                        set_clauses.append("credit_account_name = %s")
                    elif key == 'date':
                        set_clauses.append("entry_date = %s")
                    elif key == 'amount':
                        set_clauses.append("amount = %s")
                        value = Decimal(str(value))
                    else:
                        set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if set_clauses:
                values.append(entry_id)
                query = f"UPDATE journal_entries SET {', '.join(set_clauses)} WHERE id = %s"
                cursor.execute(query, values)
                self.logger.info(f"Updated journal entry {entry_id}")
    
    def delete_journal_entry(self, entry_id):
        """Delete a journal entry."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("DELETE FROM journal_entries WHERE id = %s", (entry_id,))
            self.logger.info(f"Deleted journal entry {entry_id}")
    
    # Reporting
    def get_account_balance(self, account_name_or_code):
        """Get the balance of an account."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN debit_account_name = %s THEN amount ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN credit_account_name = %s THEN amount ELSE 0 END), 0) as balance
                FROM journal_entries
                WHERE debit_account_name = %s OR credit_account_name = %s            """, (account_name_or_code, account_name_or_code, account_name_or_code, account_name_or_code))
            
            result = cursor.fetchone()
            return float(result['balance']) if result and result['balance'] is not None else 0.0
    
    def get_trial_balance(self, from_date=None, to_date=None):
        """Generate trial balance report."""
        with self.db_manager.get_db_cursor() as cursor:
            query = """
                SELECT 
                    a.name,
                    a.type,
                    a.code,
                    COALESCE(SUM(CASE WHEN je.debit_account_name = a.name OR je.debit_account_name = a.code THEN je.amount ELSE 0 END), 0) as debit_total,
                    COALESCE(SUM(CASE WHEN je.credit_account_name = a.name OR je.credit_account_name = a.code THEN je.amount ELSE 0 END), 0) as credit_total
                FROM accounts a
                LEFT JOIN journal_entries je ON (je.debit_account_name = a.name OR je.debit_account_name = a.code OR 
                                                je.credit_account_name = a.name OR je.credit_account_name = a.code)
                WHERE a.is_postable = TRUE
            """
            
            params = []
            if from_date or to_date:
                date_conditions = []
                if from_date:
                    date_conditions.append("je.entry_date >= %s")
                    params.append(from_date)
                if to_date:
                    date_conditions.append("je.entry_date <= %s")
                    params.append(to_date)
                
                if date_conditions:
                    query += f" AND ({' AND '.join(date_conditions)})"
            
            query += """
                GROUP BY a.name, a.type, a.code
                HAVING COALESCE(SUM(CASE WHEN je.debit_account_name = a.name OR je.debit_account_name = a.code THEN je.amount ELSE 0 END), 0) != 0
                    OR COALESCE(SUM(CASE WHEN je.credit_account_name = a.name OR je.credit_account_name = a.code THEN je.amount ELSE 0 END), 0) != 0
                ORDER BY a.code NULLS LAST, a.name
            """
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_ledger(self, account_name_or_code):
        """Get ledger entries for a specific account."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    entry_date,
                    description,
                    '' as reference,
                    CASE WHEN debit_account_name = %s THEN amount ELSE 0 END as debit,
                    CASE WHEN credit_account_name = %s THEN amount ELSE 0 END as credit,
                    id
                FROM journal_entries
                WHERE debit_account_name = %s OR credit_account_name = %s
                ORDER BY entry_date, created_at
            """, (account_name_or_code, account_name_or_code, account_name_or_code, account_name_or_code))
            return cursor.fetchall()
    
    # Bulk Operations
    def bulk_add_accounts(self, accounts_data):
        """Add multiple accounts in a single transaction."""
        with self.db_manager.get_db_cursor() as cursor:
            for account in accounts_data:
                self.create_account(**account)
    
    def bulk_add_journal_entries(self, entries_data):
        """Add multiple journal entries in a single transaction."""
        with self.db_manager.get_db_cursor() as cursor:
            for entry in entries_data:
                self.add_journal_entry(**entry)
    
    # Utility Methods
    def get_account_hierarchy(self):
        """Get accounts organized by hierarchy."""
        with self.db_manager.get_db_cursor() as cursor:
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description
                FROM accounts
                ORDER BY level, code NULLS LAST, name
            """)
            return cursor.fetchall()
    
    def search_accounts(self, search_term):
        """Search accounts by name, code, or description."""
        with self.db_manager.get_db_cursor() as cursor:
            search_pattern = f"%{search_term}%"
            cursor.execute("""
                SELECT name, type, code, parent_code, level, is_postable, description
                FROM accounts
                WHERE name ILIKE %s OR code ILIKE %s OR description ILIKE %s
                ORDER BY name            """, (search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()
    
    def get_statistics(self):
        """Get database statistics."""
        with self.db_manager.get_db_cursor() as cursor:
            stats = {}
            
            # Account counts
            cursor.execute("SELECT COUNT(*) as count FROM accounts")
            stats['total_accounts'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE is_postable = TRUE")
            stats['postable_accounts'] = cursor.fetchone()['count']
            
            # Journal entry counts
            cursor.execute("SELECT COUNT(*) as count FROM journal_entries")
            stats['total_entries'] = cursor.fetchone()['count']
            
            # Date range
            cursor.execute("SELECT MIN(entry_date) as min_date, MAX(entry_date) as max_date FROM journal_entries")
            date_range = cursor.fetchone()
            stats['date_range'] = (date_range['min_date'], date_range['max_date']) if date_range['min_date'] else (None, None)
            
            return stats

# Create alias for backward compatibility
AccountingSystem = AccountingSystemPostgreSQL
