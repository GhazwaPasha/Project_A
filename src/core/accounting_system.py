"""
Clean Accounting System for Supabase
Works with the new multi-tenant schema (NEW_SCHEMA.sql)
Replaces all the old complex system with a simple, clean implementation
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal

from .supabase_manager import SupabaseManager
from .auth_manager import AuthManager

class AccountingSystem:
    """Clean accounting system using Supabase backend."""
    
    def __init__(self, auth_manager: AuthManager):
        self.logger = logging.getLogger(__name__)
        self.auth_manager = auth_manager
        self.db_manager = auth_manager.db_manager
        self.current_organization_id = None
        
    def set_organization(self, org_id: str) -> bool:
        """Set the current organization for operations."""
        if not self.auth_manager.can_read_accounting_data(org_id):
            self.logger.warning(f"User lacks permission to access organization {org_id}")
            return False
        
        self.current_organization_id = org_id
        return True
    
    def get_current_organization_id(self) -> Optional[str]:
        """Get the current organization ID."""
        return self.current_organization_id
    
    # ================================
    # CHART OF ACCOUNTS
    # ================================
    
    def get_chart_of_accounts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get chart of accounts for current organization."""
        if not self.current_organization_id:
            return []
        
        return self.db_manager.get_accounts(self.current_organization_id, active_only)
    
    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        return self.db_manager.get_account(account_id)
    
    def create_account(self, code: str, name: str, account_type: str, 
                      parent_id: Optional[int] = None, description: str = None) -> Optional[Dict[str, Any]]:
        """Create a new account."""
        if not self.current_organization_id:
            raise ValueError("No organization selected")
        
        if not self.auth_manager.can_modify_accounting_data(self.current_organization_id):
            raise PermissionError("Insufficient permissions to create accounts")
        
        account_data = {
            'organization_id': self.current_organization_id,
            'code': code,
            'name': name,
            'account_type': account_type,
            'parent_id': parent_id,
            'description': description
        }
        
        return self.db_manager.create_account(account_data)
    
    def update_account(self, account_id: int, updates: Dict[str, Any]) -> bool:
        """Update an account."""
        if not self.current_organization_id:
            raise ValueError("No organization selected")
        
        if not self.auth_manager.can_modify_accounting_data(self.current_organization_id):
            raise PermissionError("Insufficient permissions to update accounts")
        
        return self.db_manager.update_account(account_id, updates)
    
    def deactivate_account(self, account_id: int) -> bool:
        """Deactivate an account."""
        return self.update_account(account_id, {'is_active': False})
    
    # ================================
    # JOURNAL ENTRIES
    # ================================
    
    def get_journal_entries(self, limit: Optional[int] = 50) -> List[Dict[str, Any]]:
        """Get journal entries for current organization."""
        if not self.current_organization_id:
            return []
        
        return self.db_manager.get_journal_entries(self.current_organization_id, limit)
    
    def get_journal_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get journal entry by ID with lines."""
        return self.db_manager.get_journal_entry(entry_id)
    
    def create_journal_entry(self, entry_date: date, description: str, 
                           lines: List[Dict[str, Any]], reference: str = None) -> Optional[Dict[str, Any]]:
        """Create a journal entry with lines."""
        if not self.current_organization_id:
            raise ValueError("No organization selected")
        
        if not self.auth_manager.can_modify_accounting_data(self.current_organization_id):
            raise PermissionError("Insufficient permissions to create journal entries")
        
        # Validate lines balance
        total_debits = sum(Decimal(str(line.get('debit_amount', 0))) for line in lines)
        total_credits = sum(Decimal(str(line.get('credit_amount', 0))) for line in lines)
        
        if total_debits != total_credits:
            raise ValueError(f"Journal entry must balance: debits={total_debits}, credits={total_credits}")
        
        # Generate entry number
        entry_number = self._generate_entry_number()
        
        entry_data = {
            'organization_id': self.current_organization_id,
            'entry_number': entry_number,
            'entry_date': entry_date.isoformat(),
            'description': description,
            'reference': reference,
            'total_amount': float(total_debits)
        }
        
        # Add line order to lines
        for i, line in enumerate(lines, 1):
            line['line_order'] = i
        
        return self.db_manager.create_journal_entry(entry_data, lines)
    
    def post_journal_entry(self, entry_id: int) -> bool:
        """Post (finalize) a journal entry."""
        if not self.current_organization_id:
            raise ValueError("No organization selected")
        
        if not self.auth_manager.can_modify_accounting_data(self.current_organization_id):
            raise PermissionError("Insufficient permissions to post journal entries")
        
        return self.db_manager.post_journal_entry(entry_id)
    
    def _generate_entry_number(self) -> str:
        """Generate a unique entry number for the organization."""
        # Get the latest entry number for this organization
        entries = self.db_manager.get_journal_entries(self.current_organization_id, limit=1)
        
        if entries:
            last_number = entries[0].get('entry_number', 'JE-0000')
            try:
                # Extract number from format like "JE-0001"
                number_part = int(last_number.split('-')[-1])
                next_number = number_part + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"JE-{next_number:04d}"
    
    # ================================
    # ACCOUNT BALANCES AND REPORTING
    # ================================
    
    def get_account_balance(self, account_id: int, as_of_date: Optional[date] = None) -> Decimal:
        """Get account balance as of a specific date."""
        if not self.current_organization_id:
            return Decimal('0')
        
        # This would typically involve summing journal entry lines
        # For now, returning 0 as we'd need to implement the calculation
        # based on journal_entry_lines table
        return Decimal('0')
    
    def get_trial_balance(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get trial balance for current organization."""
        if not self.current_organization_id:
            return []
        
        accounts = self.get_chart_of_accounts()
        trial_balance = []
        
        for account in accounts:
            balance = self.get_account_balance(account['id'], as_of_date)
            trial_balance.append({
                'account_id': account['id'],
                'account_code': account['code'],
                'account_name': account['name'],
                'account_type': account['account_type'],
                'balance': float(balance)
            })
        
        return trial_balance
    
    def get_general_ledger(self, account_id: Optional[int] = None, 
                          start_date: Optional[date] = None, 
                          end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get general ledger entries."""
        if not self.current_organization_id:
            return []
        
        # This would involve querying journal_entry_lines with filters
        # For now, returning empty list as full implementation would be complex
        return []
    
    # ================================
    # BUDGETS
    # ================================
    
    def get_budgets(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get budgets for current organization."""
        if not self.current_organization_id:
            return []
        
        return self.db_manager.get_budgets(self.current_organization_id, active_only)
    
    def create_budget(self, name: str, fiscal_year: int, start_date: date, 
                     end_date: date, description: str = None) -> Optional[Dict[str, Any]]:
        """Create a new budget."""
        if not self.current_organization_id:
            raise ValueError("No organization selected")
        
        if not self.auth_manager.can_modify_accounting_data(self.current_organization_id):
            raise PermissionError("Insufficient permissions to create budgets")
        
        budget_data = {
            'organization_id': self.current_organization_id,
            'name': name,
            'description': description,
            'fiscal_year': fiscal_year,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        return self.db_manager.create_budget(budget_data)
    
    # ================================
    # PERIOD CLOSING
    # ================================
    
    def get_period_closings(self) -> List[Dict[str, Any]]:
        """Get period closings for current organization."""
        if not self.current_organization_id:
            return []
        
        return self.db_manager.get_period_closings(self.current_organization_id)
    
    def create_period_closing(self, period_name: str, start_date: date, 
                            end_date: date, notes: str = None) -> Optional[Dict[str, Any]]:
        """Create a period closing."""
        if not self.current_organization_id:
            raise ValueError("No organization selected")
        
        if not self.auth_manager.can_close_periods(self.current_organization_id):
            raise PermissionError("Insufficient permissions to close periods")
        
        closing_data = {
            'organization_id': self.current_organization_id,
            'period_name': period_name,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'notes': notes
        }
        
        return self.db_manager.create_period_closing(closing_data)
    
    # ================================
    # UTILITY METHODS
    # ================================
    
    def validate_permissions(self, operation: str) -> bool:
        """Validate user permissions for an operation."""
        if not self.current_organization_id:
            return False
        
        if operation in ['read']:
            return self.auth_manager.can_read_accounting_data(self.current_organization_id)
        elif operation in ['create', 'update', 'delete']:
            return self.auth_manager.can_modify_accounting_data(self.current_organization_id)
        elif operation in ['close_period']:
            return self.auth_manager.can_close_periods(self.current_organization_id)
        elif operation in ['manage_org']:
            return self.auth_manager.can_manage_organization(self.current_organization_id)
        
        return False
    
    def get_organization_info(self) -> Optional[Dict[str, Any]]:
        """Get current organization information."""
        if not self.current_organization_id:
            return None
        
        return self.db_manager.get_organization(self.current_organization_id)
    
    def get_user_role(self) -> Optional[str]:
        """Get current user's role in the current organization."""
        if not self.current_organization_id:
            return None
        
        return self.auth_manager.get_user_role_in_organization(self.current_organization_id)
