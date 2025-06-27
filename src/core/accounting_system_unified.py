"""
Unified Accounting System
Merges all functionality from multiple systems into one comprehensive solution
Combines: SupabaseManager + Offline Support + Enhanced Features + Financial Calculations
"""

import logging
import sqlite3
import json
import threading
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from decimal import Decimal

from .supabase_manager import SupabaseManager
from .auth_manager import AuthManager

class OfflineManager:
    """Manages offline operations and sync queue"""
    
    def __init__(self, cache_db_path="offline_cache.db"):
        self.cache_db_path = cache_db_path
        self.logger = logging.getLogger(__name__)
        self.setup_cache_db()
        
    def setup_cache_db(self):
        """Create local SQLite cache for offline operations"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Cache tables mirror Supabase structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_accounts (
                id TEXT PRIMARY KEY,
                organization_id TEXT,
                name TEXT,
                type TEXT,
                code TEXT,
                data TEXT,  -- JSON blob
                last_synced TEXT,
                is_dirty BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_journal_entries (
                id TEXT PRIMARY KEY,
                organization_id TEXT,
                date TEXT,
                description TEXT,
                amount REAL,
                data TEXT,  -- JSON blob
                last_synced TEXT,
                is_dirty BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def cache_data(self, table_name: str, data: List[Dict], organization_id: str):
        """Cache data locally for offline access"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        try:
            for item in data:
                if table_name == 'accounts':
                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_accounts 
                        (id, organization_id, name, type, code, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('id', str(uuid.uuid4())),
                        organization_id,
                        item.get('name'),
                        item.get('type'),
                        item.get('code'),
                        json.dumps(item),
                        datetime.now().isoformat(),
                        0
                    ))
                elif table_name == 'journal_entries':
                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_journal_entries 
                        (id, organization_id, date, description, amount, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('id', str(uuid.uuid4())),
                        organization_id,
                        item.get('date'),
                        item.get('description'),
                        item.get('amount'),
                        json.dumps(item),
                        datetime.now().isoformat(),
                        0
                    ))
            
            conn.commit()
            self.logger.info(f"Cached {len(data)} {table_name} records")
            
        except Exception as e:
            self.logger.error(f"Failed to cache {table_name}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_cached_data(self, table_name: str, organization_id: str) -> List[Dict]:
        """Get cached data for offline access"""
        conn = sqlite3.connect(self.cache_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if table_name == 'accounts':
                cursor.execute(
                    'SELECT data FROM cached_accounts WHERE organization_id = ?',
                    (organization_id,)
                )
            elif table_name == 'journal_entries':
                cursor.execute(
                    'SELECT data FROM cached_journal_entries WHERE organization_id = ?',
                    (organization_id,)
                )
            
            rows = cursor.fetchall()
            return [json.loads(row['data']) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Failed to get cached {table_name}: {e}")
            return []
        finally:
            conn.close()

class AccountingSystem:
    """
    Unified Accounting System with all features:
    - Supabase database operations with RLS and authentication
    - Offline support with SQLite cache and auto-sync
    - Complete financial calculations and reporting
    """
    
    def __init__(self, auth_manager: AuthManager):
        self.logger = logging.getLogger(__name__)
        self.auth_manager = auth_manager
        self.db_manager = auth_manager.db_manager
        self.current_organization_id = None
        
        # Get current user info
        current_user = self.auth_manager.get_current_user()
        self.current_user_id = current_user['id'] if current_user else None
        
        # Initialize offline support
        self.offline_manager = OfflineManager()
        self.is_online = self._test_connectivity()
        
        if not self.current_user_id:
            raise ValueError("No authenticated user found")
            
        self.logger.info(f"Unified accounting system initialized for user {current_user.get('email', 'Unknown')}")
        
    def _test_connectivity(self) -> bool:
        """Test if Supabase is reachable"""
        try:
            if hasattr(self.db_manager, 'supabase'):
                self.db_manager.supabase.table('organizations').select('id').limit(1).execute()
                return True
        except Exception as e:
            self.logger.warning(f"Connectivity test failed: {e}")
        return False
        
    def set_organization(self, org_id: str) -> bool:
        """Set the current organization for operations."""
        if not self.auth_manager.can_read_accounting_data(org_id):
            self.logger.warning(f"User lacks permission to access organization {org_id}")
            return False
        
        self.current_organization_id = org_id
        self.logger.info(f"Set organization context to {org_id}")
        return True
    
    def get_current_organization_id(self) -> Optional[str]:
        """Get the current organization ID."""
        return self.current_organization_id
    
    # ================================
    # CHART OF ACCOUNTS with Offline Support
    # ================================
    
    def get_chart_of_accounts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get chart of accounts with offline fallback."""
        if not self.current_organization_id:
            return []
        
        # Try online first
        if self.is_online:
            try:
                accounts = self.db_manager.get_accounts(self.current_organization_id, active_only)
                # Cache the data
                if accounts:
                    self.offline_manager.cache_data('accounts', accounts, self.current_organization_id)
                return accounts
            except Exception as e:
                self.logger.error(f"Online accounts fetch failed: {e}")
                self.is_online = False
        
        # Fallback to cached data
        self.logger.info("📱 Using cached accounts data (offline mode)")
        cached_accounts = self.offline_manager.get_cached_data('accounts', self.current_organization_id)
        
        if active_only:
            return [acc for acc in cached_accounts if acc.get('is_active', True)]
        return cached_accounts
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts in dictionary format."""
        return self.get_chart_of_accounts(active_only=False)
    
    def get_postable_accounts(self) -> List[Dict[str, Any]]:
        """Get only postable accounts."""
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc.get('is_postable', True)]
    
    def get_accounts_by_level(self, level: int = 1) -> List[Dict[str, Any]]:
        """Get accounts by hierarchy level."""
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc.get('level', 1) == level]
    
    def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account."""
        if not self.current_organization_id:
            return {"success": False, "error": "No organization set"}
        
        if not self.auth_manager.can_write_accounting_data(self.current_organization_id):
            return {"success": False, "error": "Insufficient permissions"}
        
        # Ensure organization_id and created_by are set
        account_data['organization_id'] = self.current_organization_id
        account_data['created_by'] = self.current_user_id
        account_data['created_at'] = datetime.now().isoformat()
        
        try:
            result = self.db_manager.create_account(account_data)
            if result:
                self.logger.info(f"Created account: {account_data.get('name')}")
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": "Failed to create account"}
        except Exception as e:
            self.logger.error(f"Error creating account: {e}")
            return {"success": False, "error": str(e)}
    
    def update_account(self, account_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing account."""
        if not self.auth_manager.can_write_accounting_data(self.current_organization_id):
            return False
        
        try:
            return self.db_manager.update_account(account_id, updates)
        except Exception as e:
            self.logger.error(f"Error updating account: {e}")
            return False
    
    # ================================
    # JOURNAL ENTRIES with Offline Support
    # ================================
    
    def get_journal_entries(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get journal entries with offline fallback."""
        if not self.current_organization_id:
            return []
        
        # Try online first
        if self.is_online:
            try:
                entries = self.db_manager.get_journal_entries(self.current_organization_id)
                # Apply date filtering
                if start_date or end_date:
                    filtered = []
                    for entry in entries:
                        entry_date = entry.get('date', '')
                        if start_date and entry_date < start_date:
                            continue
                        if end_date and entry_date > end_date:
                            continue
                        filtered.append(entry)
                    entries = filtered
                
                # Cache the data
                if entries:
                    self.offline_manager.cache_data('journal_entries', entries, self.current_organization_id)
                return entries
            except Exception as e:
                self.logger.error(f"Online journal entries fetch failed: {e}")
                self.is_online = False
        
        # Fallback to cached data
        self.logger.info("📱 Using cached journal entries (offline mode)")
        cached_entries = self.offline_manager.get_cached_data('journal_entries', self.current_organization_id)
        
        # Apply date filtering to cached data
        if start_date or end_date:
            filtered = []
            for entry in cached_entries:
                entry_date = entry.get('date', '')
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                filtered.append(entry)
            return filtered
        
        return cached_entries
    
    def add_journal_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a journal entry."""
        if not self.current_organization_id:
            return {"success": False, "error": "No organization set"}
        
        if not self.auth_manager.can_write_accounting_data(self.current_organization_id):
            return {"success": False, "error": "Insufficient permissions"}
        
        # Ensure required fields are set
        entry_data['organization_id'] = self.current_organization_id
        entry_data['created_by'] = self.current_user_id
        entry_data['created_at'] = datetime.now().isoformat()
        
        try:
            result = self.db_manager.create_journal_entry(entry_data)
            if result:
                self.logger.info(f"Created journal entry: {entry_data.get('description')}")
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": "Failed to create journal entry"}
        except Exception as e:
            self.logger.error(f"Error creating journal entry: {e}")
            return {"success": False, "error": str(e)}
    
    def get_recent_journal_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent journal entries."""
        entries = self.get_journal_entries()
        # Sort by date descending and limit
        sorted_entries = sorted(entries, key=lambda x: x.get('date', ''), reverse=True)
        return sorted_entries[:limit]
    
    # ================================
    # FINANCIAL CALCULATIONS
    # ================================
    
    def get_trial_balance(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, float]:
        """Calculate trial balance from journal entries."""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_all_accounts()
        
        # Create account lookup
        account_lookup = {acc['name']: acc for acc in accounts}
        account_balances = {}
        
        for entry in entries:
            debit_account = entry.get('debit_account', '')
            credit_account = entry.get('credit_account', '')
            amount = float(entry.get('amount', 0))
            
            # Initialize accounts if not exists
            if debit_account not in account_balances:
                account_balances[debit_account] = 0.0
            if credit_account not in account_balances:
                account_balances[credit_account] = 0.0
            
            # Apply debits and credits based on account types
            debit_info = account_lookup.get(debit_account, {})
            credit_info = account_lookup.get(credit_account, {})
            
            debit_type = debit_info.get('type', '').lower()
            credit_type = credit_info.get('type', '').lower()
            
            # Assets, Expenses increase with debits
            if debit_type in ['asset', 'expense']:
                account_balances[debit_account] += amount
            else:
                account_balances[debit_account] -= amount
            
            # Liabilities, Equity, Revenue increase with credits  
            if credit_type in ['liability', 'equity', 'revenue']:
                account_balances[credit_account] += amount
            else:
                account_balances[credit_account] -= amount
        
        return account_balances
    
    def generate_income_statement_breakdown(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate income statement with breakdown."""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_all_accounts()
        
        # Create account type lookup
        account_types = {acc['name']: acc['type'].lower() for acc in accounts}
        
        revenue_total = 0.0
        expense_total = 0.0
        revenue_breakdown = {}
        expense_breakdown = {}
        
        for entry in entries:
            debit_account = entry.get('debit_account', '')
            credit_account = entry.get('credit_account', '')
            amount = float(entry.get('amount', 0))
            
            # Process revenue (credits to revenue accounts)
            if account_types.get(credit_account) == 'revenue':
                revenue_total += amount
                if credit_account not in revenue_breakdown:
                    revenue_breakdown[credit_account] = 0.0
                revenue_breakdown[credit_account] += amount
            
            # Process expenses (debits to expense accounts)
            if account_types.get(debit_account) == 'expense':
                expense_total += amount
                if debit_account not in expense_breakdown:
                    expense_breakdown[debit_account] = 0.0
                expense_breakdown[debit_account] += amount
        
        net_income = revenue_total - expense_total
        
        return {
            'revenue_total': revenue_total,
            'expense_total': expense_total,
            'net_income': net_income,
            'revenue_breakdown': revenue_breakdown,
            'expense_breakdown': expense_breakdown,
            'period_start': start_date,
            'period_end': end_date
        }
    
    def generate_balance_sheet_breakdown(self, as_of_date: str) -> Dict[str, Any]:
        """Generate balance sheet as of a specific date."""
        trial_balance = self.get_trial_balance(None, as_of_date)
        accounts = self.get_all_accounts()
        
        # Create account type lookup
        account_types = {acc['name']: acc['type'].lower() for acc in accounts}
        
        assets = {}
        liabilities = {}
        equity = {}
        
        for account_name, balance in trial_balance.items():
            account_type = account_types.get(account_name, '').lower()
            
            if account_type == 'asset':
                assets[account_name] = balance
            elif account_type == 'liability':
                liabilities[account_name] = balance
            elif account_type == 'equity':
                equity[account_name] = balance
        
        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        total_equity = sum(equity.values())
        
        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'as_of_date': as_of_date
        }
    
    # ================================
    # UTILITY METHODS
    # ================================
    
    def is_account_postable(self, account_name_or_code: str) -> bool:
        """Check if account is postable."""
        accounts = self.get_all_accounts()
        for acc in accounts:
            if acc['name'] == account_name_or_code or acc.get('code') == account_name_or_code:
                return acc.get('is_postable', True)
        return True  # Default to postable
    
    def resolve_account(self, account_input: str) -> str:
        """Resolve account name from input."""
        accounts = self.get_all_accounts()
        
        # Try exact match first
        for acc in accounts:
            if acc['name'] == account_input or acc.get('code') == account_input:
                return acc['name']
        
        # Try partial match
        account_input_lower = account_input.lower()
        for acc in accounts:
            if account_input_lower in acc['name'].lower():
                return acc['name']
        
        return account_input  # Return as-is if no match
    
    def refresh_connection(self):
        """Refresh database connection and test connectivity."""
        self.is_online = self._test_connectivity()
        self.logger.info(f"Connection status: {'Online' if self.is_online else 'Offline'}")
