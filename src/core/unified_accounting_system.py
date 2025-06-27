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
                    cursor.execute('''
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


class UnifiedAccountingSystem:
    """
    Unified Accounting System that combines all functionality:
    - Core accounting operations with authentication
    - Offline support with automatic sync
    - Advanced financial features and reporting
    - Period closing and audit trails
    """
    
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
            self.supabase.rpc('set_app_context', {
                'user_id': self.current_user_id,
                'organization_id': self.current_organization_id,
                'role': 'accountant'  # This should come from session manager
            }).execute()
        except Exception as e:
            self.logger.error(f"Failed to set database context: {e}")

    # ================================
    # CHART OF ACCOUNTS OPERATIONS
    # ================================
    
    def get_chart_of_accounts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get chart of accounts for current organization with calculated hierarchy fields."""
        if not self.current_organization_id:
            return []
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                result = self.db_manager.get_accounts(self.current_organization_id, active_only)
                if result:
                    # Update cache
                    self.offline_cache.cache_data('accounts', result, self.current_organization_id)
                    # Add calculated fields
                    return self._enhance_accounts_with_hierarchy(result)
            except Exception as e:
                self.logger.error(f"Online accounts fetch failed: {e}")
        
        # Fallback to cached data
        self.logger.info("📱 Using cached accounts data")
        cached_accounts = self.offline_cache.get_cached_data('accounts', self.current_organization_id)
        
        if active_only:
            filtered_accounts = [acc for acc in cached_accounts if acc.get('is_active', True)]
        else:
            filtered_accounts = cached_accounts
            
        # Add calculated fields
        return self._enhance_accounts_with_hierarchy(filtered_accounts)
    
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
            
            # Add compatibility field mappings for UI
            enhanced_acc['type'] = acc.get('account_type', '')  # Map account_type to type for UI compatibility
            
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
        
        # Add organization context
        account_data['organization_id'] = self.current_organization_id
        account_data['created_by'] = self.current_user_id
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                result = self.db_manager.create_account(account_data)
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"Online account creation failed: {e}")
                self.is_online = False
        
        # Queue for later sync if offline
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
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                return self.db_manager.update_account(account_id, updates)
            except Exception as e:
                self.logger.error(f"Online account update failed: {e}")
                self.is_online = False
        
        # Queue for later sync if offline
        updates['id'] = account_id
        self.offline_cache.queue_operation(
            'UPDATE', 'accounts', updates,
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
        """Get journal entries for current organization."""
        if not self.current_organization_id:
            return []
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                result = self.db_manager.get_journal_entries(
                    self.current_organization_id, start_date, end_date
                )
                if result:
                    # Update cache
                    self.offline_cache.cache_data('journal_entries', result, self.current_organization_id)
                    return result
            except Exception as e:
                self.logger.error(f"Online journal entries fetch failed: {e}")
        
        # Fallback to cached data
        self.logger.info("📱 Using cached journal entries")
        cached_entries = self.offline_cache.get_cached_data('journal_entries', self.current_organization_id)
        
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
    
    def get_recent_journal_entries(self, limit: int = 20) -> List[Dict]:
        """Get recent journal entries"""
        entries = self.get_journal_entries()
        # Sort by date descending and limit
        sorted_entries = sorted(entries, key=lambda x: x.get('date', ''), reverse=True)
        return sorted_entries[:limit]
    
    def add_journal_entry(self, entry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add journal entry."""
        if not self.current_organization_id:
            raise ValueError("No organization context set")
        
        if not self.auth_manager.can_create_journal_entries(self.current_organization_id):
            raise PermissionError("Insufficient permissions to create journal entries")
        
        # Add organization context
        entry_data['organization_id'] = self.current_organization_id
        entry_data['created_by'] = self.current_user_id
        
        # Try online first
        if self.is_online:
            try:
                self._set_database_context()
                result = self.db_manager.create_journal_entry(entry_data)
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"Online journal entry creation failed: {e}")
                self.is_online = False
        
        # Queue for later sync if offline
        self.offline_cache.queue_operation(
            'INSERT', 'journal_entries', entry_data,
            self.current_organization_id, self.current_user_id
        )
        
        # Return the entry data for immediate UI update
        entry_data['id'] = str(uuid.uuid4())
        entry_data['queued'] = True
        return entry_data
    
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
    
    def get_trial_balance(self, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Calculate trial balance from journal entries"""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_chart_of_accounts(active_only=False)
        
        # Create account lookup
        account_lookup = {acc['name']: acc for acc in accounts}
        
        # Track debit and credit totals separately for each account
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
        
        # Build trial balance result in expected format
        trial_balance = []
        all_accounts = set(account_debits.keys()) | set(account_credits.keys())
        
        for account_name in all_accounts:
            debit_total = account_debits.get(account_name, 0.0)
            credit_total = account_credits.get(account_name, 0.0)
            
            # Only include accounts with activity
            if debit_total > 0 or credit_total > 0:
                trial_balance.append({
                    'name': account_name,
                    'debit_total': debit_total,
                    'credit_total': credit_total
                })
        
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
    
    def generate_income_statement_breakdown(self, start_date: str, end_date: str) -> Dict:
        """Generate income statement with breakdown"""
        entries = self.get_journal_entries(start_date, end_date)
        accounts = self.get_chart_of_accounts(active_only=False)
        
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
        accounts = self.get_chart_of_accounts(active_only=False)
        
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
        accounts = self.get_chart_of_accounts(active_only=False)
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
