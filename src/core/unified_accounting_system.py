"""
Unified Accounting System
Combines all functionality from multiple systems into one comprehensive solution:
- Core accounting operations (SupabaseManager + AccountingSystem)
- Offline support with sync (EnhancedSupabaseOnlyManager)
- Advanced features (EnhancedAccountingSystem)
- Financial calculations and reporting
- Period closing and audit trails
"""

import logging
import sqlite3
import json
import threading
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from decimal import Decimal
import calendar

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .config import DatabaseConfig
from .auth_manager import AuthManager

class OfflineCache:
    """Manages offline SQLite cache and sync operations"""
    
    def __init__(self, cache_db_path="offline_cache.db"):
        self.cache_db_path = cache_db_path
        self.logger = logging.getLogger(__name__)
        self.setup_cache_db()
        
    def setup_cache_db(self):
        """Create local SQLite cache tables"""
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
                    from .data_transformer import data_transformer
                    # Transform database format for caching
                    cache_entry = data_transformer.db_to_cache_journal_entry(item)
                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_journal_entries 
                        (id, organization_id, date, description, amount, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        cache_entry.get('id', str(uuid.uuid4())),
                        organization_id,
                        cache_entry.get('date'),
                        cache_entry.get('description'), 
                        cache_entry.get('amount'),
                        json.dumps(cache_entry),
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
            cached_data = [json.loads(row['data']) for row in rows]
            
            # Transform cached journal entries to application format
            if table_name == 'journal_entries':
                from .data_transformer import data_transformer
                transformed_data = []
                for item in cached_data:
                    app_entry = data_transformer.cache_to_app_journal_entry(item)
                    transformed_data.append(app_entry)
                return transformed_data
            
            return cached_data
            
        except Exception as e:
            self.logger.error(f"Failed to get cached {table_name}: {e}")
            return []
        finally:
            conn.close()
    
    def queue_operation(self, operation_type: str, table_name: str, data: Dict, 
                       organization_id: str, user_id: str):
        """Queue an operation for later sync when online"""
        print(f"🔄 DEBUG: queue_operation called")
        print(f"   operation_type: {operation_type}")
        print(f"   table_name: {table_name}")
        print(f"   organization_id: {organization_id}")
        print(f"   user_id: {user_id}")
        print(f"   data keys: {list(data.keys()) if data else 'None'}")
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        try:
            operation_id = str(uuid.uuid4())
            print(f"   Generated operation_id: {operation_id}")
            
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
            print(f"✅ DEBUG: Operation queued successfully with ID: {operation_id}")
            self.logger.info(f"Queued {operation_type} operation for {table_name}")
            
            # Also update local cache immediately for better UX
            print(f"🔄 DEBUG: Updating local cache...")
            self._update_local_cache(operation_type, table_name, data, organization_id)
            print(f"✅ DEBUG: Local cache updated")
            
        except Exception as e:
            print(f"❌ DEBUG: Failed to queue operation: {e}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
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
                if table_name == 'accounts':
                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_accounts 
                        (id, organization_id, name, type, code, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['id'], organization_id, data.get('name'),
                        data.get('type'), data.get('code'), json.dumps(data),
                        datetime.now().isoformat(), 1
                    ))
                elif table_name == 'journal_entries':
                    from .data_transformer import data_transformer
                    # Transform for caching (data is already in app format here)
                    cache_entry = data_transformer.app_to_cache_journal_entry(data)
                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_journal_entries 
                        (id, organization_id, date, description, amount, data, last_synced, is_dirty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['id'], organization_id, cache_entry.get('date'),
                        cache_entry.get('description'), cache_entry.get('amount'), json.dumps(cache_entry),
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
                    
                    # Normalize account_type for accounts table operations
                    if op['table_name'] == 'accounts' and 'account_type' in data:
                        data['account_type'] = data['account_type'].lower()
                    
                    if op['operation_type'] == 'INSERT':
                        # Special handling for journal entries with new format
                        if op['table_name'] == 'journal_entries' and isinstance(data, dict) and 'header' in data and 'lines' in data:
                            # Use proper journal entry creation with header and lines
                            entry_result = supabase_client.table('journal_entries').insert(data['header']).execute()
                            if entry_result.data:
                                entry_id = entry_result.data[0]['id']
                                # Add entry_id to each line and insert
                                for line in data['lines']:
                                    line['journal_entry_id'] = entry_id
                                lines_result = supabase_client.table('journal_entry_lines').insert(data['lines']).execute()
                                if not lines_result.data:
                                    # Rollback entry if lines failed
                                    supabase_client.table('journal_entries').delete().eq('id', entry_id).execute()
                                    raise Exception("Failed to insert journal entry lines")
                        else:
                            # Standard table insert
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


class UnifiedAccountingSystem:
    """
    Unified Accounting System that combines all functionality:
    - Core accounting operations with authentication
    - Offline support with automatic sync
    - Advanced financial features and reporting
    - Period closing and audit trails
    """

    def generate_cash_flow_breakdown(self, start_date: str, end_date: str) -> dict:
        """
        Generate a simple cash flow statement breakdown.
        This is a basic direct method (indirect method would require more logic).
        """
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_chart_of_accounts(active_only=False)
        account_types = {acc['name']: acc['type'].lower() for acc in accounts}

        # Categorize accounts for cash flow
        cash_accounts = [acc['name'] for acc in accounts if acc['type'].lower() == 'asset' and 'cash' in acc['name'].lower()]
        operating_activities = []
        investing_activities = []
        financing_activities = []

        net_operating = 0.0
        net_investing = 0.0
        net_financing = 0.0

        # Use normalized account names for type lookups
        for entry in entries:
            debit = self._normalize_account_name(entry.get('debit_account', ''))
            credit = self._normalize_account_name(entry.get('credit_account', ''))
            amount = float(entry.get('amount', 0))

            # Operating: revenue/expense accounts
            if account_types.get(debit) == 'expense' or account_types.get(credit) == 'revenue':
                operating_activities.append((f"{debit} / {credit}", amount))
                net_operating += amount if account_types.get(debit) == 'expense' else -amount
            # Investing: fixed assets
            elif account_types.get(debit) == 'asset' and any(x in debit.lower() for x in ['equipment', 'building', 'vehicle']):
                investing_activities.append((debit, amount))
                net_investing -= amount
            # Financing: equity or liability
            elif account_types.get(debit) == 'equity' or account_types.get(credit) == 'liability':
                financing_activities.append((f"{debit} / {credit}", amount))
                net_financing += amount if account_types.get(debit) == 'equity' else -amount

        net_cash_flow = net_operating + net_investing + net_financing

        return {
            "operating activities": operating_activities,
            "investing activities": investing_activities,
            "financing activities": financing_activities,
            "net_operating": net_operating,
            "net_investing": net_investing,
            "net_financing": net_financing,
            "net_cash_flow": net_cash_flow
        }

    def __init__(self, auth_manager: AuthManager):
        self.logger = logging.getLogger(__name__)
        
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        # Core components
        self.auth_manager = auth_manager
        self.db_manager = auth_manager.db_manager
        self.current_organization_id = None
        self.current_user_id = self._get_current_user_id() if auth_manager else None
        
        # Initialize Supabase client for direct operations
        DatabaseConfig.validate_config()
        self.supabase = create_client(
            DatabaseConfig.SUPABASE_URL,
            DatabaseConfig.SUPABASE_ANON_KEY
        )
        
        # Offline support
        self.offline_cache = OfflineCache()
        self.is_online = self._test_connectivity()
        
        # Start background connectivity monitoring
        self._start_connectivity_monitor()
        
        self.logger.info("✅ Unified Accounting System initialized")
        
    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from auth manager"""
        if not self.auth_manager:
            return None
        user = self.auth_manager.get_current_user()
        return user['id'] if user else None

    def set_organization(self, org_id: str) -> bool:
        """Set the current organization for operations."""
        if not self.auth_manager.can_read_accounting_data(org_id):
            self.logger.warning(f"User lacks permission to access organization {org_id}")
            return False
        
        self.current_organization_id = org_id
        self.logger.info(f"📁 Organization context set to: {org_id}")
        
        # Refresh cache for new organization
        if self.is_online:
            self._refresh_cache()
            
        return True
    
    def _test_connectivity(self) -> bool:
        """Test if Supabase is reachable"""
        try:
            self.supabase.table('organizations').select('id').limit(1).execute()
            return True
        except Exception as e:
            self.logger.warning(f"🔌 Connectivity test failed: {e}")
            return False
    
    def _start_connectivity_monitor(self):
        """Monitor connectivity and auto-sync when back online"""
        def monitor_loop():
            while True:
                import time
                time.sleep(30)  # Check every 30 seconds
                
                was_online = self.is_online
                self.is_online = self._test_connectivity()
                
                if not was_online and self.is_online:
                    # Just came back online - sync pending operations
                    self.logger.info("🌐 Back online - syncing pending operations...")
                    synced = self.offline_cache.sync_pending_operations(self.supabase)
                    self.logger.info(f"✅ Synced {synced} pending operations")
                    
                    # Refresh cache from server
                    self._refresh_cache()
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _refresh_cache(self):
        """Refresh local cache from Supabase"""
        if not self.is_online or not self.current_organization_id:
            return
        
        try:
            # Set database context for RLS
            self._set_database_context()
            
            # Cache accounts
            accounts_result = self.supabase.table('accounts').select('*').execute()
            if accounts_result.data:
                self.offline_cache.cache_data('accounts', accounts_result.data, self.current_organization_id)
            
            # Cache journal entries
            entries_result = self.supabase.table('journal_entries').select('*').execute()
            if entries_result.data:
                self.offline_cache.cache_data('journal_entries', entries_result.data, self.current_organization_id)
            
            self.logger.info("✅ Cache refreshed from Supabase")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh cache: {e}")
    
    def _set_database_context(self):
        """Set PostgreSQL context for RLS policies"""
        if not self.is_online or not self.current_user_id or not self.current_organization_id:
            return
        
        try:
            # Get the actual user role from auth manager
            role = 'accountant'  # Default fallback
            if self.auth_manager:
                user_role = self.auth_manager.get_user_role_in_organization(self.current_organization_id)
                if user_role:
                    role = user_role
            
            self.supabase.rpc('set_app_context', {
                'user_id': self.current_user_id,
                'organization_id': self.current_organization_id,
                'role': role
            }).execute()
            
            self.logger.info(f"✅ Database context set for user {self.current_user_id}, org {self.current_organization_id}, role {role}")
            
        except Exception as e:
            self.logger.error(f"Failed to set database context: {e}")

    # ================================
    # CHART OF ACCOUNTS OPERATIONS
    # ================================
    
    def get_chart_of_accounts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get chart of accounts with a cache-first strategy."""
        if not self.current_organization_id:
            return []

        # 1. Load from cache first for speed
        cached_accounts = self.offline_cache.get_cached_data('accounts', self.current_organization_id)
        if cached_accounts:
            self.logger.info(f"Loaded {len(cached_accounts)} accounts from cache.")
            # In the background, refresh the cache from the database
            threading.Thread(target=self._refresh_cache, daemon=True).start()
            return self._process_accounts(cached_accounts, active_only)

        # 2. If cache is empty, fetch from the database
        if self.is_online:
            try:
                self._set_database_context()
                result = self.db_manager.get_accounts(self.current_organization_id, active_only)
                if result:
                    self.offline_cache.cache_data('accounts', result, self.current_organization_id)
                    return self._process_accounts(result, active_only)
            except Exception as e:
                self.logger.error(f"Online accounts fetch failed: {e}")

        return []

    def get_chart_of_accounts_fresh(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get chart of accounts with fresh data (bypassing cache for consistency)."""
        if not self.current_organization_id:
            return []

        # Always try to get fresh data from database first
        if self.is_online:
            try:
                self._set_database_context()
                result = self.db_manager.get_accounts(self.current_organization_id, active_only)
                if result:
                    # Update cache with fresh data
                    self.offline_cache.cache_data('accounts', result, self.current_organization_id)
                    self.logger.info(f"Loaded {len(result)} fresh accounts from database.")
                    return self._process_accounts(result, active_only)
            except Exception as e:
                self.logger.error(f"Fresh accounts fetch failed: {e}")

        # Fallback to cache if online fetch fails
        cached_accounts = self.offline_cache.get_cached_data('accounts', self.current_organization_id)
        if cached_accounts:
            self.logger.info(f"Fallback: Loaded {len(cached_accounts)} accounts from cache.")
            return self._process_accounts(cached_accounts, active_only)

        return []

    def _process_accounts(self, accounts: List[Dict], active_only: bool) -> List[Dict]:
        """Helper to filter and enhance accounts."""
        if active_only:
            accounts = [acc for acc in accounts if acc.get('is_active', True)]
        return self._enhance_accounts_with_hierarchy(accounts)
    
    def _enhance_accounts_with_hierarchy(self, accounts: List[Dict]) -> List[Dict]:
        """Add calculated hierarchy fields to account records"""
        if not accounts:
            return accounts
        
        # Create a mapping for parent lookups and hierarchy analysis
        account_by_id = {acc['id']: acc for acc in accounts}
        children_by_parent = {}
        
        # Build children mapping
        for acc in accounts:
            parent_id = acc.get('parent_id')
            if parent_id:
                if parent_id not in children_by_parent:
                    children_by_parent[parent_id] = []
                children_by_parent[parent_id].append(acc)
        
        def calculate_level(acc, visited=None):
            """Calculate hierarchy level (1-4)"""
            if visited is None:
                visited = set()
            acc_id = acc['id']
            if acc_id in visited:  # Prevent infinite loops
                return 1
            visited.add(acc_id)
            parent_id = acc.get('parent_id')
            if not parent_id or parent_id not in account_by_id:
                return 1  # Root level
            parent_acc = account_by_id[parent_id]
            return calculate_level(parent_acc, visited) + 1
        
        def get_inherited_group(acc, visited=None):
            """Get group inherited from parent account"""
            if visited is None:
                visited = set()
            acc_id = acc['id']
            if acc_id in visited:  # Prevent infinite loops
                return None
            visited.add(acc_id)
            # Check if account has direct group assignment
            direct_group = acc.get('group')
            if direct_group:
                return direct_group
            # Check parent inheritance
            parent_id = acc.get('parent_id')
            if parent_id and parent_id in account_by_id:
                parent_acc = account_by_id[parent_id]
                return get_inherited_group(parent_acc, visited)
            return None
        
        def is_postable(acc):
            """Determine if account is postable based on hierarchy rules"""
            acc_id = acc['id']
            level = calculate_level(acc)
            has_children = acc_id in children_by_parent
            # Rules for postability:
            # 1. If it's a leaf account (no children), it's postable
            # 2. For level 3+ accounts without children are postable
            if not has_children:
                return True
            elif level >= 3:
                # Level 3+ with children - depends on business rules
                return False
            else:
                # Level 1-2 with children are definitely header accounts
                return False
        
        def get_parent_code(acc):
            """Get parent account code"""
            parent_id = acc.get('parent_id')
            if parent_id and parent_id in account_by_id:
                return account_by_id[parent_id].get('code', '')
            return ''
        
        # Enhance each account with calculated fields
        enhanced_accounts = []
        for acc in accounts:
            enhanced_acc = acc.copy()  # Don't modify original
            enhanced_acc['level'] = calculate_level(acc)
            enhanced_acc['is_postable'] = is_postable(acc)
            enhanced_acc['parent_code'] = get_parent_code(acc)
            # Add group data with inheritance
            direct_group = acc.get('group')
            inherited_group = get_inherited_group(acc)
            enhanced_acc['group'] = direct_group or inherited_group
            enhanced_acc['group_inherited'] = direct_group is None and inherited_group is not None
            # Add compatibility field mappings for UI
            enhanced_acc['type'] = acc.get('account_type', acc.get('type', ''))  # Map account_type to type for UI compatibility
            enhanced_accounts.append(enhanced_acc)
        return enhanced_accounts
    
    def get_accounts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Alias for get_chart_of_accounts"""
        return self.get_chart_of_accounts(active_only)
    
    def get_all_accounts(self) -> List[Tuple]:
        """Get all accounts in tuple format for compatibility with 4-level hierarchy"""
        accounts = self.get_chart_of_accounts(active_only=False)
        
        # Create a mapping for parent lookups and hierarchy analysis
        account_by_id = {acc['id']: acc for acc in accounts}
        children_by_parent = {}
        
        # Build children mapping
        for acc in accounts:
            parent_id = acc.get('parent_id')
            if parent_id:
                if parent_id not in children_by_parent:
                    children_by_parent[parent_id] = []
                children_by_parent[parent_id].append(acc)
        
        def get_parent_code(parent_id):
            """Get parent account code from parent_id"""
            if parent_id and parent_id in account_by_id:
                return account_by_id[parent_id].get('code', '')
            return ''
        
        def calculate_level(acc, visited=None):
            """Calculate hierarchy level (1-4)"""
            if visited is None:
                visited = set()
            
            acc_id = acc['id']
            if acc_id in visited:  # Prevent infinite loops
                return 1
            visited.add(acc_id)
            
            parent_id = acc.get('parent_id')
            if not parent_id or parent_id not in account_by_id:
                return 1  # Root level
            
            parent_acc = account_by_id[parent_id]
            return calculate_level(parent_acc, visited) + 1
        
        def is_postable(acc):
            """
            Determine if account is postable based on hierarchy rules:
            - Level 4 accounts (leaf accounts) are typically postable
            - Accounts with no children are postable
            - Parent accounts (with children) are typically not postable (header accounts)
            """
            acc_id = acc['id']
            level = calculate_level(acc)
            has_children = acc_id in children_by_parent
            
            # Rules for postability:
            # 1. If it's a leaf account (no children), it's postable
            # 2. If it's level 4, it's likely postable even if it has children
            # 3. For business logic: Level 3+ accounts without children are postable
            if not has_children:
                return True
            elif level >= 3:
                # Level 3+ with children - depends on business rules
                # For most accounting systems, having children makes it non-postable
                return False
            else:
                # Level 1-2 with children are definitely header accounts
                return False
        
        result = []
        for acc in accounts:
            # Convert to tuple format: (name, type, code, parent_code, level, is_postable, description)
            parent_code = get_parent_code(acc.get('parent_id'))
            level = calculate_level(acc)
            postable = is_postable(acc)
            
            result.append((
                acc.get('name', ''),
                acc.get('account_type', ''),
                acc.get('code', ''),
                parent_code,
                level,
                postable,
                acc.get('description', '')
            ))
        
        return result
    
    def get_postable_accounts(self) -> List[Tuple]:
        """Get only postable accounts (leaf accounts that can have transactions)"""
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc[5]]  # is_postable is index 5
    
    def get_accounts_by_level(self, level: int = 1) -> List[Tuple]:
        """Get accounts by hierarchy level"""
        all_accounts = self.get_all_accounts()
        return [acc for acc in all_accounts if acc[4] == level]  # level is index 4
    
    def create_account(self, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new account."""
        if not self.current_organization_id:
            raise ValueError("No organization context set")
        
        if not self.auth_manager.can_create_accounts(self.current_organization_id):
            raise PermissionError("Insufficient permissions to create accounts")
        
        # Extract group data before creating account
        group = account_data.pop('group', None)
        
        # Add organization context
        account_data['organization_id'] = self.current_organization_id
        account_data['created_by'] = self.current_user_id
        
        # Convert account_type to lowercase to match database enum
        if 'account_type' in account_data:
            account_data['account_type'] = account_data['account_type'].lower()
        
        # Try online first
        if self.is_online:
            try:
                print(f"Debug: UnifiedAccountingSystem.create_account attempting online creation")
                self._set_database_context()
                result = self.db_manager.create_account(account_data)
                print(f"Debug: UnifiedAccountingSystem.create_account online result: {result}")
                if result:
                    print(f"Debug: Online creation successful, returning: {result}")
                    
                    # Save group if provided
                    if group and group != 'None':
                        account_id = result.get('id')
                        if account_id:
                            self.save_account_group(account_id, group)
                    
                    return result
                else:
                    print(f"Debug: Online creation returned None, falling back to queue")
            except Exception as e:
                print(f"Debug: UnifiedAccountingSystem.create_account online exception: {e}")
                self.logger.error(f"Online account creation failed: {e}")
                self.is_online = False
        
        # Queue for later sync if offline
        # Store group data in the account_data for offline sync
        if group and group != 'None':
            account_data['group'] = group
        
        self.offline_cache.queue_operation(
            'INSERT', 'accounts', account_data, 
            self.current_organization_id, self.current_user_id
        )
        
        # Return the account data for immediate UI update
        account_data['id'] = str(uuid.uuid4())
        account_data['queued'] = True
        return account_data
    
    def update_account(self, account_id: int, updates: Dict[str, Any]) -> bool:
        """Update account."""
        if not self.current_organization_id:
            return False
        
        if not self.auth_manager.can_edit_accounts(self.current_organization_id):
            raise PermissionError("Insufficient permissions to update accounts")
        
        print(f"🔍 DEBUG: update_account - account_id: {account_id}, full_updates: {updates}")
        
        # Check if group is being updated
        group_updated = 'group' in updates
        new_group = updates.get('group')
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                # Include group in the main update - don't separate it
                success = self.db_manager.update_account(account_id, updates)
                print(f"🔍 DEBUG: db_manager.update_account result: {success}")
                
                if success:
                    # If group was updated, update child accounts' inherited groups
                    # We do this regardless of whether the group value changed, because
                    # child accounts might not have the group value stored in the database
                    if group_updated and new_group:
                        print(f"🔍 DEBUG: Group field updated to '{new_group}', updating child accounts")
                        self._update_child_accounts_inherited_groups(account_id, new_group)
                    
                    # Force cache refresh to reflect changes
                    self._refresh_cache()
                
                return success
            except Exception as e:
                print(f"🔍 DEBUG: update_account exception: {e}")
                self.logger.error(f"Online account update failed: {e}")
                self.is_online = False
        
        # Queue for later sync if offline
        updates['id'] = account_id
        
        self.offline_cache.queue_operation(
            'UPDATE', 'accounts', updates,
            self.current_organization_id, self.current_user_id
        )
        return True
    
    def _update_child_accounts_inherited_groups(self, parent_account_id: int, new_parent_group: str):
        """Update inherited groups for all child accounts when parent group changes."""
        try:
            print(f"🔍 DEBUG: _update_child_accounts_inherited_groups - parent_id: {parent_account_id}, new_group: {new_parent_group}")
            
            # Get all accounts to find children
            all_accounts = self.get_chart_of_accounts(active_only=False)
            account_by_id = {acc['id']: acc for acc in all_accounts}
            
            # Find all child accounts (direct and indirect)
            children_to_update = []
            
            def find_children(parent_id, visited=None):
                """Recursively find all children of a parent account."""
                if visited is None:
                    visited = set()
                if parent_id in visited:
                    return  # Prevent infinite loops
                visited.add(parent_id)
                
                for acc in all_accounts:
                    if acc.get('parent_id') == parent_id:
                        # Check if the child account has a direct group assignment
                        direct_group = acc.get('group')
                        if not direct_group:  # No direct group assignment - should inherit
                            children_to_update.append(acc)
                            print(f"🔍 DEBUG: Found child account to update: {acc['name']} (ID: {acc['id']}) - no direct group")
                        else:
                            print(f"🔍 DEBUG: Skipping child account {acc['name']} - has direct group assignment: {direct_group}")
                        
                        # Recursively find grandchildren regardless of whether this child has a direct group
                        find_children(acc['id'], visited)
            
            find_children(parent_account_id)
            
            print(f"🔍 DEBUG: Found {len(children_to_update)} child accounts to update")
            
            # Update each child account's group in the database
            for child_account in children_to_update:
                child_id = child_account['id']
                try:
                    # Update the group field directly in the database
                    update_data = {'group': new_parent_group}
                    success = self.db_manager.update_account(child_id, update_data)
                    if success:
                        print(f"🔍 DEBUG: Updated child account '{child_account['name']}' group to '{new_parent_group}'")
                    else:
                        print(f"🔍 DEBUG: Failed to update child account '{child_account['name']}' group")
                except Exception as e:
                    print(f"🔍 DEBUG: Error updating child account '{child_account['name']}': {e}")
                    
        except Exception as e:
            print(f"🔍 DEBUG: Error in _update_child_accounts_inherited_groups: {e}")
            self.logger.error(f"Error updating child accounts' inherited groups: {e}")
    
    def delete_account(self, account_identifier: Union[int, str]) -> bool:
        """Delete account by ID or name (soft delete)."""
        if not self.current_organization_id:
            return False
        
        if not self.auth_manager.can_edit_accounts(self.current_organization_id):
            raise PermissionError("Insufficient permissions to delete accounts")
        
        # If identifier is a string (name), find the account ID
        account_id = account_identifier
        if isinstance(account_identifier, str):
            accounts = self.get_chart_of_accounts(active_only=False)
            account = next((acc for acc in accounts if acc['name'] == account_identifier), None)
            if not account:
                self.logger.error(f"Account '{account_identifier}' not found")
                return False
            account_id = account['id']
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                return self.db_manager.delete_account(account_id)
            except Exception as e:
                self.logger.error(f"Online account deletion failed: {e}")
                self.is_online = False
        
        # Queue for later sync if offline
        delete_data = {'id': account_id, 'is_active': False}
        self.offline_cache.queue_operation(
            'UPDATE', 'accounts', delete_data,
            self.current_organization_id, self.current_user_id
        )
        return True

    def is_account_postable(self, account_name_or_code: str) -> bool:
        """Check if account is postable"""
        accounts = self.get_chart_of_accounts(active_only=False)
        for acc in accounts:
            if acc['name'] == account_name_or_code or acc.get('code') == account_name_or_code:
                return acc.get('is_postable', True)
        return True  # Default to postable
    
    def resolve_account(self, account_input: str) -> str:
        """Resolve account name from input with fuzzy matching"""
        accounts = self.get_chart_of_accounts(active_only=False)
        
        # Try exact match first
        for acc in accounts:
            if acc['name'] == account_input or acc.get('code') == account_input:
                return acc['name']
        
        # Try partial match
        account_input_lower = account_input.lower()
        best_match = None
        best_score = 0
        
        for acc in accounts:
            name_lower = acc['name'].lower()
            score = 0
            
            # Scoring algorithm
            if name_lower.startswith(account_input_lower):
                score = 10
            elif f" {account_input_lower}" in name_lower:
                score = 8
            elif account_input_lower in name_lower:
                score = 5
            elif name_lower.endswith(account_input_lower):
                score = 3
            
            if score > best_score:
                best_score = score
                best_match = acc['name']
        
        return best_match if best_match else account_input

    # ================================
    # JOURNAL ENTRY OPERATIONS
    # ================================
    
    def get_journal_entries(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get journal entries with a cache-first strategy."""
        if not self.current_organization_id:
            return []

        # 1. Load from cache first
        cached_entries = self.offline_cache.get_cached_data('journal_entries', self.current_organization_id)
        if cached_entries:
            self.logger.info(f"Loaded {len(cached_entries)} journal entries from cache.")
            threading.Thread(target=self._refresh_cache, daemon=True).start()
            return self._filter_entries(cached_entries, start_date, end_date)

        # 2. If cache is empty, fetch from the database
        if self.is_online:
            try:
                self._set_database_context()
                raw_result = self.db_manager.get_journal_entries(
                    self.current_organization_id, start_date, end_date
                )
                if raw_result:
                    from .data_transformer import data_transformer
                    app_entries = data_transformer.transform_journal_entries_list(raw_result)
                    self.offline_cache.cache_data('journal_entries', raw_result, self.current_organization_id)
                    return app_entries
            except Exception as e:
                self.logger.error(f"Online journal entries fetch failed: {e}")

        return []

    def _filter_entries(self, entries: List[Dict], start_date: Optional[str], end_date: Optional[str]) -> List[Dict]:
        """Filter journal entries by date."""
        if not start_date and not end_date:
            return entries

        filtered = []
        for entry in entries:
            entry_date = entry.get('date', '')
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            filtered.append(entry)
        return filtered
    
    def get_recent_journal_entries(self, limit: int = 20) -> List[Dict]:
        """Get recent journal entries in UI-friendly format"""
        entries = self.get_journal_entries()
        
        # Entries are already in application format, just sort and limit
        sorted_entries = sorted(entries, key=lambda x: x.get('date', ''), reverse=True)
        return sorted_entries[:limit]
    
    def add_journal_entry(self, entry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add journal entry with proper data transformation."""
        print("🔥 CRITICAL DEBUG: UnifiedAccountingSystem.add_journal_entry() called!")
        print(f"🔥 Entry data received: {entry_data}")
        try:
            self.logger.info(f"🔄 Starting journal entry creation: {entry_data}")
            
            # Check organization context
            if not self.current_organization_id:
                self.logger.error("❌ No organization context set")
                raise ValueError("No organization context set")
            
            self.logger.info(f"✅ Organization context: {self.current_organization_id}")
            
            # Check permissions
            if not self.auth_manager.can_create_journal_entries(self.current_organization_id):
                self.logger.error("❌ Insufficient permissions")
                raise PermissionError("Insufficient permissions to create journal entries")
            
            self.logger.info("✅ Permissions validated")
            
            # Transform frontend data to proper database format
            try:
                self.logger.info("🔄 Starting data transformation...")
                journal_entry_data, journal_lines = self._transform_journal_entry_data(entry_data)
                self.logger.info(f"✅ Data transformation successful")
                self.logger.debug(f"Transformed data: {journal_entry_data}")
                self.logger.debug(f"Transformed lines: {journal_lines}")
            except Exception as e:
                self.logger.error(f"❌ Data transformation failed: {e}")
                raise ValueError(f"Invalid journal entry data: {e}")
            
            # Try online first
            if self.is_online:
                try:
                    self.logger.info("🌐 Attempting online creation...")
                    self._set_database_context()
                    self.logger.info(f"🔄 Creating journal entry online: {journal_entry_data.get('entry_number', 'N/A')}")
                    
                    result = self.db_manager.create_journal_entry(journal_entry_data, journal_lines)
                    if result:
                        self.logger.info(f"✅ Journal entry created successfully online: {result.get('entry_number', 'N/A')}")
                        return result
                    else:
                        self.logger.error("❌ Online creation returned None - falling back to offline")
                        
                except Exception as e:
                    self.logger.error(f"❌ Online journal entry creation failed: {e}")
                    # Log more details for debugging
                    self.logger.error(f"Organization ID: {self.current_organization_id}")
                    self.logger.error(f"User ID: {self.current_user_id}")
                    self.is_online = False
                    self.logger.info("📱 Switching to offline mode")
            else:
                self.logger.info("📱 System is offline, queueing entry")
            
            # Queue for later sync if offline
            try:
                self.logger.info("🔄 Preparing offline entry...")
                print(f"🔄 DEBUG: Preparing offline entry...")
                
                offline_entry = {
                    'header': journal_entry_data,
                    'lines': journal_lines
                }
                
                self.logger.info(f"🔄 Queueing operation for offline sync...")
                print(f"🔄 DEBUG: About to queue operation...")
                print(f"   Organization ID: {self.current_organization_id}")
                print(f"   User ID: {self.current_user_id}")
                print(f"   Offline entry keys: {list(offline_entry.keys())}")
                
                self.offline_cache.queue_operation(
                    'INSERT', 'journal_entries', offline_entry,
                    self.current_organization_id, self.current_user_id
                )
                
                print(f"✅ DEBUG: Operation queued successfully!")
                self.logger.info("✅ Entry queued for sync")
                
                # Return the entry data for immediate UI update
                journal_entry_data['id'] = str(uuid.uuid4())
                journal_entry_data['queued'] = True
                journal_entry_data['journal_entry_lines'] = journal_lines
                
                print(f"✅ DEBUG: Returning offline entry with ID: {journal_entry_data.get('id')}")
                self.logger.info(f"✅ Returning offline entry: {journal_entry_data.get('entry_number', 'N/A')}")
                return journal_entry_data
                
            except Exception as e:
                print(f"❌ DEBUG: Failed to queue offline entry: {e}")
                print(f"   Exception type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
                self.logger.error(f"❌ Failed to queue offline entry: {e}")
                raise ValueError(f"Failed to queue journal entry: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ Complete journal entry creation failed: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception args: {e.args}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _transform_journal_entry_data(self, entry_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Transform frontend journal entry data to database format."""
        # Extract frontend data
        entry_date = entry_data.get('date', '')
        description = entry_data.get('description', '').strip()
        debit_account_name = entry_data.get('debit_account', '').strip()
        credit_account_name = entry_data.get('credit_account', '').strip()
        amount = entry_data.get('amount', '')
        
        # Validation
        if not all([entry_date, description, debit_account_name, credit_account_name, amount]):
            raise ValueError("Missing required fields: date, description, debit_account, credit_account, amount")
        
        # Parse and validate amount
        try:
            amount_decimal = float(amount)
            if amount_decimal <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount: {amount}")
        
        # Resolve account names to IDs
        debit_account_id = self._resolve_account_name_to_id(debit_account_name)
        credit_account_id = self._resolve_account_name_to_id(credit_account_name)
        
        if not debit_account_id:
            raise ValueError(f"Debit account not found: {debit_account_name}")
        if not credit_account_id:
            raise ValueError(f"Credit account not found: {credit_account_name}")
        
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and credit accounts cannot be the same")
        
        # Generate entry number
        entry_number = self._generate_journal_entry_number()
        
        # Create journal entry header
        journal_entry_data = {
            'organization_id': self.current_organization_id,
            'entry_number': entry_number,
            'entry_date': entry_date,
            'description': description,
            'reference': entry_data.get('reference', ''),
            'total_amount': amount_decimal,
            'created_by': self.current_user_id
        }
        
        # Create journal entry lines (double-entry bookkeeping)
        journal_lines = [
            {
                'account_id': debit_account_id,
                'description': f"Debit: {description}",
                'debit_amount': amount_decimal,
                'credit_amount': 0,
                'line_order': 1
            },
            {
                'account_id': credit_account_id,
                'description': f"Credit: {description}",
                'debit_amount': 0,
                'credit_amount': amount_decimal,
                'line_order': 2
            }
        ]
        
        self.logger.info(f"🔄 Transformed journal entry: {entry_number} - {description} (${amount_decimal})")
        return journal_entry_data, journal_lines
    
    def _resolve_account_name_to_id(self, account_name: str) -> Optional[int]:
        """Resolve account name to database ID."""
        try:
            self.logger.info(f"🔍 Resolving account name: '{account_name}'")
            
            # Get accounts from cache or database
            self.logger.info("🔄 Fetching chart of accounts...")
            accounts = self.get_chart_of_accounts(active_only=False)
            self.logger.info(f"✅ Retrieved {len(accounts)} accounts from chart of accounts")
            
            if not accounts:
                self.logger.warning("⚠️ No accounts found in chart of accounts!")
                return None
            
            # Log first few accounts for debugging
            self.logger.debug("📋 Available accounts:")
            for i, account in enumerate(accounts[:5]):  # Show first 5 accounts
                self.logger.debug(f"  {i+1}. ID: {account.get('id')}, Name: '{account.get('name', 'N/A')}', Code: '{account.get('code', 'N/A')}'")
            if len(accounts) > 5:
                self.logger.debug(f"  ... and {len(accounts) - 5} more accounts")
            
            # Try exact name match first
            self.logger.info(f"🔍 Trying exact name match for: '{account_name}'")
            for account in accounts:
                if account.get('name', '').strip() == account_name.strip():
                    account_id = account.get('id')
                    self.logger.info(f"✅ Exact match found: '{account_name}' → ID: {account_id}")
                    return account_id
            
            self.logger.info(f"❌ No exact match found for: '{account_name}'")
            
            # Try partial match (handle "code - name" format)
            self.logger.info(f"🔍 Trying partial/code-name match for: '{account_name}'")
            for account in accounts:
                account_full_name = account.get('name', '')
                if ' - ' in account_full_name:
                    _, name_part = account_full_name.split(' - ', 1)
                    if name_part.strip() == account_name.strip():
                        account_id = account.get('id')
                        self.logger.info(f"✅ Code-name match found: '{account_name}' → '{account_full_name}' → ID: {account_id}")
                        return account_id
                
                # Check if account name is in "code - name" format and match name part
                if ' - ' in account_name:
                    _, input_name_part = account_name.split(' - ', 1)
                    if input_name_part.strip() == account_full_name.strip():
                        account_id = account.get('id')
                        self.logger.info(f"✅ Reverse code-name match found: '{account_name}' → '{account_full_name}' → ID: {account_id}")
                        return account_id
            
            self.logger.info(f"❌ No partial match found for: '{account_name}'")
            
            # Try fuzzy matching as last resort
            self.logger.info(f"🔍 Trying fuzzy match for: '{account_name}'")
            account_name_lower = account_name.lower()
            for account in accounts:
                account_full_name = account.get('name', '').lower()
                if account_name_lower in account_full_name or account_full_name in account_name_lower:
                    account_id = account.get('id')
                    self.logger.warning(f"⚠️ Using fuzzy match for account: '{account_name}' → '{account.get('name')}' → ID: {account_id}")
                    return account_id
            
            self.logger.error(f"❌ No match found for account: '{account_name}' (tried exact, partial, and fuzzy matching)")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error resolving account name '{account_name}': {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _generate_journal_entry_number(self) -> str:
        """Generate unique journal entry number."""
        try:
            print(f"🔢 DEBUG: Generating entry number for org {self.current_organization_id}")
            
            # First try to get the latest entry number directly from database
            if self.is_online and self.db_manager:
                try:
                    print(f"🔢 DEBUG: Querying database for latest entry number...")
                    # Query database directly for latest entry number
                    result = self.db_manager.supabase.table('journal_entries')\
                        .select('entry_number')\
                        .eq('organization_id', self.current_organization_id)\
                        .order('entry_number', desc=True)\
                        .limit(1)\
                        .execute()
                    
                    print(f"🔢 DEBUG: Database query result: {result.data}")
                    
                    if result.data and len(result.data) > 0:
                        last_number = result.data[0].get('entry_number', 'JE-0000')
                        print(f"🔢 DEBUG: Found latest entry number: {last_number}")
                        
                        try:
                            # Extract numeric part from format like "JE-0001"
                            if '-' in last_number:
                                number_part = int(last_number.split('-')[-1])
                                next_number = number_part + 1
                            else:
                                next_number = 1
                        except (ValueError, IndexError):
                            next_number = 1
                    else:
                        print(f"🔢 DEBUG: No existing entries found, starting with 1")
                        next_number = 1
                        
                except Exception as db_error:
                    print(f"🔢 DEBUG: Database query failed: {db_error}")
                    # Fallback to checking cached entries
                    recent_entries = self.get_journal_entries()
                    if recent_entries:
                        last_entry = recent_entries[0]
                        last_number = last_entry.get('entry_number', 'JE-0000')
                        try:
                            if '-' in last_number:
                                number_part = int(last_number.split('-')[-1])
                                next_number = number_part + 1
                            else:
                                next_number = 1
                        except (ValueError, IndexError):
                            next_number = 1
                    else:
                        next_number = 1
            else:
                print(f"🔢 DEBUG: Offline mode, checking cached entries...")
                # Fallback to cached entries when offline
                recent_entries = self.get_journal_entries()
                if recent_entries:
                    last_entry = recent_entries[0]
                    last_number = last_entry.get('entry_number', 'JE-0000')
                    try:
                        if '-' in last_number:
                            number_part = int(last_number.split('-')[-1])
                            next_number = number_part + 1
                        else:
                            next_number = 1
                    except (ValueError, IndexError):
                        next_number = 1
                else:
                    next_number = 1
            
            generated_number = f"JE-{next_number:04d}"
            print(f"🔢 DEBUG: Generated entry number: {generated_number}")
            return generated_number
            
        except Exception as e:
            self.logger.error(f"Error generating entry number: {e}")
            print(f"🔢 DEBUG: Error generating entry number: {e}")
            # Fallback to timestamp-based number
            import time
            timestamp = int(time.time())
            fallback_number = f"JE-{timestamp % 10000:04d}"
            print(f"🔢 DEBUG: Using fallback timestamp-based number: {fallback_number}")
            return fallback_number
    
    def add_journal_entries_batch(self, entries: List[Dict]) -> int:
        """Add multiple journal entries"""
        successful = 0
        for entry in entries:
            try:
                result = self.add_journal_entry(entry)
                if result:
                    successful += 1
            except Exception as e:
                self.logger.error(f"Failed to add journal entry: {e}")
        return successful
    
    def add_journal_entries_with_progress(self, entries: List[Dict], progress_callback=None) -> int:
        """Add journal entries with progress callback"""
        successful = 0
        total = len(entries)
        
        for i, entry in enumerate(entries):
            try:
                result = self.add_journal_entry(entry)
                if result:
                    successful += 1
            except Exception as e:
                self.logger.error(f"Failed to add journal entry: {e}")
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return successful
    
    def clear_journal_entries(self) -> int:
        """Clear all journal entries (admin function)"""
        if not self.current_organization_id:
            return 0
        
        if not self.auth_manager.is_super_admin():
            raise PermissionError("Only super admins can clear journal entries")
        
        if self.is_online:
            try:
                self._set_database_context()
                # This should be restricted to admin users
                result = self.supabase.table('journal_entries').delete().neq('id', 'never-match').execute()
                self.logger.warning("⚠️ Cleared all journal entries from database")
                return len(result.data) if result.data else 0
            except Exception as e:
                self.logger.error(f"Failed to clear journal entries: {e}")
                return 0
        else:
            self.logger.warning("Cannot clear journal entries while offline")
            return 0

    # ================================
    # FINANCIAL CALCULATIONS
    # ================================
    
    def get_hierarchical_account_balances(self, start_date: Optional[str] = None, 
                                        end_date: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate account balances with hierarchical aggregation.
        Returns balances for ALL accounts (including parent accounts with aggregated child balances).
        """
        if not self.current_organization_id:
            print("No organization ID set")
            return {}
        
        # Get all accounts with hierarchy information
        accounts = self.get_chart_of_accounts(active_only=False)
        if not accounts:
            return {}
        
        # Build hierarchy mapping
        account_by_id = {acc['id']: acc for acc in accounts}
        children_by_parent = {}
        
        for acc in accounts:
            parent_id = acc.get('parent_id')
            if parent_id:
                if parent_id not in children_by_parent:
                    children_by_parent[parent_id] = []
                children_by_parent[parent_id].append(acc)
        
        # Get direct transaction balances for postable accounts
        direct_balances = self._get_direct_account_balances(start_date, end_date)
        
        # Calculate hierarchical balances (bottom-up aggregation)
        hierarchical_balances = {}
        
        def calculate_account_balance(account_id: int) -> Dict[str, Any]:
            """Recursively calculate account balance including child aggregation."""
            account = account_by_id.get(account_id)
            if not account:
                return {'debit_total': 0.0, 'credit_total': 0.0, 'net_balance': 0.0}
            
            account_name = account['name']
            
            # Start with direct balance for this account
            # Try to match by account name, and also by code + name format
            direct_balance = direct_balances.get(account_name, {'debit_total': 0.0, 'credit_total': 0.0})
            
            # If not found by name, try to find by code + name format
            if direct_balance['debit_total'] == 0.0 and direct_balance['credit_total'] == 0.0:
                account_code = account.get('code', '')
                if account_code:
                    code_name_format = f"{account_code} - {account_name}"
                    if code_name_format in direct_balances:
                        direct_balance = direct_balances[code_name_format]
            
            total_debit = direct_balance['debit_total']
            total_credit = direct_balance['credit_total']
            
            # Add aggregated balances from children
            children = children_by_parent.get(account_id, [])
            for child in children:
                child_balance = calculate_account_balance(child['id'])
                total_debit += child_balance['debit_total']
                total_credit += child_balance['credit_total']
            
            # Calculate net balance based on account type
            account_type = account.get('account_type', '').lower()
            net_balance = self._calculate_net_balance(total_debit, total_credit, account_type)
            
            balance_info = {
                'debit_total': total_debit,
                'credit_total': total_credit,
                'net_balance': net_balance,
                'has_children': bool(children),
                'child_count': len(children),
                'is_postable': account.get('is_postable', True),
                'level': account.get('level', 1)
            }
            
            hierarchical_balances[account_name] = balance_info
            return balance_info
        
        # Calculate balances for all accounts
        # First, process all accounts to ensure we get balances for leaf accounts with transactions
        for account in accounts:
            calculate_account_balance(account['id'])
        
        return hierarchical_balances
    
    def _get_direct_account_balances(self, start_date: Optional[str] = None, 
                                   end_date: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """Get direct transaction balances for accounts (no aggregation)."""
        entries = self.get_journal_entries(start_date, end_date)
        
        # Track debit and credit totals for each account
        account_debits = {}
        account_credits = {}
        
        for entry in entries:
            debit_account = entry.get('debit_account', '')
            credit_account = entry.get('credit_account', '')
            amount = float(entry.get('amount', 0))
            
            # Initialize accounts if not exists
            if debit_account not in account_debits:
                account_debits[debit_account] = 0.0
                account_credits[debit_account] = 0.0
            if credit_account not in account_debits:
                account_debits[credit_account] = 0.0
                account_credits[credit_account] = 0.0
            
            # Record debits and credits
            account_debits[debit_account] += amount
            account_credits[credit_account] += amount
        
        # Convert to expected format
        balances = {}
        all_accounts = set(account_debits.keys()) | set(account_credits.keys())
        
        for account_name in all_accounts:
            balances[account_name] = {
                'debit_total': account_debits.get(account_name, 0.0),
                'credit_total': account_credits.get(account_name, 0.0)
            }
        
        return balances
    
    def _calculate_net_balance(self, debit_total: float, credit_total: float, account_type: str) -> float:
        """Calculate net balance based on account type and normal balance."""
        if account_type in ['asset', 'expense']:
            # Assets and expenses have normal debit balance
            return debit_total - credit_total
        else:
            # Liabilities, equity, and revenue have normal credit balance
            return credit_total - debit_total

    def get_trial_balance(self, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Calculate trial balance with hierarchical aggregation."""
        hierarchical_balances = self.get_hierarchical_account_balances(start_date, end_date)
        accounts = self.get_chart_of_accounts(active_only=False)
        
        # Create account lookup for metadata
        account_lookup = {acc['name']: acc for acc in accounts}
        
        # Build trial balance result
        trial_balance = []
        total_debits = 0.0
        total_credits = 0.0
        
        for account_name, balance_info in hierarchical_balances.items():
            debit_total = balance_info['debit_total']
            credit_total = balance_info['credit_total']
            net_balance = balance_info['net_balance']
            
            # Only include POSTABLE accounts with non-zero balances
            if (balance_info['is_postable'] and 
                (debit_total > 0 or credit_total > 0 or abs(net_balance) >= 0.01)):
                
                account_info = account_lookup.get(account_name, {})
                
                # Calculate proper trial balance columns based on account type
                account_type = account_info.get('account_type', '').lower()
                
                # For trial balance, we need to show the balance in the correct column
                # Assets and Expenses have normal debit balance
                # Liabilities, Equity, and Revenue have normal credit balance
                if account_type in ['asset', 'expense']:
                    # Normal debit balance accounts
                    debit_balance = max(0, net_balance) if net_balance > 0 else 0
                    credit_balance = max(0, -net_balance) if net_balance < 0 else 0
                else:
                    # Normal credit balance accounts (liability, equity, revenue)
                    debit_balance = max(0, -net_balance) if net_balance < 0 else 0
                    credit_balance = max(0, net_balance) if net_balance > 0 else 0
                
                trial_balance.append({
                    'name': account_name,
                    'debit_balance': debit_balance,
                    'credit_balance': credit_balance,
                    'net_balance': net_balance,
                    'account_type': account_info.get('account_type', ''),
                    'code': account_info.get('code', ''),
                    'level': balance_info['level'],
                    'is_postable': balance_info['is_postable'],
                    'has_children': balance_info['has_children'],
                    'child_count': balance_info['child_count']
                })
                
                # Update totals for trial balance validation
                total_debits += debit_balance
                total_credits += credit_balance
        
        # Sort by account code for consistent display
        trial_balance.sort(key=lambda x: x.get('code', '') or x['name'])
        
        return trial_balance
    
    def get_ledger(self, account_name: str, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> List[Tuple]:
        """Get ledger entries for specific account"""
        entries = self.get_journal_entries(start_date, end_date)
        ledger_entries = []
        
        # Helper function to match account names (handles "code - name" format)
        def account_matches(journal_account, target_account_name):
            """Check if the journal account matches the target account name."""
            # Direct name match
            if journal_account == target_account_name:
                return True
            
            # Check if journal account is in "code - name" format
            if ' - ' in journal_account:
                parts = journal_account.split(' - ', 1)
                if len(parts) == 2:
                    j_code, j_name = parts
                    # Match by name (in case code is slightly different)
                    if j_name == target_account_name:
                        return True
            
            # Partial match for cases where formatting might be inconsistent
            if target_account_name in journal_account or journal_account in target_account_name:
                return True
                
            return False
        
        for entry in entries:
            date = entry.get('date', '')
            description = entry.get('description', '')
            debit_account = entry.get('debit_account', '')
            credit_account = entry.get('credit_account', '')
            amount = float(entry.get('amount', 0))
            
            if account_matches(debit_account, account_name) or account_matches(credit_account, account_name):
                # Format: (date, description, debit_account, credit_account, amount)
                ledger_entries.append((date, description, debit_account, credit_account, amount))
        
        return sorted(ledger_entries, key=lambda x: x[0])  # Sort by date

    # ================================
    # FINANCIAL REPORTING
    # ================================
    
    def _normalize_account_name(self, account_field: str) -> str:
        """Strip code prefix if present: '1120 - Cash at Bank' -> 'Cash at Bank'"""
        if not account_field:
            return ""
        if " - " in account_field:
            return account_field.split(" - ", 1)[1].strip()
        return account_field.strip()

    def generate_income_statement_breakdown(self, start_date: Optional[str] = None, 
                                          end_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate income statement with hierarchical balance aggregation."""
        try:
            # Use hierarchical balances for accurate reporting
            hierarchical_balances = self.get_hierarchical_account_balances(start_date, end_date)
            accounts = self.get_chart_of_accounts(active_only=False)
            
            # Create account type lookup and hierarchy mapping
            account_types = {acc['name']: acc.get('account_type', '').lower() for acc in accounts}
            account_by_id = {acc['id']: acc for acc in accounts}
            
            # Build hierarchical structure for income statement sections
            def build_income_hierarchy(account_type_filter):
                """Build hierarchical tree for income statement accounts."""
                tree = []
                
                # Get accounts of the specified type
                type_accounts = [acc for acc in accounts if acc.get('account_type', '').lower() == account_type_filter]
                
                # Build parent-child relationships
                for account in type_accounts:
                    if not account.get('parent_id'):  # Root accounts
                        node = self._build_account_node(account, type_accounts, hierarchical_balances, account_by_id)
                        if node:  # Only add if has balance or children
                            tree.append(node)
                
                return sorted(tree, key=lambda x: x['code'] or x['name'])
            
            # Build hierarchical trees for each section
            revenues_tree = build_income_hierarchy('revenue')
            expenses_tree = build_income_hierarchy('expense')
            
            # Separate COGS from other expenses
            cogs_tree = []
            operating_expenses_tree = []
            
            for node in expenses_tree:
                if 'cost' in node['name'].lower() or 'cogs' in node['name'].lower():
                    cogs_tree.append(node)
                else:
                    operating_expenses_tree.append(node)
            
            # Calculate totals
            total_revenue = self._calculate_tree_total(revenues_tree)
            total_cogs = self._calculate_tree_total(cogs_tree)
            total_expenses = self._calculate_tree_total(operating_expenses_tree)
            gross_profit = total_revenue - total_cogs
            net_income = gross_profit - total_expenses
            
            return {
                'revenues': revenues_tree,
                'cogs': cogs_tree,
                'expenses': operating_expenses_tree,
                'total_revenue': total_revenue,
                'total_cogs': total_cogs,
                'total_expenses': total_expenses,
                'gross_profit': gross_profit,
                'net_income': net_income,
                'period': f"{start_date or 'All Time'} to {end_date or 'Current'}",
                'is_hierarchical': True
            }
            
        except Exception as e:
            print(f"Error generating hierarchical income statement: {e}")
            # Fallback to original method
            return self._generate_income_statement_fallback(start_date, end_date)
    
    def _generate_income_statement_fallback(self, start_date: Optional[str] = None, 
                                          end_date: Optional[str] = None) -> Dict[str, Any]:
        """Fallback method for income statement generation."""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_chart_of_accounts(active_only=False)

        # Create account type lookup
        account_types = {acc['name']: acc.get('account_type', '').lower() for acc in accounts}

        # Track account balances
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
            debit_type = account_types.get(debit_account, '')
            credit_type = account_types.get(credit_account, '')
            
            # Assets, Expenses increase with debits
            if debit_type in ['asset', 'expense']:
                account_balances[debit_account] += amount
            else:
                account_balances[debit_account] -= amount
            
            # Liabilities, Equity, Revenue increase with credits  
            if credit_type in ['liability', 'equity', 'revenue', 'income']:
                account_balances[credit_account] += amount
            else:
                account_balances[credit_account] -= amount
        
        # Categorize accounts
        revenues = {}
        expenses = {}
        cogs = {}
        
        for account_name, balance in account_balances.items():
            account_type = account_types.get(account_name, '')
            
            if account_type in ['revenue', 'income']:
                revenues[account_name] = abs(balance)
            elif account_type == 'expense':
                if 'cost' in account_name.lower() or 'cogs' in account_name.lower():
                    cogs[account_name] = abs(balance)
                else:
                    expenses[account_name] = abs(balance)
        
        # Calculate totals
        total_revenue = sum(revenues.values())
        total_cogs = sum(cogs.values())
        total_expenses = sum(expenses.values())
        gross_profit = total_revenue - total_cogs
        net_income = gross_profit - total_expenses

        return {
            'revenues': sorted(revenues.items(), key=lambda x: x[0]),
            'cogs': sorted(cogs.items(), key=lambda x: x[0]),
            'expenses': sorted(expenses.items(), key=lambda x: x[0]),
            'total_revenue': total_revenue,
            'total_cogs': total_cogs,
            'total_expenses': total_expenses,
            'gross_profit': gross_profit,
            'net_income': net_income,
            'period': f"{start_date or 'All Time'} to {end_date or 'Current'}"
        }

    def generate_balance_sheet_breakdown(self, as_of_date: str) -> Dict:
        """Generate balance sheet with hierarchical balance aggregation and proper classifications."""
        try:
            # Use hierarchical balances for accurate reporting
            hierarchical_balances = self.get_hierarchical_account_balances(None, as_of_date)
            accounts = self.get_chart_of_accounts(active_only=False)
            classifications = self.get_account_classifications()
            
            # Create account type lookup and hierarchy mapping
            account_types = {acc['name']: acc.get('account_type', '').lower() for acc in accounts}
            account_by_id = {acc['id']: acc for acc in accounts}
            
            # Build hierarchical structure with classifications
            def build_classified_tree(account_type_filter):
                """Build hierarchical tree for specific account type with classifications."""
                tree = []
                
                # Get accounts of the specified type
                type_accounts = [acc for acc in accounts if acc.get('account_type', '').lower() == account_type_filter]
                
                # Group by classification
                classified_accounts = {
                    'current_asset': [],
                    'fixed_asset': [],
                    'other_asset': [],
                    'current_liability': [],
                    'long_term_liability': [],
                    'other_liability': []
                }
                
                for account in type_accounts:
                    classification = classifications.get(account['id'], '')
                    if classification in classified_accounts:
                        classified_accounts[classification].append(account)
                    else:
                        # Default classification based on account type
                        if account_type_filter == 'asset':
                            classified_accounts['other_asset'].append(account)
                        elif account_type_filter == 'liability':
                            classified_accounts['other_liability'].append(account)
                
                # Build trees for each classification
                for classification, accounts_list in classified_accounts.items():
                    if accounts_list:
                        # Build parent-child relationships for this classification
                        classification_tree = []
                        for account in accounts_list:
                            if not account.get('parent_id'):  # Root accounts
                                node = self._build_account_node(account, accounts_list, hierarchical_balances, account_by_id)
                                if node:  # Only add if has balance or children
                                    classification_tree.append(node)
                        
                        if classification_tree:
                            tree.append({
                                'classification': classification,
                                'name': self._get_classification_display_name(classification),
                                'accounts': sorted(classification_tree, key=lambda x: x['code'] or x['name'])
                            })
                
                return tree
            
            # Build classified trees
            assets_classified = build_classified_tree('asset')
            liabilities_classified = build_classified_tree('liability')
            equity_tree = self._build_simple_tree('equity', accounts, hierarchical_balances, account_by_id)
            
            # Calculate totals
            total_assets = sum(self._calculate_tree_total(section['accounts']) for section in assets_classified)
            total_liabilities = sum(self._calculate_tree_total(section['accounts']) for section in liabilities_classified)
            total_equity = self._calculate_tree_total(equity_tree)
            
            return {
                'assets': assets_classified,
                'liabilities': liabilities_classified,
                'equity': equity_tree,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'as_of_date': as_of_date,
                'is_hierarchical': True,
                'is_classified': True
            }
            
        except Exception as e:
            print(f"Error generating hierarchical balance sheet: {e}")
            # Fallback to original method
            return self._generate_balance_sheet_fallback(as_of_date)
    
    def _build_account_node(self, account, all_accounts, hierarchical_balances, account_by_id):
        """Build a hierarchical node for an account."""
        account_name = account['name']
        balance_info = hierarchical_balances.get(account_name, {})
        net_balance = balance_info.get('net_balance', 0.0)
        
        # Check if this account or its children have balances
        has_balance = abs(net_balance) >= 0.01
        has_children_with_balance = False
        
        # Find children
        children = []
        for child_account in all_accounts:
            if child_account.get('parent_id') == account['id']:
                child_node = self._build_account_node(child_account, all_accounts, hierarchical_balances, account_by_id)
                if child_node:
                    children.append(child_node)
                    has_children_with_balance = True
        
        # Only include if has balance or children with balance
        if has_balance or has_children_with_balance:
            return {
                'id': account['id'],
                'name': account_name,
                'code': account.get('code', ''),
                'level': account.get('level', 3),
                'balance': max(0, net_balance) if account.get('account_type', '').lower() in ['asset', 'liability'] else net_balance,
                'is_postable': account.get('is_postable', True),
                'has_children': len(children) > 0,
                'children': children,
                'account_type': account.get('account_type', '')
            }
        
        return None
    
    def _calculate_tree_total(self, tree):
        """Calculate total balance for a hierarchical tree.
        Only count leaf accounts (level 3) to avoid double-counting."""
        total = 0.0
        for node in tree:
            # If this is a leaf account (level 3) or has no children, count its balance
            if node.get('level', 3) == 3 or not node.get('children', []):
                total += node.get('balance', 0.0)
            else:
                # For parent accounts, only count children (avoid double-counting)
                total += self._calculate_tree_total(node.get('children', []))
        return total
    
    def _generate_balance_sheet_fallback(self, as_of_date: str) -> Dict:
        """Fallback method for balance sheet generation."""
        trial_balance = self.get_trial_balance(None, as_of_date)
        accounts = self.get_chart_of_accounts(active_only=False)

        # Create account type lookup
        account_types = {acc['name']: acc.get('account_type', '').lower() for acc in accounts}

        assets = {}
        liabilities = {}
        equity = {}

        for entry in trial_balance:
            account_name = entry['name']
            balance = entry.get('debit_total', 0.0) - entry.get('credit_total', 0.0)
            account_type = account_types.get(account_name, '')

            if account_type == 'asset':
                assets[account_name] = max(0, balance)
            elif account_type == 'liability':
                liabilities[account_name] = max(0, -balance)  # Liabilities have credit balance
            elif account_type == 'equity':
                equity[account_name] = -balance  # Equity has credit balance

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        total_equity = sum(equity.values())

        return {
            'assets': sorted(assets.items(), key=lambda x: x[0]),
            'liabilities': sorted(liabilities.items(), key=lambda x: x[0]),
            'equity': sorted(equity.items(), key=lambda x: x[0]),
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'as_of_date': as_of_date
        }

    def generate_statement_of_equity(self, start_date: str, end_date: str) -> Dict:
        """Generate statement of equity"""
        # Get beginning equity balance
        beginning_balance = self.get_trial_balance(None, start_date)
        accounts = self.get_chart_of_accounts(active_only=False)
        account_types = {acc['name']: acc.get('account_type', '').lower() for acc in accounts}

        # Sum balances for equity accounts
        beginning_equity = 0.0
        for entry in beginning_balance:
            account_name = entry.get('name', '')
            account_type = account_types.get(account_name, '').lower()
            if account_type == 'equity':
                # Use net_balance from the new trial balance format
                balance = entry.get('net_balance', 0.0)
                beginning_equity += balance

        # Get net income for the period
        income_statement = self.generate_income_statement_breakdown(start_date, end_date)
        net_income = income_statement.get('net_income', 0)

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

    # ================================
    # ADVANCED FEATURES INTEGRATION
    # ================================
    
    def get_financial_health_score(self, as_of_date: Optional[date] = None) -> Dict[str, Any]:
        """Calculate overall financial health score"""
        if as_of_date is None:
            as_of_date = date.today()
            
        score = 100  # Start with perfect score
        factors = []
        
        try:
            # Get balance sheet data
            balance_sheet = self.generate_balance_sheet_breakdown(as_of_date.strftime('%Y-%m-%d'))
            
            # Factor 1: Current Ratio (Assets / Liabilities)
            total_assets = balance_sheet.get('total_assets', 0)
            total_liabilities = balance_sheet.get('total_liabilities', 0)
            
            if total_liabilities > 0:
                current_ratio = total_assets / total_liabilities
                if current_ratio < 1.0:
                    score -= 25
                    factors.append('Assets below liabilities - liquidity concerns')
                elif current_ratio < 1.5:
                    score -= 10
                    factors.append('Low asset-to-liability ratio')
            
            # Factor 2: Profitability (recent period)
            year_start = as_of_date.replace(month=1, day=1)
            income_statement = self.generate_income_statement_breakdown(
                year_start.strftime('%Y-%m-%d'),
                as_of_date.strftime('%Y-%m-%d')
            )
            
            net_income = income_statement.get('net_income', 0)
            revenue_total = income_statement.get('revenue_total', 0)
            
            if net_income < 0:
                score -= 30
                factors.append('Negative net income')
            elif revenue_total > 0:
                profit_margin = (net_income / revenue_total) * 100
                if profit_margin < 5:
                    score -= 15
                    factors.append('Low profit margins (< 5%)')
            
            # Ensure score doesn't go below 0
            score = max(0, score)
            
            # Determine health category
            if score >= 80:
                health_category = 'Excellent'
            elif score >= 60:
                health_category = 'Good'
            elif score >= 40:
                health_category = 'Fair'
            else:
                health_category = 'Poor'
            
        except Exception as e:
            self.logger.error(f"Failed to calculate financial health score: {e}")
            return {'error': 'Unable to calculate financial health score'}
        
        return {
            'score': score,
            'category': health_category,
            'factors': factors,
            'last_calculated': datetime.now().isoformat(),
            'as_of_date': as_of_date.isoformat()
        }

    # ================================
    # UTILITY METHODS
    # ================================
    
    def refresh_connection(self):
        """Refresh database connection and cache"""
        self.is_online = self._test_connectivity()
        if self.is_online:
            self._refresh_cache()
        self.logger.info(f"🔄 Connection refreshed - Online: {self.is_online}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get offline sync status"""
        conn = sqlite3.connect(self.offline_cache.cache_db_path)
        cursor = conn.cursor()
        
        try:
            # Count pending operations
            cursor.execute('SELECT COUNT(*) FROM pending_operations')
            pending_count = cursor.fetchone()[0]
            
            # Count cached items
            cursor.execute('SELECT COUNT(*) FROM cached_accounts WHERE organization_id = ?', (self.current_organization_id,))
            cached_accounts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM cached_journal_entries WHERE organization_id = ?', (self.current_organization_id,))
            cached_entries = cursor.fetchone()[0]
            
            return {
                'is_online': self.is_online,
                'pending_operations': pending_count,
                'cached_accounts': cached_accounts,
                'cached_journal_entries': cached_entries,
                'organization_id': self.current_organization_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get sync status: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def force_sync(self) -> Dict[str, Any]:
        """Force sync all pending operations"""
        if not self.is_online:
            return {'error': 'Cannot sync while offline'}
        
        try:
            synced = self.offline_cache.sync_pending_operations(self.supabase)
            self._refresh_cache()
            
            return {
                'success': True,
                'synced_operations': synced,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Force sync failed: {e}")
            return {'error': str(e)}

    # ================================
    # COMPATIBILITY METHODS
    # ================================
    
    def get_journal_entries_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get journal entries by date range - alias for compatibility"""
        return self.get_journal_entries(start_date, end_date)
    
    def get_account_balance(self, account_name: str, as_of_date: Optional[str] = None) -> float:
        """Calculate account balance as of a specific date"""
        trial_balance = self.get_trial_balance(None, as_of_date)
        return trial_balance.get(account_name, 0.0)
    
    def seed_hierarchical_accounts(self):
        """Seed chart of accounts (placeholder for compatibility)"""
        self.logger.info("Chart of accounts seeding - use account creation methods instead")
        return True
    
    def force_reseed_hierarchical_accounts(self):
        """Force reseed accounts (placeholder for compatibility)"""
        self.logger.info("Force reseed - use account creation methods instead")
        return True
    
    # ================================
    # ACCOUNT CLASSIFICATIONS
    # ================================
    
    def get_account_classifications(self) -> Dict[int, str]:
        """Get all account classifications for the current organization."""
        if not self.current_organization_id:
            return {}
        
        try:
            if self.is_online:
                self._set_database_context()
                result = self.supabase.table('account_classifications').select(
                    'account_id, classification'
                ).eq('organization_id', self.current_organization_id).execute()
                
                classifications = {}
                for row in result.data:
                    classifications[row['account_id']] = row['classification']
                return classifications
            else:
                # Fallback to cached data
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get account classifications: {e}")
            return {}
    
    def save_account_classifications(self, classifications: Dict[int, str]) -> bool:
        """Save account classifications to database."""
        if not self.current_organization_id:
            return False
        
        try:
            if self.is_online:
                self._set_database_context()
                
                # Delete existing classifications
                self.supabase.table('account_classifications').delete().eq(
                    'organization_id', self.current_organization_id
                ).execute()
                
                # Insert new classifications
                if classifications:
                    classification_data = []
                    for account_id, classification in classifications.items():
                        classification_data.append({
                            'organization_id': self.current_organization_id,
                            'account_id': account_id,
                            'classification': classification,
                            'assigned_by': self.current_user_id
                        })
                    
                    self.supabase.table('account_classifications').insert(
                        classification_data
                    ).execute()
                
                return True
            else:
                # Queue for offline sync
                for account_id, classification in classifications.items():
                    self.offline_cache.queue_operation(
                        'insert', 'account_classifications', {
                            'organization_id': self.current_organization_id,
                            'account_id': account_id,
                            'classification': classification,
                            'assigned_by': self.current_user_id
                        }, self.current_organization_id, self.current_user_id or ''
                    )
                return True
        except Exception as e:
            self.logger.error(f"Failed to save account classifications: {e}")
            return False
    
    def get_account_classification(self, account_id: int) -> Optional[str]:
        """Get classification for a specific account."""
        classifications = self.get_account_classifications()
        return classifications.get(account_id)
    
    def classify_account(self, account_id: int, classification: str) -> bool:
        """Classify a single account."""
        return self.save_account_classifications({account_id: classification})
    
    def _get_classification_display_name(self, classification: str) -> str:
        """Get display name for classification."""
        display_names = {
            'current_asset': 'Current Assets',
            'fixed_asset': 'Fixed Assets',
            'other_asset': 'Other Assets',
            'current_liability': 'Current Liabilities',
            'long_term_liability': 'Long-term Liabilities',
            'other_liability': 'Other Liabilities'
        }
        return display_names.get(classification, classification.replace('_', ' ').title())
    
    def _build_simple_tree(self, account_type_filter, accounts, hierarchical_balances, account_by_id):
        """Build simple hierarchical tree without classifications."""
        tree = []
        
        # Get accounts of the specified type
        type_accounts = [acc for acc in accounts if acc.get('account_type', '').lower() == account_type_filter]
        
        # Build parent-child relationships
        for account in type_accounts:
            if not account.get('parent_id'):  # Root accounts
                node = self._build_account_node(account, type_accounts, hierarchical_balances, account_by_id)
                if node:  # Only add if has balance or children
                    tree.append(node)
        
        return sorted(tree, key=lambda x: x['code'] or x['name'])
    
    # ================================
    # GROUP MANAGEMENT (NEW)
    # ================================
    
    def get_group_options_by_type(self, account_type: str) -> List[str]:
        """Get available group options for a given account type."""
        group_options = {
            'asset': ['None', 'Current Asset', 'Fixed Asset', 'Other Asset', 'Prepaid Expense'],
            'liability': ['None', 'Current Liability', 'Long-term Liability', 'Other Liability'],
            'equity': ['None', 'Owners Equity', 'Retained Earnings', 'Other Equity'],
            'revenue': ['None', 'Sales Revenue', 'Service Revenue', 'Other Revenue', 'Interest Income'],
            'expense': ['None', 'Cost of Goods Sold', 'Operating Expense', 'Administrative Expense', 'Selling Expense', 'Financial Expense', 'Other Expense'],
        }
        return group_options.get(account_type.lower(), ['None'])
    
    def get_group_display_name(self, group: str) -> str:
        """Get display name for group."""
        if not group or group == 'None':
            return 'None'
        
        display_map = {
            'current_asset': 'Current Asset',
            'fixed_asset': 'Fixed Asset',
            'other_asset': 'Other Asset',
            'prepaid_expense': 'Prepaid Expense',
            'current_liability': 'Current Liability',
            'long_term_liability': 'Long-term Liability',
            'other_liability': 'Other Liability',
            'owners_equity': 'Owners Equity',
            'retained_earnings': 'Retained Earnings',
            'other_equity': 'Other Equity',
            'sales_revenue': 'Sales Revenue',
            'service_revenue': 'Service Revenue',
            'other_revenue': 'Other Revenue',
            'interest_income': 'Interest Income',
            'cogs': 'Cost of Goods Sold',
            'operating_expense': 'Operating Expense',
            'administrative_expense': 'Administrative Expense',
            'selling_expense': 'Selling Expense',
            'financial_expense': 'Financial Expense',
            'other_expense': 'Other Expense'
        }
        return display_map.get(group, group.replace('_', ' ').title())
    
    def get_group_key_from_display(self, display_name: str) -> str:
        """Convert display name back to group key."""
        if not display_name or display_name == 'None':
            return ''
        
        reverse_mapping = {
            'Current Asset': 'current_asset',
            'Fixed Asset': 'fixed_asset',
            'Other Asset': 'other_asset',
            'Prepaid Expense': 'prepaid_expense',
            'Current Liability': 'current_liability',
            'Long-term Liability': 'long_term_liability',
            'Other Liability': 'other_liability',
            'Owners Equity': 'owners_equity',
            'Retained Earnings': 'retained_earnings',
            'Other Equity': 'other_equity',
            'Sales Revenue': 'sales_revenue',
            'Service Revenue': 'service_revenue',
            'Other Revenue': 'other_revenue',
            'Interest Income': 'interest_income',
            'Cost of Goods Sold': 'cogs',
            'Operating Expense': 'operating_expense',
            'Administrative Expense': 'administrative_expense',
            'Selling Expense': 'selling_expense',
            'Financial Expense': 'financial_expense',
            'Other Expense': 'other_expense'
        }
        return reverse_mapping.get(display_name, '')
    
    def save_account_group(self, account_id: int, group: str) -> bool:
        """Save group for a single account by updating the group column in the accounts table."""
        if not self.current_organization_id:
            return False
        try:
            print(f"🔍 DEBUG: save_account_group - account_id: {account_id}, group: {group}, is_online: {self.is_online}")
            if self.is_online:
                self._set_database_context()
                # Update the group column in the accounts table
                print(f"🔍 DEBUG: Executing Supabase update for account {account_id} with group '{group}'")
                
                # Check if group column exists first
                try:
                    result = self.supabase.table('accounts').update({'group': group}).eq('id', account_id).eq('organization_id', self.current_organization_id).execute()
                    print(f"🔍 DEBUG: Supabase update result: {result.data if result else 'None'}")
                    
                    if result and result.data:
                        print(f"✅ Group updated successfully for account {account_id}")
                        self._refresh_cache()
                        return True
                    else:
                        print(f"⚠️ No rows updated for account {account_id}")
                        return False
                        
                except Exception as column_error:
                    print(f"🔍 DEBUG: Column error: {column_error}")
                    # Check if this is a column doesn't exist error
                    if "column" in str(column_error).lower() and "does not exist" in str(column_error).lower():
                        print(f"❌ Group column does not exist in accounts table. Please run the migration script: add_group_column_to_accounts.sql")
                        return False
                    else:
                        # Re-raise if it's a different error
                        raise column_error
            else:
                # Queue for offline sync
                print(f"🔍 DEBUG: Queuing group update for offline sync")
                self.offline_cache.queue_operation(
                    'update', 'accounts', {
                        'id': account_id,
                        'group': group
                    }, self.current_organization_id, self.current_user_id or ''
                )
                return True
        except Exception as e:
            print(f"🔍 DEBUG: save_account_group exception: {e}")
            self.logger.error(f"Failed to save account group: {e}")
            return False
    
    def get_account_group(self, account_id: int) -> Optional[str]:
        """Get group for a specific account (including inheritance)."""
        accounts = self.get_chart_of_accounts(active_only=False)
        account = next((acc for acc in accounts if acc['id'] == account_id), None)
        if account:
            return account.get('group')
        return None
    
    def get_inherited_group_for_account(self, account_id: int) -> Optional[str]:
        """Get inherited group for an account (without direct assignment)."""
        accounts = self.get_chart_of_accounts(active_only=False)
        account = next((acc for acc in accounts if acc['id'] == account_id), None)
        if account:
            return account.get('group') if account.get('group_inherited') else None
        return None

    def generate_group_based_income_statement(self, start_date: Optional[str] = None, 
                                            end_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate income statement using group-based categorization with standard hierarchical structure."""
        try:
            # Use hierarchical balances for accurate reporting
            hierarchical_balances = self.get_hierarchical_account_balances(start_date, end_date)
            accounts = self.get_chart_of_accounts(active_only=False)
            
            # Create account lookup
            account_by_id = {acc['id']: acc for acc in accounts}
            
            # Group accounts by their group classification
            revenue_groups = {
                'sales_revenue': [],
                'service_revenue': [],
                'other_revenue': [],
                'interest_income': []
            }
            
            expense_groups = {
                'cogs': [],
                'operating_expense': [],
                'administrative_expense': [],
                'selling_expense': [],
                'financial_expense': [],
                'other_expense': []
            }
            
            # Categorize accounts by group
            for account in accounts:
                account_type = account.get('account_type', '').lower()
                group = account.get('group', '')
                
                if account_type == 'revenue':
                    if group in revenue_groups:
                        revenue_groups[group].append(account)
                    else:
                        revenue_groups['other_revenue'].append(account)
                elif account_type == 'expense':
                    if group in expense_groups:
                        expense_groups[group].append(account)
                    else:
                        expense_groups['other_expense'].append(account)
            
            # Build standard hierarchical structure for revenue groups
            revenue_sections = []
            for group_key, group_accounts in revenue_groups.items():
                if group_accounts:
                    # Get only postable accounts for this group
                    postable_accounts = [acc for acc in group_accounts if acc.get('is_postable', False)]
                    
                    if postable_accounts:
                        # Build complete hierarchy for each postable account
                        hierarchical_accounts = []
                        for acc in postable_accounts:
                            # Get complete hierarchy path for this account
                            hierarchy_path = self._get_account_hierarchy_path(acc['id'], accounts)
                            balance = hierarchical_balances.get(acc['name'], {}).get('net_balance', 0)
                            
                            # Add hierarchy information to account
                            acc['balance'] = balance
                            acc['net_balance'] = balance
                            acc['hierarchy_path'] = hierarchy_path
                            hierarchical_accounts.append(acc)
                        
                        # Calculate total for this group
                        group_total = sum(acc['balance'] for acc in hierarchical_accounts)
                        
                        # Create group section with hierarchical accounts
                        revenue_sections.append({
                            'group': group_key,
                            'name': self.get_group_display_name(group_key),
                            'accounts': hierarchical_accounts,
                            'total': group_total,
                            'is_group_section': True
                        })
            
            # Build standard hierarchical structure for expense groups
            expense_sections = []
            for group_key, group_accounts in expense_groups.items():
                if group_accounts:
                    # Get only postable accounts for this group
                    postable_accounts = [acc for acc in group_accounts if acc.get('is_postable', False)]
                    
                    if postable_accounts:
                        # Build complete hierarchy for each postable account
                        hierarchical_accounts = []
                        for acc in postable_accounts:
                            # Get complete hierarchy path for this account
                            hierarchy_path = self._get_account_hierarchy_path(acc['id'], accounts)
                            balance = hierarchical_balances.get(acc['name'], {}).get('net_balance', 0)
                            
                            # Add hierarchy information to account
                            acc['balance'] = balance
                            acc['net_balance'] = balance
                            acc['hierarchy_path'] = hierarchy_path
                            hierarchical_accounts.append(acc)
                        
                        # Calculate total for this group
                        group_total = sum(acc['balance'] for acc in hierarchical_accounts)
                        
                        # Create group section with hierarchical accounts
                        expense_sections.append({
                            'group': group_key,
                            'name': self.get_group_display_name(group_key),
                            'accounts': hierarchical_accounts,
                            'total': group_total,
                            'is_group_section': True
                        })
            
            # Calculate totals
            total_revenue = sum(section['total'] for section in revenue_sections)
            total_cogs = sum(section['total'] for section in expense_sections if section['group'] == 'cogs')
            total_operating_expenses = sum(section['total'] for section in expense_sections if section['group'] != 'cogs')
            
            gross_profit = total_revenue - total_cogs
            net_income = gross_profit - total_operating_expenses
            
            return {
                'revenue_sections': revenue_sections,
                'expense_sections': expense_sections,
                'total_revenue': total_revenue,
                'total_cogs': total_cogs,
                'total_operating_expenses': total_operating_expenses,
                'gross_profit': gross_profit,
                'net_income': net_income,
                'period': f"{start_date or 'All Time'} to {end_date or 'Current'}",
                'is_group_based': True,
                'is_hierarchical': True,
                'structure': 'standard_hierarchy'
            }
            
        except Exception as e:
            print(f"Error generating group-based income statement: {e}")
            # Fallback to original method
            return self.generate_income_statement_breakdown(start_date, end_date)
    
    def _build_group_tree(self, group_accounts: List[Dict], hierarchical_balances: Dict, account_by_id: Dict) -> List[Dict]:
        """Build hierarchical tree for accounts in a specific group."""
        tree = []
        
        # Build parent-child relationships for this group
        for account in group_accounts:
            if not account.get('parent_id'):  # Root accounts
                node = self._build_account_node(account, group_accounts, hierarchical_balances, account_by_id)
                if node:  # Only add if has balance or children
                    tree.append(node)
        
        return sorted(tree, key=lambda x: x['code'] or x['name'])

    def generate_group_based_balance_sheet(self, as_of_date: str) -> Dict[str, Any]:
        """Generate balance sheet using group-based categorization with standard hierarchical structure."""
        try:
            # Use hierarchical balances for accurate reporting
            hierarchical_balances = self.get_hierarchical_account_balances(None, as_of_date)
            accounts = self.get_chart_of_accounts(active_only=False)
            
            # Create account lookup
            account_by_id = {acc['id']: acc for acc in accounts}
            
            # Group accounts by their group classification
            asset_groups = {
                'current_asset': [],
                'fixed_asset': [],
                'other_asset': [],
                'prepaid_expense': []
            }
            
            liability_groups = {
                'current_liability': [],
                'long_term_liability': [],
                'other_liability': []
            }
            
            equity_groups = {
                'owners_equity': [],
                'retained_earnings': [],
                'other_equity': []
            }
            
            # Categorize accounts by group
            for account in accounts:
                account_type = account.get('account_type', '').lower()
                group = account.get('group', '')
                
                if account_type == 'asset':
                    if group in asset_groups:
                        asset_groups[group].append(account)
                    else:
                        asset_groups['other_asset'].append(account)
                elif account_type == 'liability':
                    if group in liability_groups:
                        liability_groups[group].append(account)
                    else:
                        liability_groups['other_liability'].append(account)
                elif account_type == 'equity':
                    if group in equity_groups:
                        equity_groups[group].append(account)
                    else:
                        equity_groups['other_equity'].append(account)
            
            # Build standard hierarchical structure for asset groups
            asset_sections = []
            for group_key, group_accounts in asset_groups.items():
                if group_accounts:
                    # Build a true tree for this group
                    tree = self._build_account_tree(group_accounts, hierarchical_balances)
                    group_total = self._calculate_tree_total(tree)
                    asset_sections.append({
                        'group': group_key,
                        'name': self.get_group_display_name(group_key),
                        'accounts': tree,
                        'total': group_total,
                        'is_group_section': True
                    })
            
            # Build standard hierarchical structure for liability groups
            liability_sections = []
            for group_key, group_accounts in liability_groups.items():
                if group_accounts:
                    tree = self._build_account_tree(group_accounts, hierarchical_balances)
                    group_total = self._calculate_tree_total(tree)
                    liability_sections.append({
                        'group': group_key,
                        'name': self.get_group_display_name(group_key),
                        'accounts': tree,
                        'total': group_total,
                        'is_group_section': True
                    })
            
            # Build standard hierarchical structure for equity groups
            equity_sections = []
            for group_key, group_accounts in equity_groups.items():
                if group_accounts:
                    tree = self._build_account_tree(group_accounts, hierarchical_balances)
                    group_total = self._calculate_tree_total(tree)
                    equity_sections.append({
                        'group': group_key,
                        'name': self.get_group_display_name(group_key),
                        'accounts': tree,
                        'total': group_total,
                        'is_group_section': True
                    })
            
            # Calculate totals
            total_assets = sum(section['total'] for section in asset_sections)
            total_liabilities = sum(section['total'] for section in liability_sections)
            total_equity = sum(section['total'] for section in equity_sections)
            
            return {
                'asset_sections': asset_sections,
                'liability_sections': liability_sections,
                'equity_sections': equity_sections,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'as_of_date': as_of_date or 'Current',
                'is_group_based': True,
                'is_hierarchical': True,
                'structure': 'standard_hierarchy'
            }
            
        except Exception as e:
            print(f"Error generating group-based balance sheet: {e}")
            # Fallback to original method
            return self.generate_balance_sheet_breakdown(as_of_date)

    def _get_account_hierarchy_path(self, account_id: int, all_accounts: List[Dict]) -> List[Dict]:
        """Get the complete hierarchy path for an account from root to the account itself."""
        path = []
        current_id = account_id
        
        # Build path from account up to root
        while current_id:
            # Find current account
            current_account = next((acc for acc in all_accounts if acc['id'] == current_id), None)
            if not current_account:
                break
            
            # Add to path (insert at beginning to maintain root->leaf order)
            path.insert(0, {
                'id': current_account['id'],
                'name': current_account['name'],
                'code': current_account.get('code', ''),
                'level': current_account.get('level', 1),
                'is_postable': current_account.get('is_postable', False)
            })
            
            # Move to parent
            current_id = current_account.get('parent_id')
        
        return path

    def _build_account_tree(self, accounts: list, balances: dict) -> list:
        """Builds a hierarchical tree from a flat account list using parent_id relationships."""
        account_by_id = {acc['id']: acc for acc in accounts}
        children_by_parent = {}
        for acc in accounts:
            parent_id = acc.get('parent_id')
            if parent_id:
                children_by_parent.setdefault(parent_id, []).append(acc)
        
        def build_node(acc):
            node = {
                'id': acc['id'],
                'name': acc['name'],
                'code': acc.get('code', ''),
                'level': acc.get('level', 1),
                'is_postable': acc.get('is_postable', False),
                'balance': balances.get(acc['name'], {}).get('net_balance', 0),
                'children': []
            }
            for child in children_by_parent.get(acc['id'], []):
                node['children'].append(build_node(child))
            return node
        
        # Only top-level accounts (no parent in this group)
        roots = [acc for acc in accounts if not acc.get('parent_id') or acc.get('parent_id') not in account_by_id]
        return [build_node(acc) for acc in roots]

    def get_account_historical_balances(self, account_name: str, from_date: str, to_date: str) -> list:
        """
        Get historical balances for a specific account for each month between from_date and to_date (inclusive).
        Returns a list of dicts: [{ 'period': 'Jan', 'date': '2024-01-31', 'balance': ... }, ...]
        """
        if not self.current_organization_id:
            return []
        try:
            from datetime import datetime, timedelta
            import calendar

            # Parse input dates
            start = datetime.strptime(from_date, "%Y-%m-%d")
            end = datetime.strptime(to_date, "%Y-%m-%d")
            # Build a list of month-end dates between start and end
            month_ends = []
            current = start.replace(day=1)
            while current <= end:
                # Get last day of this month
                last_day = calendar.monthrange(current.year, current.month)[1]
                month_end = current.replace(day=last_day)
                # Only include if within range
                if month_end >= start and month_end <= end:
                    month_ends.append(month_end)
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year+1, month=1, day=1)
                else:
                    current = current.replace(month=current.month+1, day=1)
            # Always include the end date if not already present
            if month_ends and month_ends[-1] < end:
                month_ends.append(end)
            elif not month_ends:
                month_ends.append(end)
            # Get balance as of each month end
            historical_data = []
            for dt in month_ends:
                end_date_str = dt.strftime('%Y-%m-%d')
                hierarchical_balances = self.get_hierarchical_account_balances(None, end_date_str)
                balance_info = hierarchical_balances.get(account_name, {})
                net_balance = balance_info.get('net_balance', 0.0)
                month_label = dt.strftime('%b')
                historical_data.append({
                    'period': month_label,
                    'date': end_date_str,
                    'balance': net_balance
                })
            return historical_data
        except Exception as e:
            print(f"Error getting historical balances for {account_name}: {e}")
            return []

    def get_account_comparison_data(self, account1_name: str, account2_name: str, from_date: str, to_date: str) -> dict:
        """
        Get comparison data for two accounts for each month between from_date and to_date.
        Returns dict with month_labels, account1, account2.
        """
        try:
            account1_data = self.get_account_historical_balances(account1_name, from_date, to_date)
            account2_data = self.get_account_historical_balances(account2_name, from_date, to_date)
            month_labels = [d['period'] for d in account1_data] if account1_data else []
            account1_balances = [d['balance'] for d in account1_data] if account1_data else []
            account2_balances = [d['balance'] for d in account2_data] if account2_data else []
            return {
                'month_labels': month_labels,
                'account1': {
                    'name': account1_name,
                    'balances': account1_balances
                },
                'account2': {
                    'name': account2_name,
                    'balances': account2_balances
                },
                'months': len(month_labels)
            }
        except Exception as e:
            print(f"Error getting account comparison data: {e}")
            return {
                'month_labels': [],
                'account1': {'name': account1_name, 'balances': []},
                'account2': {'name': account2_name, 'balances': []},
                'months': 0
            }

    def get_expense_breakdown_by_groups(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Get expense breakdown by groups for donut chart visualization.
        Returns list of dicts with group name, total amount, and color.
        """
        try:
            # Get group-based income statement data
            income_statement = self.generate_group_based_income_statement(from_date, to_date)
            
            # Define colors for each expense group
            group_colors = {
                'cogs': '#f44336',  # Red for COGS
                'operating_expense': '#ff9800',  # Orange for Operating
                'administrative_expense': '#9c27b0',  # Purple for Admin
                'selling_expense': '#2196f3',  # Blue for Selling
                'financial_expense': '#ff5722',  # Deep Orange for Financial
                'other_expense': '#607d8b'  # Blue Grey for Other
            }
            
            expense_breakdown = []
            
            # Process expense sections from income statement
            for section in income_statement.get('expense_sections', []):
                group_key = section.get('group', '')
                group_name = section.get('name', '')
                group_total = section.get('total', 0)
                
                # Only include groups with actual amounts
                if group_total > 0:
                    expense_breakdown.append({
                        'group': group_key,
                        'name': group_name,
                        'amount': group_total,
                        'color': group_colors.get(group_key, '#607d8b')  # Default to blue grey
                    })
            
            # Sort by amount (largest first)
            expense_breakdown.sort(key=lambda x: x['amount'], reverse=True)
            
            return expense_breakdown
            
        except Exception as e:
            print(f"Error getting expense breakdown by groups: {e}")
            # Return empty list on error
            return []

    def get_margin_trends_data(self, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Get historical margin trends data for chart visualization.
        Returns data for Gross Margin, Net Margin, and Revenue Growth over the selected period.
        """
        try:
            from datetime import datetime, timedelta
            import calendar
            
            # Parse input dates
            start = datetime.strptime(from_date, "%Y-%m-%d")
            end = datetime.strptime(to_date, "%Y-%m-%d")
            
            # Calculate monthly periods within the date range
            monthly_data = []
            current_date = start.replace(day=1)  # Start of first month
            
            while current_date <= end:
                # Calculate end of current month
                if current_date.month == 12:
                    month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
                
                # Ensure we don't exceed the requested end date
                if month_end > end:
                    month_end = end
                
                # Get income statement for this month
                month_start_str = current_date.strftime("%Y-%m-%d")
                month_end_str = month_end.strftime("%Y-%m-%d")
                
                try:
                    income_statement = self.generate_group_based_income_statement(month_start_str, month_end_str)
                    
                    total_revenue = income_statement.get('total_revenue', 0)
                    total_cogs = income_statement.get('total_cogs', 0)
                    total_operating_expenses = income_statement.get('total_operating_expenses', 0)
                    net_income = income_statement.get('net_income', 0)
                    
                    # Calculate margins
                    gross_profit = total_revenue - total_cogs
                    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
                    net_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
                    
                    monthly_data.append({
                        'period': current_date.strftime("%Y-%m"),
                        'gross_margin': gross_margin,
                        'net_margin': net_margin,
                        'revenue': total_revenue,
                        'net_income': net_income
                    })
                    
                except Exception as e:
                    print(f"Error calculating data for {month_start_str}: {e}")
                    # Add zero values for this month
                    monthly_data.append({
                        'period': current_date.strftime("%Y-%m"),
                        'gross_margin': 0,
                        'net_margin': 0,
                        'revenue': 0,
                        'net_income': 0
                    })
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            # Calculate revenue growth (month-over-month)
            revenue_growth = []
            for i, data in enumerate(monthly_data):
                if i == 0:
                    revenue_growth.append(0)  # First month has no growth
                else:
                    prev_revenue = monthly_data[i-1]['revenue']
                    current_revenue = data['revenue']
                    if prev_revenue > 0:
                        growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
                    else:
                        growth = 0 if current_revenue == 0 else 100  # 100% growth if from 0
                    revenue_growth.append(growth)
            
            # Add revenue growth to monthly data
            for i, data in enumerate(monthly_data):
                data['revenue_growth'] = revenue_growth[i]
            
            return {
                'monthly_data': monthly_data,
                'periods': [data['period'] for data in monthly_data],
                'gross_margins': [data['gross_margin'] for data in monthly_data],
                'net_margins': [data['net_margin'] for data in monthly_data],
                'revenue_growth': [data['revenue_growth'] for data in monthly_data],
                'revenues': [data['revenue'] for data in monthly_data],
                'net_incomes': [data['net_income'] for data in monthly_data]
            }
            
        except Exception as e:
            print(f"Error getting margin trends data: {e}")
            # Return empty data structure
            return {
                'monthly_data': [],
                'periods': [],
                'gross_margins': [],
                'net_margins': [],
                'revenue_growth': [],
                'revenues': [],
                'net_incomes': []
            }

# ================================
# ENHANCED FEATURES INTEGRATION
# (These would normally be separate modules, but included here for completeness)
# ================================

class FinancialRatios:
    """Calculate financial ratios from accounting data"""
    
    def __init__(self, accounting_system: UnifiedAccountingSystem):
        self.system = accounting_system
        self.logger = logging.getLogger(__name__)
    
    def calculate_liquidity_ratios(self, as_of_date: str) -> Dict[str, float]:
        """Calculate liquidity ratios"""
        balance_sheet = self.system.generate_balance_sheet_breakdown(as_of_date)
        
        total_assets = balance_sheet.get('total_assets', 0)
        total_liabilities = balance_sheet.get('total_liabilities', 0)
        
        ratios = {}
        
        if total_liabilities > 0:
            ratios['current_ratio'] = total_assets / total_liabilities
        else:
            ratios['current_ratio'] = float('inf')  # No liabilities
        
        return ratios
    
    def calculate_profitability_ratios(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Calculate profitability ratios"""
        income_statement = self.system.generate_income_statement_breakdown(start_date, end_date)
        
        revenue = income_statement.get('revenue_total', 0)
        net_income = income_statement.get('net_income', 0)
        
        ratios = {}
        
        if revenue > 0:
            ratios['net_profit_margin'] = (net_income / revenue) * 100
            ratios['gross_profit_margin'] = (revenue - income_statement.get('expense_total', 0)) / revenue * 100
        else:
            ratios['net_profit_margin'] = 0
            ratios['gross_profit_margin'] = 0
        
        return ratios


# Create alias for backward compatibility
AccountingSystem = UnifiedAccountingSystem
