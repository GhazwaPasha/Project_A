from PyQt6.QtCore import QObject, QTimer
from typing import Dict, List, Any, Callable
import logging
from dataclasses import dataclass
from enum import Enum

class QueryType(Enum):
    PERMISSIONS = "permissions"
    ACCOUNTS = "accounts"
    JOURNAL_ENTRIES = "journal_entries"
    ORGANIZATION_DATA = "organization_data"

@dataclass
class BatchedQuery:
    query_type: QueryType
    org_id: str
    parameters: Dict[str, Any]
    callback: Callable
    priority: int = 0

class BatchedQueryManager(QObject):
    """Manages batched database queries to reduce round trips"""
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
        # Query batching
        self.pending_queries: Dict[QueryType, List[BatchedQuery]] = {}
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_batched_queries)
        self.batch_timer.setSingleShot(True)
        self.batch_delay = 50  # 50ms batch delay
        
        # Cache for batched results
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
    def add_query(self, query_type: QueryType, org_id: str, parameters: Dict[str, Any], 
                  callback: Callable, priority: int = 0):
        """Add a query to the batch"""
        query = BatchedQuery(
            query_type=query_type,
            org_id=org_id,
            parameters=parameters,
            callback=callback,
            priority=priority
        )
        
        if query_type not in self.pending_queries:
            self.pending_queries[query_type] = []
        
        self.pending_queries[query_type].append(query)
        
        # Start batch timer if not already running
        if not self.batch_timer.isActive():
            self.batch_timer.start(self.batch_delay)
    
    def _process_batched_queries(self):
        """Process all pending batched queries"""
        try:
            for query_type, queries in self.pending_queries.items():
                if queries:
                    self._execute_batched_query(query_type, queries)
            
            # Clear processed queries
            self.pending_queries.clear()
            
        except Exception as e:
            self.logger.error(f"Error processing batched queries: {e}")
    
    def _execute_batched_query(self, query_type: QueryType, queries: List[BatchedQuery]):
        """Execute a batch of queries of the same type"""
        try:
            if query_type == QueryType.PERMISSIONS:
                self._execute_batched_permissions(queries)
            elif query_type == QueryType.ACCOUNTS:
                self._execute_batched_accounts(queries)
            elif query_type == QueryType.JOURNAL_ENTRIES:
                self._execute_batched_journal_entries(queries)
            elif query_type == QueryType.ORGANIZATION_DATA:
                self._execute_batched_organization_data(queries)
                
        except Exception as e:
            self.logger.error(f"Error executing batched {query_type.value} query: {e}")
            # Call callbacks with error
            for query in queries:
                try:
                    query.callback({"error": str(e)})
                except Exception as callback_error:
                    self.logger.error(f"Error in query callback: {callback_error}")
    
    def _execute_batched_permissions(self, queries: List[BatchedQuery]):
        """Execute batched permissions queries"""
        if not self.auth_manager.db_manager or not self.auth_manager.db_manager.supabase:
            self._handle_no_db_connection(queries)
            return
        
        try:
            # Group queries by organization
            org_queries = {}
            for query in queries:
                org_id = query.org_id
                if org_id not in org_queries:
                    org_queries[org_id] = []
                org_queries[org_id].append(query)
            
            # Execute RPC call for each organization
            for org_id, org_query_list in org_queries.items():
                try:
                    # Get all unique permissions needed for this org
                    all_permissions = set()
                    for query in org_query_list:
                        permissions = query.parameters.get('permissions', [])
                        if isinstance(permissions, list):
                            all_permissions.update(permissions)
                        else:
                            all_permissions.add(permissions)
                    
                    # Execute single RPC call for all permissions
                    result = self.auth_manager.db_manager.supabase.rpc(
                        'check_user_permissions_batch',
                        {
                            'org_id': org_id,
                            'permissions': list(all_permissions)
                        }
                    ).execute()
                    
                    # Distribute results to callbacks
                    permissions_result = result.data if result.data else {}
                    
                    for query in org_query_list:
                        requested_permissions = query.parameters.get('permissions', [])
                        if isinstance(requested_permissions, list):
                            # Multiple permissions requested
                            query_result = {}
                            for perm in requested_permissions:
                                query_result[perm] = permissions_result.get(perm, False)
                        else:
                            # Single permission requested
                            query_result = {requested_permissions: permissions_result.get(requested_permissions, False)}
                        
                        try:
                            query.callback(query_result)
                        except Exception as e:
                            self.logger.error(f"Error in permissions callback: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error executing permissions for org {org_id}: {e}")
                    # Call callbacks with error
                    for query in org_query_list:
                        try:
                            query.callback({"error": str(e)})
                        except Exception as callback_error:
                            self.logger.error(f"Error in permissions callback: {callback_error}")
                            
        except Exception as e:
            self.logger.error(f"Error in batched permissions execution: {e}")
            self._handle_query_error(queries, e)
    
    def _execute_batched_accounts(self, queries: List[BatchedQuery]):
        """Execute batched accounts queries"""
        if not self.auth_manager.db_manager or not self.auth_manager.db_manager.supabase:
            self._handle_no_db_connection(queries)
            return
        
        try:
            # Group by organization
            org_queries = {}
            for query in queries:
                org_id = query.org_id
                if org_id not in org_queries:
                    org_queries[org_id] = []
                org_queries[org_id].append(query)
            
            for org_id, org_query_list in org_queries.items():
                try:
                    # Single query for all accounts in organization
                    result = self.auth_manager.db_manager.supabase.table('accounts')\
                        .select('*')\
                        .eq('organization_id', org_id)\
                        .order('account_number')\
                        .execute()
                    
                    accounts_data = result.data if result.data else []
                    
                    # Distribute to all callbacks for this org
                    for query in org_query_list:
                        try:
                            query.callback({"accounts": accounts_data})
                        except Exception as e:
                            self.logger.error(f"Error in accounts callback: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error executing accounts for org {org_id}: {e}")
                    self._handle_query_error(org_query_list, e)
                    
        except Exception as e:
            self.logger.error(f"Error in batched accounts execution: {e}")
            self._handle_query_error(queries, e)
    
    def _execute_batched_journal_entries(self, queries: List[BatchedQuery]):
        """Execute batched journal entries queries"""
        if not self.auth_manager.db_manager or not self.auth_manager.db_manager.supabase:
            self._handle_no_db_connection(queries)
            return
        
        try:
            # Group by organization
            org_queries = {}
            for query in queries:
                org_id = query.org_id
                if org_id not in org_queries:
                    org_queries[org_id] = []
                org_queries[org_id].append(query)
            
            for org_id, org_query_list in org_queries.items():
                try:
                    # Get the highest limit requested
                    max_limit = 50  # Default
                    for query in org_query_list:
                        limit = query.parameters.get('limit', 50)
                        max_limit = max(max_limit, limit)
                    
                    # Single query for journal entries
                    result = self.auth_manager.db_manager.supabase.table('journal_entries')\
                        .select('*')\
                        .eq('organization_id', org_id)\
                        .order('created_at', desc=True)\
                        .limit(max_limit)\
                        .execute()
                    
                    entries_data = result.data if result.data else []
                    
                    # Distribute to all callbacks for this org
                    for query in org_query_list:
                        try:
                            limit = query.parameters.get('limit', 50)
                            query_data = entries_data[:limit] if limit < len(entries_data) else entries_data
                            query.callback({"journal_entries": query_data})
                        except Exception as e:
                            self.logger.error(f"Error in journal entries callback: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error executing journal entries for org {org_id}: {e}")
                    self._handle_query_error(org_query_list, e)
                    
        except Exception as e:
            self.logger.error(f"Error in batched journal entries execution: {e}")
            self._handle_query_error(queries, e)
    
    def _execute_batched_organization_data(self, queries: List[BatchedQuery]):
        """Execute batched organization data queries"""
        if not self.auth_manager.db_manager or not self.auth_manager.db_manager.supabase:
            self._handle_no_db_connection(queries)
            return
        
        try:
            # Group by organization
            org_queries = {}
            for query in queries:
                org_id = query.org_id
                if org_id not in org_queries:
                    org_queries[org_id] = []
                org_queries[org_id].append(query)
            
            for org_id, org_query_list in org_queries.items():
                try:
                    # Get organization details
                    result = self.auth_manager.db_manager.supabase.table('organizations')\
                        .select('*')\
                        .eq('id', org_id)\
                        .single()\
                        .execute()
                    
                    org_data = result.data if result.data else {}
                    
                    # Distribute to all callbacks for this org
                    for query in org_query_list:
                        try:
                            query.callback({"organization": org_data})
                        except Exception as e:
                            self.logger.error(f"Error in organization data callback: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error executing organization data for org {org_id}: {e}")
                    self._handle_query_error(org_query_list, e)
                    
        except Exception as e:
            self.logger.error(f"Error in batched organization data execution: {e}")
            self._handle_query_error(queries, e)
    
    def _handle_no_db_connection(self, queries: List[BatchedQuery]):
        """Handle case when no database connection is available"""
        error_result = {"error": "No database connection available"}
        for query in queries:
            try:
                query.callback(error_result)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")
    
    def _handle_query_error(self, queries: List[BatchedQuery], error: Exception):
        """Handle query execution errors"""
        error_result = {"error": str(error)}
        for query in queries:
            try:
                query.callback(error_result)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")
    
    def flush_queries(self):
        """Force processing of all pending queries immediately"""
        if self.batch_timer.isActive():
            self.batch_timer.stop()
        
        self._process_batched_queries()
    
    def clear_cache(self):
        """Clear the query cache"""
        self.query_cache.clear() 