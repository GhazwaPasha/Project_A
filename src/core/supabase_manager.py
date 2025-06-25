"""
Clean Supabase Database Manager
Works with the new multi-tenant schema (NEW_SCHEMA.sql)
Supabase-only, no local database or offline functionality
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .config import DatabaseConfig

class SupabaseManager:
    """Clean Supabase database manager for the new schema."""
    
    def __init__(self, user_id: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        # Validate configuration
        DatabaseConfig.validate_config()
        
        # Initialize Supabase client
        self.supabase = create_client(
            DatabaseConfig.SUPABASE_URL,
            DatabaseConfig.SUPABASE_ANON_KEY
        )
        
        self.current_user_id = user_id
        
    def set_user(self, user_id: str):
        """Set the current user ID for operations."""
        self.current_user_id = user_id
        
    # ================================
    # USER PROFILE OPERATIONS
    # ================================
    
    def get_user_profile(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        uid = user_id or self.current_user_id
        if not uid:
            return None
            
        try:
            result = self.supabase.table('user_profiles').select('*').eq('id', uid).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return None
    
    def create_user_profile(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user profile."""
        try:
            result = self.supabase.table('user_profiles').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error creating user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile."""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('user_profiles').update(updates).eq('id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            return False
    
    def is_super_admin(self, user_id: Optional[str] = None) -> bool:
        """Check if user is a super admin."""
        uid = user_id or self.current_user_id
        if not uid:
            return False
            
        profile = self.get_user_profile(uid)
        return profile and profile.get('is_super_admin', False)
    
    # ================================
    # ORGANIZATION OPERATIONS
    # ================================
    
    def get_organizations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all organizations for a user."""
        uid = user_id or self.current_user_id
        if not uid:
            return []
            
        try:
            # Get user's organizations through membership
            result = self.supabase.table('organization_members')\
                .select('organization_id, role, organizations(*)')\
                .eq('user_id', uid)\
                .eq('is_active', True)\
                .execute()
            
            organizations = []
            for member in result.data:
                org = member['organizations']
                org['user_role'] = member['role']
                organizations.append(org)
            
            return organizations
        except Exception as e:
            self.logger.error(f"Error getting user organizations: {e}")
            return []
    
    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID."""
        try:
            result = self.supabase.table('organizations').select('*').eq('id', org_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting organization: {e}")
            return None
    
    def create_organization(self, org_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new organization."""
        try:
            result = self.supabase.table('organizations').insert(org_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error creating organization: {e}")
            return None
    
    def update_organization(self, org_id: str, updates: Dict[str, Any]) -> bool:
        """Update organization."""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('organizations').update(updates).eq('id', org_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error updating organization: {e}")
            return False
    
    # ================================
    # ORGANIZATION MEMBERSHIP OPERATIONS
    # ================================
    
    def get_organization_members(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all members of an organization."""
        try:
            result = self.supabase.table('organization_members')\
                .select('*, user_profiles(id, email, full_name)')\
                .eq('organization_id', org_id)\
                .eq('is_active', True)\
                .execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error getting organization members: {e}")
            return []
    
    def add_organization_member(self, org_id: str, user_id: str, role: str, invited_by: Optional[str] = None) -> bool:
        """Add a user to an organization."""
        try:
            member_data = {
                'organization_id': org_id,
                'user_id': user_id,
                'role': role,
                'invited_by': invited_by or self.current_user_id,
                'joined_at': datetime.now().isoformat()
            }
            result = self.supabase.table('organization_members').insert(member_data).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error adding organization member: {e}")
            return False
    
    def update_member_role(self, org_id: str, user_id: str, new_role: str) -> bool:
        """Update a member's role in an organization."""
        try:
            result = self.supabase.table('organization_members')\
                .update({'role': new_role})\
                .eq('organization_id', org_id)\
                .eq('user_id', user_id)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error updating member role: {e}")
            return False
    
    def remove_organization_member(self, org_id: str, user_id: str) -> bool:
        """Remove a user from an organization."""
        try:
            result = self.supabase.table('organization_members')\
                .update({'is_active': False})\
                .eq('organization_id', org_id)\
                .eq('user_id', user_id)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error removing organization member: {e}")
            return False
    
    def get_user_role_in_organization(self, org_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """Get user's role in a specific organization."""
        uid = user_id or self.current_user_id
        if not uid:
            return None
            
        try:
            result = self.supabase.table('organization_members')\
                .select('role')\
                .eq('organization_id', org_id)\
                .eq('user_id', uid)\
                .eq('is_active', True)\
                .execute()
            return result.data[0]['role'] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting user role: {e}")
            return None
    
    # ================================
    # ACCOUNT OPERATIONS
    # ================================
    
    def get_accounts(self, org_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get chart of accounts for an organization."""
        try:
            query = self.supabase.table('accounts').select('*').eq('organization_id', org_id)
            if active_only:
                query = query.eq('is_active', True)
            result = query.order('code').execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error getting accounts: {e}")
            return []
    
    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        try:
            result = self.supabase.table('accounts').select('*').eq('id', account_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting account: {e}")
            return None
    
    def create_account(self, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new account."""
        try:
            account_data['created_by'] = self.current_user_id
            result = self.supabase.table('accounts').insert(account_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error creating account: {e}")
            return None
    
    def update_account(self, account_id: int, updates: Dict[str, Any]) -> bool:
        """Update account."""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('accounts').update(updates).eq('id', account_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error updating account: {e}")
            return False
    
    # ================================
    # JOURNAL ENTRY OPERATIONS
    # ================================
    
    def get_journal_entries(self, org_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get journal entries for an organization."""
        try:
            query = self.supabase.table('journal_entries')\
                .select('*, journal_entry_lines(*, accounts(code, name))')\
                .eq('organization_id', org_id)\
                .order('entry_date', desc=True)
            
            if limit:
                query = query.limit(limit)
                
            result = query.execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error getting journal entries: {e}")
            return []
    
    def get_journal_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get journal entry by ID with lines."""
        try:
            result = self.supabase.table('journal_entries')\
                .select('*, journal_entry_lines(*, accounts(code, name))')\
                .eq('id', entry_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting journal entry: {e}")
            return None
    
    def create_journal_entry(self, entry_data: Dict[str, Any], lines: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a journal entry with lines."""
        try:
            # Create the entry header
            entry_data['created_by'] = self.current_user_id
            entry_result = self.supabase.table('journal_entries').insert(entry_data).execute()
            
            if not entry_result.data:
                return None
                
            entry = entry_result.data[0]
            entry_id = entry['id']
            
            # Create the lines
            for line in lines:
                line['journal_entry_id'] = entry_id
                
            lines_result = self.supabase.table('journal_entry_lines').insert(lines).execute()
            
            if lines_result.data:
                entry['journal_entry_lines'] = lines_result.data
                return entry
            else:
                # Rollback entry if lines failed
                self.supabase.table('journal_entries').delete().eq('id', entry_id).execute()
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating journal entry: {e}")
            return None
    
    def post_journal_entry(self, entry_id: int) -> bool:
        """Post (finalize) a journal entry."""
        try:
            updates = {
                'is_posted': True,
                'posted_by': self.current_user_id,
                'posted_at': datetime.now().isoformat()
            }
            result = self.supabase.table('journal_entries').update(updates).eq('id', entry_id).execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error posting journal entry: {e}")
            return False
    
    # ================================
    # BUDGET OPERATIONS
    # ================================
    
    def get_budgets(self, org_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get budgets for an organization."""
        try:
            query = self.supabase.table('budgets').select('*').eq('organization_id', org_id)
            if active_only:
                query = query.eq('is_active', True)
            result = query.order('fiscal_year', desc=True).execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error getting budgets: {e}")
            return []
    
    def create_budget(self, budget_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new budget."""
        try:
            budget_data['created_by'] = self.current_user_id
            result = self.supabase.table('budgets').insert(budget_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error creating budget: {e}")
            return None
    
    # ================================
    # PERIOD CLOSING OPERATIONS
    # ================================
    
    def get_period_closings(self, org_id: str) -> List[Dict[str, Any]]:
        """Get period closings for an organization."""
        try:
            result = self.supabase.table('period_closing')\
                .select('*')\
                .eq('organization_id', org_id)\
                .order('end_date', desc=True)\
                .execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error getting period closings: {e}")
            return []
    
    def create_period_closing(self, closing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a period closing."""
        try:
            result = self.supabase.table('period_closing').insert(closing_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error creating period closing: {e}")
            return None
