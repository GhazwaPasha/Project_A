"""
Enhanced Database Manager with Offline Support
Supabase-first with local SQLite cache for offline resilience
"""
import sqlite3
import psycopg2
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import threading
import queue
import uuid

class OfflineManager:
    """Manages offline operations and sync queue"""
    
    def __init__(self, cache_db_path="offline_cache.db"):
        self.cache_db_path = cache_db_path
        self.logger = logging.getLogger(__name__)
        self.sync_queue = queue.Queue()
        self.is_online = True
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_operations (
                id TEXT PRIMARY KEY,
                operation_type TEXT,  -- INSERT, UPDATE, DELETE
                table_name TEXT,
                data TEXT,  -- JSON blob
                organization_id TEXT,
                user_id TEXT,
                created_at TEXT,
                retry_count INTEGER DEFAULT 0
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
                if table_name == 'accounts':                    cursor.execute('''
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
                elif table_name == 'journal_entries':                    cursor.execute('''
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
    
    def queue_operation(self, operation_type: str, table_name: str, data: Dict, 
                       organization_id: str, user_id: str):
        """Queue an operation for later sync when online"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        try:
            operation_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO pending_operations 
                (id, operation_type, table_name, data, organization_id, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                operation_id,
                operation_type,
                table_name,
                json.dumps(data),
                organization_id,
                user_id,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            self.logger.info(f"Queued {operation_type} operation for {table_name}")
            
            # Also update local cache immediately for better UX
            self._update_local_cache(operation_type, table_name, data, organization_id)
            
        except Exception as e:
            self.logger.error(f"Failed to queue operation: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _update_local_cache(self, operation_type: str, table_name: str, 
                           data: Dict, organization_id: str):
        """Update local cache immediately for better offline UX"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        try:
            if operation_type == 'INSERT':
                data['id'] = data.get('id', str(uuid.uuid4()))
                if table_name == 'accounts':                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_accounts 
                        (id, organization_id, name, type, code, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['id'], organization_id, data.get('name'),
                        data.get('type'), data.get('code'), json.dumps(data),
                        datetime.now().isoformat(), 1
                    ))
                elif table_name == 'journal_entries':                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_journal_entries 
                        (id, organization_id, date, description, amount, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['id'], organization_id, data.get('date'),
                        data.get('description'), data.get('amount'), json.dumps(data),
                        datetime.now().isoformat(), 1
                    ))
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update local cache: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def sync_pending_operations(self, supabase_client):
        """Sync all pending operations when back online"""
        conn = sqlite3.connect(self.cache_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM pending_operations ORDER BY created_at')
            operations = cursor.fetchall()
            
            successful_ops = []
            
            for op in operations:
                try:
                    data = json.loads(op['data'])
                    
                    if op['operation_type'] == 'INSERT':
                        supabase_client.table(op['table_name']).insert(data).execute()
                    elif op['operation_type'] == 'UPDATE':
                        supabase_client.table(op['table_name']).update(data).eq('id', data['id']).execute()
                    elif op['operation_type'] == 'DELETE':
                        supabase_client.table(op['table_name']).delete().eq('id', data['id']).execute()
                    
                    successful_ops.append(op['id'])
                    self.logger.info(f"Synced {op['operation_type']} on {op['table_name']}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to sync operation {op['id']}: {e}")
                    # Increment retry count
                    cursor.execute(
                        'UPDATE pending_operations SET retry_count = retry_count + 1 WHERE id = ?',
                        (op['id'],)
                    )
            
            # Remove successful operations
            for op_id in successful_ops:
                cursor.execute('DELETE FROM pending_operations WHERE id = ?', (op_id,))
            
            conn.commit()
            return len(successful_ops)
            
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            return 0
        finally:
            conn.close()

class EnhancedSupabaseOnlyManager:
    """Supabase-first with robust offline support"""
    
    def __init__(self, organization_id=None, user_id=None):
        self.organization_id = organization_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        
        # Initialize Supabase
        from supabase import create_client
        import os
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        
        # Initialize offline manager
        self.offline_manager = OfflineManager()
        
        # Test connectivity
        self.is_online = self._test_connectivity()
        
        # Start connectivity monitoring
        self._start_connectivity_monitor()
    
    def _test_connectivity(self) -> bool:
        """Test if Supabase is reachable"""
        try:
            # Simple query to test connectivity
            self.supabase.table('organizations').select('id').limit(1).execute()
            return True
        except Exception as e:
            self.logger.warning(f"Supabase connectivity test failed: {e}")
            return False
    
    def _start_connectivity_monitor(self):
        """Monitor connectivity and auto-sync when back online"""
        def monitor_loop():
            while True:
                import time
                time.sleep(10)  # Check every 10 seconds
                
                was_online = self.is_online
                self.is_online = self._test_connectivity()
                
                if not was_online and self.is_online:
                    # Just came back online - sync pending operations
                    self.logger.info("🌐 Back online - syncing pending operations...")
                    synced = self.offline_manager.sync_pending_operations(self.supabase)
                    self.logger.info(f"✅ Synced {synced} pending operations")
                    
                    # Refresh cache from server
                    self._refresh_cache()
        
        import threading
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _refresh_cache(self):
        """Refresh local cache from Supabase"""
        if not self.is_online or not self.organization_id:
            return
        
        try:
            # Set database context first
            self._set_database_context()
            
            # Cache accounts
            accounts = self.supabase.table('accounts').select('*').execute()
            if accounts.data:
                self.offline_manager.cache_data('accounts', accounts.data, self.organization_id)
            
            # Cache journal entries
            entries = self.supabase.table('journal_entries').select('*').execute()
            if entries.data:
                self.offline_manager.cache_data('journal_entries', entries.data, self.organization_id)
            
            self.logger.info("✅ Cache refreshed from Supabase")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh cache: {e}")
    
    def _set_database_context(self):
        """Set PostgreSQL context for RLS policies"""
        if not self.is_online:
            return
        
        try:
            self.supabase.rpc('set_app_context', {
                'user_id': self.user_id,
                'organization_id': self.organization_id,
                'role': 'accountant'  # This should come from session
            }).execute()
        except Exception as e:
            self.logger.error(f"Failed to set database context: {e}")
    
    # Accounting Operations with Offline Support
    def get_accounts(self) -> List[Dict]:
        """Get accounts - online first, offline fallback"""
        if self.is_online:
            try:
                self._set_database_context()
                result = self.supabase.table('accounts').select('*').execute()
                if result.data:
                    # Update cache
                    self.offline_manager.cache_data('accounts', result.data, self.organization_id)
                    return result.data
            except Exception as e:
                self.logger.error(f"Online accounts fetch failed: {e}")
        
        # Fallback to cached data
        self.logger.info("📱 Using cached accounts data (offline mode)")
        return self.offline_manager.get_cached_data('accounts', self.organization_id)
    
    def create_account(self, account_data: Dict) -> Dict:
        """Create account - queue if offline"""
        if self.is_online:
            try:
                self._set_database_context()
                result = self.supabase.table('accounts').insert(account_data).execute()
                if result.data:
                    return {"success": True, "data": result.data[0]}
            except Exception as e:
                self.logger.error(f"Online account creation failed: {e}")
                self.is_online = False  # Mark as offline and queue
        
        # Queue for later sync
        self.offline_manager.queue_operation(
            'INSERT', 'accounts', account_data, self.organization_id, self.user_id
        )
        return {"success": True, "data": account_data, "queued": True}
    
    def get_journal_entries(self, start_date=None, end_date=None) -> List[Dict]:
        """Get journal entries with offline support"""
        if self.is_online:
            try:
                self._set_database_context()
                query = self.supabase.table('journal_entries').select('*')
                if start_date:
                    query = query.gte('date', start_date)
                if end_date:
                    query = query.lte('date', end_date)
                
                result = query.execute()
                if result.data:
                    self.offline_manager.cache_data('journal_entries', result.data, self.organization_id)
                    return result.data
            except Exception as e:
                self.logger.error(f"Online journal entries fetch failed: {e}")
        
        # Fallback to cached data
        self.logger.info("📱 Using cached journal entries (offline mode)")
        cached_entries = self.offline_manager.get_cached_data('journal_entries', self.organization_id)
        
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

    def add_journal_entry(self, entry_data: Dict) -> Dict:
        """Add journal entry with offline support"""
        if self.is_online:
            try:
                self._set_database_context()
                result = self.supabase.table('journal_entries').insert(entry_data).execute()
                if result.data:
                    return {"success": True, "data": result.data[0]}
            except Exception as e:
                self.logger.error(f"Online journal entry creation failed: {e}")
                self.is_online = False
        
        # Queue for later sync
        self.offline_manager.queue_operation(
            'INSERT', 'journal_entries', entry_data, self.organization_id, self.user_id
        )
        return {"success": True, "data": entry_data, "queued": True}

    def get_trial_balance(self, start_date=None, end_date=None) -> Dict[str, float]:
        """Calculate trial balance from journal entries"""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_accounts()
        
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

    def get_all_accounts(self) -> List[Tuple]:
        """Get all accounts in tuple format for compatibility"""
        accounts = self.get_accounts()
        result = []
        
        for acc in accounts:
            # Convert to tuple format: (name, type, code, parent_code, level, is_postable, description)
            result.append((
                acc.get('name', ''),
                acc.get('type', ''),
                acc.get('code', ''),
                acc.get('parent_code', ''),
                acc.get('level', 1),
                acc.get('is_postable', True),
                acc.get('description', '')
            ))
        
        return result

    def get_postable_accounts(self) -> List[Tuple]:
        """Get only postable accounts"""
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc[5]]  # is_postable is index 5

    def get_accounts_by_level(self, level: int = 1) -> List[Tuple]:
        """Get accounts by hierarchy level"""
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc[4] == level]  # level is index 4

    def get_recent_journal_entries(self, limit: int = 20) -> List[Dict]:
        """Get recent journal entries"""
        entries = self.get_journal_entries()
        # Sort by date descending and limit
        sorted_entries = sorted(entries, key=lambda x: x.get('date', ''), reverse=True)
        return sorted_entries[:limit]

    def get_ledger(self, account_name: str, start_date=None, end_date=None) -> List[Tuple]:
        """Get ledger entries for specific account"""
        entries = self.get_journal_entries(start_date, end_date)
        ledger_entries = []
        
        for entry in entries:
            date = entry.get('date', '')
            description = entry.get('description', '')
            debit_account = entry.get('debit_account', '')
            credit_account = entry.get('credit_account', '')
            amount = float(entry.get('amount', 0))
            
            if debit_account == account_name or credit_account == account_name:
                # Format: (date, description, debit_account, credit_account, amount)
                ledger_entries.append((date, description, debit_account, credit_account, amount))
        
        return sorted(ledger_entries, key=lambda x: x[0])  # Sort by date

    def generate_income_statement_breakdown(self, start_date: str, end_date: str) -> Dict:
        """Generate income statement with breakdown"""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_accounts()
        
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
            'expense_breakdown': expense_breakdown
        }

    def generate_balance_sheet_breakdown(self, as_of_date: str) -> Dict:
        """Generate balance sheet as of a specific date"""
        trial_balance = self.get_trial_balance(None, as_of_date)
        accounts = self.get_accounts()
        
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
            'total_equity': total_equity
        }

    def generate_statement_of_equity(self, start_date: str, end_date: str) -> Dict:
        """Generate statement of equity"""
        # Get beginning equity balance
        beginning_balance = self.get_trial_balance(None, start_date)
        accounts = self.get_accounts()
        account_types = {acc['name']: acc['type'].lower() for acc in accounts}
        
        beginning_equity = sum(
            balance for account, balance in beginning_balance.items()
            if account_types.get(account, '').lower() == 'equity'
        )
        
        # Get net income for the period
        income_statement = self.generate_income_statement_breakdown(start_date, end_date)
        net_income = income_statement['net_income']
        
        # Calculate ending equity
        ending_equity = beginning_equity + net_income
        
        return {
            'beginning_equity': beginning_equity,
            'net_income': net_income,
            'ending_equity': ending_equity,
            'changes': {
                'retained_earnings': net_income
            }
        }

    # Utility methods for compatibility
    def refresh_connection(self):
        """Refresh database connection"""
        self.is_online = self._test_connectivity()
        if self.is_online:
            self._refresh_cache()

    def seed_hierarchical_accounts(self):
        """Seed chart of accounts (placeholder)"""
        self.logger.info("Chart of accounts seeding not implemented for Supabase system")
        return True

    def force_reseed_hierarchical_accounts(self):
        """Force reseed accounts (placeholder)"""
        self.logger.info("Force reseed not implemented for Supabase system")
        return True

    def is_account_postable(self, account_name_or_code: str) -> bool:
        """Check if account is postable"""
        accounts = self.get_accounts()
        for acc in accounts:
            if acc['name'] == account_name_or_code or acc.get('code') == account_name_or_code:
                return acc.get('is_postable', True)
        return True  # Default to postable

    def resolve_account(self, account_input: str) -> str:
        """Resolve account name from input"""
        accounts = self.get_accounts()
        
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

    def clear_journal_entries(self):
        """Clear all journal entries (admin function)"""
        if self.is_online:
            try:
                self._set_database_context()
                # This should be restricted to admin users
                result = self.supabase.table('journal_entries').delete().neq('id', 'never-match').execute()
                self.logger.warning("Cleared all journal entries from database")
                return len(result.data) if result.data else 0
            except Exception as e:
                self.logger.error(f"Failed to clear journal entries: {e}")
                return 0
        else:
            self.logger.warning("Cannot clear journal entries while offline")
            return 0

    def add_journal_entries_batch(self, entries: List[Dict]) -> int:
        """Add multiple journal entries"""
        successful = 0
        for entry in entries:
            result = self.add_journal_entry(entry)
            if result.get('success'):
                successful += 1
        return successful

    def add_journal_entries_with_progress(self, entries: List[Dict], progress_callback=None) -> int:
        """Add journal entries with progress callback"""
        successful = 0
        total = len(entries)
        
        for i, entry in enumerate(entries):
            result = self.add_journal_entry(entry)
            if result.get('success'):
                successful += 1
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return successful

    def get_journal_entries_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get journal entries by date range - alias for compatibility"""
        return self.get_journal_entries(start_date, end_date)
