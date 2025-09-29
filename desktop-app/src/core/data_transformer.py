"""
Data Transformation Layer
Handles conversion between database format (relational) and application format (simple)
"""

from typing import Dict, List, Optional, Any
import logging

class DataTransformer:
    """Centralized data transformation for journal entries and accounts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def db_to_app_journal_entry(self, db_entry: Dict[str, Any], accounts_lookup: Optional[Dict[int, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Transform database journal entry format to application format"""
        try:
            # Extract basic information with flexible field names
            entry_date = db_entry.get('entry_date', db_entry.get('date', ''))
            description = db_entry.get('description', '')
            entry_number = db_entry.get('entry_number', 'N/A')
            total_amount = db_entry.get('total_amount', db_entry.get('amount', 0))
            
            # Get journal entry lines
            lines = db_entry.get('journal_entry_lines', [])
            
            # If no lines, this might be old format - return as-is
            if not lines:
                # Check if this is already in app format
                if 'debit_account' in db_entry and 'credit_account' in db_entry:
                    return {
                        'date': entry_date,
                        'description': description,
                        'debit_account': db_entry.get('debit_account', ''),
                        'credit_account': db_entry.get('credit_account', ''),
                        'amount': float(total_amount) if total_amount else 0,
                        'entry_number': entry_number,
                        'id': db_entry.get('id', '')
                    }
                return None
            
            # Ensure we have exactly 2 lines (debit and credit)
            if len(lines) != 2:
                self.logger.warning(f"Journal entry {entry_number} has {len(lines)} lines, expected 2")
                # Continue anyway, but log it
            
            # Find debit and credit lines
            debit_line = None
            credit_line = None
            
            for line in lines:
                debit_amount = float(line.get('debit_amount', 0))
                credit_amount = float(line.get('credit_amount', 0))
                
                if debit_amount > 0:
                    debit_line = line
                elif credit_amount > 0:
                    credit_line = line
            
            if not debit_line or not credit_line:
                self.logger.warning(f"Journal entry {entry_number} missing debit/credit lines")
                return None
            
            # Get account information - handle both cases: with accounts array or just account_id
            debit_account = self._resolve_account_name(debit_line, accounts_lookup)
            credit_account = self._resolve_account_name(credit_line, accounts_lookup)
            
            # Get amount (use debit amount as the transaction amount)
            amount = float(debit_line.get('debit_amount', 0))
            
            return {
                'date': entry_date,
                'description': description,
                'debit_account': debit_account,
                'credit_account': credit_account,
                'amount': amount,
                'entry_number': entry_number,
                'id': db_entry.get('id', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error transforming journal entry: {e}")
            self.logger.error(f"Entry data: {db_entry}")
            return None
    
    def _resolve_account_name(self, line: Dict[str, Any], accounts_lookup: Optional[Dict[int, Dict[str, Any]]] = None) -> str:
        """Resolve account name from line data"""
        # First, try nested accounts data (if join worked)
        account_info = line.get('accounts', {})
        if account_info:
            return self._format_account_name(account_info)
        
        # Second, try accounts lookup if provided
        account_id = line.get('account_id')
        if account_id and accounts_lookup:
            account_data = accounts_lookup.get(int(account_id), {})
            if account_data:
                return self._format_account_name(account_data)
        
        # Fallback to account ID
        return f"Account ID: {account_id}" if account_id else "Unknown Account"
    
    def app_to_cache_journal_entry(self, app_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Transform application format to cache format (for offline storage)"""
        return {
            'id': app_entry.get('id', ''),
            'date': app_entry.get('date', ''),
            'description': app_entry.get('description', ''),
            'debit_account': app_entry.get('debit_account', ''),
            'credit_account': app_entry.get('credit_account', ''),
            'amount': app_entry.get('amount', 0),
            'entry_number': app_entry.get('entry_number', ''),
            # Keep both old and new field names for compatibility
            'entry_date': app_entry.get('date', ''),
            'total_amount': app_entry.get('amount', 0)
        }
    
    def db_to_cache_journal_entry(self, db_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Transform database format to cache format"""
        # First convert to app format, then to cache format
        app_entry = self.db_to_app_journal_entry(db_entry)
        if app_entry:
            return self.app_to_cache_journal_entry(app_entry)
        else:
            # Fallback: store raw DB format with compatible field names
            return {
                'id': db_entry.get('id', ''),
                'date': db_entry.get('entry_date', db_entry.get('date', '')),
                'description': db_entry.get('description', ''),
                'amount': db_entry.get('total_amount', db_entry.get('amount', 0)),
                'entry_number': db_entry.get('entry_number', ''),
                'entry_date': db_entry.get('entry_date', db_entry.get('date', '')),
                'total_amount': db_entry.get('total_amount', db_entry.get('amount', 0)),
                # Store full data for later transformation
                'raw_data': db_entry
            }
    
    def cache_to_app_journal_entry(self, cache_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Transform cache format to application format"""
        # Check if this cache entry has raw database data
        raw_data = cache_entry.get('raw_data')
        if raw_data:
            # Try to transform the raw database data
            transformed = self.db_to_app_journal_entry(raw_data)
            if transformed:
                return transformed
        
        # Fallback to direct cache data
        return {
            'date': cache_entry.get('date', cache_entry.get('entry_date', '')),
            'description': cache_entry.get('description', ''),
            'debit_account': cache_entry.get('debit_account', ''),
            'credit_account': cache_entry.get('credit_account', ''),
            'amount': cache_entry.get('amount', cache_entry.get('total_amount', 0)),
            'entry_number': cache_entry.get('entry_number', ''),
            'id': cache_entry.get('id', '')
        }
    
    def _format_account_name(self, account_info: Dict[str, Any]) -> str:
        """Format account name for UI display"""
        if not account_info:
            return 'Unknown Account'
        
        code = account_info.get('code', '')
        name = account_info.get('name', '')
        
        if code and name:
            return f"{code} - {name}"
        elif name:
            return name
        elif code:
            return code
        else:
            return 'Unknown Account'
    
    def transform_journal_entries_list(self, db_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of database journal entries to application format"""
        transformed = []
        for entry in db_entries:
            app_entry = self.db_to_app_journal_entry(entry)
            if app_entry:
                transformed.append(app_entry)
        return transformed

# Global transformer instance
data_transformer = DataTransformer() 