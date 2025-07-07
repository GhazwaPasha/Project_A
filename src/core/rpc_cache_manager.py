"""
RPC Cache Manager for optimizing database calls
Provides smart caching and batching for RPC calls to reduce database round trips
"""

import time
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import logging


class CacheStrategy(Enum):
    """Cache strategy for different types of data"""
    SHORT_TERM = 30  # 30 seconds - for frequently changing data
    MEDIUM_TERM = 300  # 5 minutes - for moderately stable data
    LONG_TERM = 1800  # 30 minutes - for stable data
    SESSION = -1  # Until session ends - for user-specific data


class RPCCacheManager:
    """Smart cache manager for RPC calls with batching and invalidation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._batch_queue: Dict[str, List[Tuple[str, Any, callable]]] = {}
        self._batch_timers: Dict[str, Any] = {}
        
    def get_cached_result(self, cache_key: str, strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM) -> Optional[Any]:
        """Get cached result if valid"""
        if cache_key not in self._cache:
            return None
            
        cache_entry = self._cache[cache_key]
        current_time = time.time()
        
        # Check if cache is expired
        if strategy.value > 0 and (current_time - cache_entry['timestamp']) > strategy.value:
            # Cache expired, remove it
            del self._cache[cache_key]
            return None
            
        self.logger.debug(f"Cache hit for key: {cache_key}")
        return cache_entry['data']
    
    def set_cached_result(self, cache_key: str, data: Any, strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM):
        """Set cached result with timestamp"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time(),
            'strategy': strategy
        }
        self.logger.debug(f"Cached result for key: {cache_key}")
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            # Clear all cache
            self._cache.clear()
            self.logger.info("All cache invalidated")
        else:
            # Clear matching entries
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
            self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching: {pattern}")
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a specific user"""
        self.invalidate_cache(f"user_{user_id}")
    
    def invalidate_org_cache(self, org_id: str):
        """Invalidate all cache entries for a specific organization"""
        self.invalidate_cache(f"org_{org_id}")
    
    def batch_rpc_call(self, batch_key: str, rpc_name: str, params: Dict[str, Any], 
                      callback: callable, timeout_ms: int = 50):
        """Batch RPC calls to reduce database round trips"""
        if batch_key not in self._batch_queue:
            self._batch_queue[batch_key] = []
            
        # Add to batch queue
        self._batch_queue[batch_key].append((rpc_name, params, callback))
        
        # Start timer if not already running
        if batch_key not in self._batch_timers:
            from PyQt6.QtCore import QTimer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._execute_batch(batch_key))
            timer.start(timeout_ms)
            self._batch_timers[batch_key] = timer
    
    def _execute_batch(self, batch_key: str):
        """Execute batched RPC calls"""
        if batch_key not in self._batch_queue:
            return
            
        batch_items = self._batch_queue[batch_key]
        self._batch_queue[batch_key] = []
        
        if batch_key in self._batch_timers:
            self._batch_timers[batch_key].deleteLater()
            del self._batch_timers[batch_key]
        
        if not batch_items:
            return
            
        self.logger.debug(f"Executing batch of {len(batch_items)} RPC calls for key: {batch_key}")
        
        # Group by RPC name and parameters
        grouped_calls = {}
        for rpc_name, params, callback in batch_items:
            param_key = str(sorted(params.items()))
            if rpc_name not in grouped_calls:
                grouped_calls[rpc_name] = {}
            if param_key not in grouped_calls[rpc_name]:
                grouped_calls[rpc_name][param_key] = []
            grouped_calls[rpc_name][param_key].append((params, callback))
        
        # Execute grouped calls
        for rpc_name, param_groups in grouped_calls.items():
            for param_key, calls in param_groups.items():
                if len(calls) == 1:
                    # Single call, execute directly
                    params, callback = calls[0]
                    self._execute_single_rpc(rpc_name, params, callback)
                else:
                    # Multiple calls with same parameters, execute once and share result
                    params, _ = calls[0]
                    result = self._execute_single_rpc(rpc_name, params, None)
                    for _, callback in calls:
                        if callback:
                            callback(result)
    
    def _execute_single_rpc(self, rpc_name: str, params: Dict[str, Any], callback: callable) -> Any:
        """Execute a single RPC call"""
        try:
            # This would be implemented by the calling class
            # For now, we'll just call the callback with None
            if callback:
                callback(None)
            return None
        except Exception as e:
            self.logger.error(f"Error executing RPC {rpc_name}: {e}")
            if callback:
                callback(None)
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        total_size = sum(len(str(v)) for v in self._cache.values())
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'batch_queues': len(self._batch_queue),
            'active_timers': len(self._batch_timers)
        }


# Global instance
rpc_cache = RPCCacheManager() 