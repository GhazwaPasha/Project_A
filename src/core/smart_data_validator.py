"""
Smart Data Validation Layer
Prevents expensive operations when there's no data, solving performance issues.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import threading
import time

class SmartDataValidator:
    """Validates data existence before expensive operations to prevent timeouts."""
    
    def __init__(self, system):
        self.system = system
        self.logger = logging.getLogger(__name__)
        
        # Cache validation results to avoid repeated checks
        self._validation_cache = {}
        self._cache_lock = threading.Lock()
        
        # Track data state per organization
        self._org_data_state = {}
        
    def has_any_data(self, org_id: str = None) -> bool:
        """Quick check if organization has any meaningful data."""
        if not org_id:
            org_id = self.system.current_organization_id
            
        if not org_id:
            return False
            
        cache_key = f"has_data_{org_id}"
        
        with self._cache_lock:
            if cache_key in self._validation_cache:
                return self._validation_cache[cache_key]
        
        # Quick database check for any transactions
        try:
            result = self.system.supabase.table('journal_entries')\
                .select('id', count='exact')\
                .eq('organization_id', org_id)\
                .limit(1)\
                .execute()
            
            has_data = result.count > 0 if result.count is not None else False
            
            with self._cache_lock:
                self._validation_cache[cache_key] = has_data
                
            self.logger.info(f"Data validation for org {org_id}: {has_data}")
            return has_data
            
        except Exception as e:
            self.logger.error(f"Error checking data existence: {e}")
            return False
    
    def has_accounts(self, org_id: str = None) -> bool:
        """Check if organization has any accounts."""
        if not org_id:
            org_id = self.system.current_organization_id
            
        if not org_id:
            return False
            
        cache_key = f"has_accounts_{org_id}"
        
        with self._cache_lock:
            if cache_key in self._validation_cache:
                return self._validation_cache[cache_key]
        
        try:
            result = self.system.supabase.table('accounts')\
                .select('id', count='exact')\
                .eq('organization_id', org_id)\
                .eq('is_active', True)\
                .limit(1)\
                .execute()
            
            has_accounts = result.count > 0 if result.count is not None else False
            
            with self._cache_lock:
                self._validation_cache[cache_key] = has_accounts
                
            return has_accounts
            
        except Exception as e:
            self.logger.error(f"Error checking accounts existence: {e}")
            return False
    
    def validate_before_expensive_operation(self, operation_name: str, org_id: str = None) -> bool:
        """Validate data exists before expensive operations."""
        if not self.has_any_data(org_id):
            self.logger.warning(f"Skipping expensive operation '{operation_name}' - no data available")
            return False
        return True
    
    def get_safe_empty_result(self, operation_type: str) -> Any:
        """Get appropriate empty result for different operation types."""
        empty_results = {
            'ledger': [],
            'balances': {},
            'ratios': {'error': 'No data available for ratio calculation'},
            'charts': [],
            'metrics': {'cash': 0, 'revenue': 0, 'expenses': 0, 'net_income': 0},
            'trial_balance': [],
            'income_statement': {'error': 'No transactions available'},
            'balance_sheet': {'error': 'No accounts or transactions available'}
        }
        return empty_results.get(operation_type, {})
    
    def clear_cache(self, org_id: str = None):
        """Clear validation cache for organization."""
        if org_id:
            keys_to_remove = [k for k in self._validation_cache.keys() if org_id in k]
        else:
            keys_to_remove = list(self._validation_cache.keys())
            
        with self._cache_lock:
            for key in keys_to_remove:
                self._validation_cache.pop(key, None)


def smart_data_guard(operation_type: str = 'default'):
    """Decorator to guard expensive operations with data validation."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get validator from system
            validator = getattr(self, 'data_validator', None)
            if not validator:
                # Try to get from system
                if hasattr(self, 'system'):
                    validator = getattr(self.system, 'data_validator', None)
            
            if validator:
                # Check if we have data before expensive operation
                if not validator.validate_before_expensive_operation(func.__name__):
                    # Return safe empty result
                    return validator.get_safe_empty_result(operation_type)
            
            # Proceed with normal operation
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# Global validator instance
_data_validator = None

def get_data_validator(system) -> SmartDataValidator:
    """Get or create global data validator instance."""
    global _data_validator
    if _data_validator is None:
        _data_validator = SmartDataValidator(system)
    return _data_validator 