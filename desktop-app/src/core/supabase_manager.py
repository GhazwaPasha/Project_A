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
    
    def __init__(self, user_id: Optional[str] = None, authenticated_client: Any = None):
        self.logger = logging.getLogger(__name__)
        
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        # Use authenticated client if provided, otherwise create new one
        if authenticated_client:
            self.supabase = authenticated_client
            self.logger.debug("Using authenticated Supabase client")
        else:
            # Validate configuration
            DatabaseConfig.validate_config()
            
            # Initialize Supabase client
            self.supabase = create_client(
                DatabaseConfig.SUPABASE_URL,
                DatabaseConfig.SUPABASE_ANON_KEY
            )
            self.logger.debug("Created new Supabase client")
        
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
            # First try the user_profiles table
            result = self.supabase.table('user_profiles').select('*').eq('id', uid).execute()
            if result.data:
                return result.data[0]
            
            # Fallback to users table if profile doesn't exist yet
            users_result = self.supabase.table('users').select('*').eq('id', uid).execute()
            if users_result.data:
                user_data = users_result.data[0]
                # Try to create profile from user data
                profile_data = {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'full_name': user_data.get('full_name'),
                    'avatar_url': user_data.get('avatar_url'),
                    'phone': user_data.get('phone'),
                    'is_super_admin': False,
                    'preferences': {}
                }
                
                # Try to create the profile
                try:
                    profile_result = self.supabase.table('user_profiles').insert(profile_data).execute()
                    return profile_result.data[0] if profile_result.data else profile_data
                except Exception as e:
                    self.logger.warning(f"Could not create user profile, returning user data: {e}")
                    return profile_data
                    
            return None
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
            self.logger.debug("is_super_admin: No user ID available")
            return False
            
        profile = self.get_user_profile(uid)
        is_admin = profile and profile.get('is_super_admin', False)
        self.logger.debug(f"is_super_admin check for user {uid}: profile={bool(profile)}, is_super_admin={is_admin}")
        return is_admin
    
    # ================================
    # ORGANIZATION OPERATIONS
    # ================================
    
    def get_organizations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all organizations for a user."""
        uid = user_id or self.current_user_id
        if not uid:
            self.logger.error("get_organizations: No user ID available")
            return []
            
        try:
            self.logger.debug(f"Getting organizations for user: {uid}")
            
            # Use the clean Supabase helper function
            try:
                result = self.supabase.rpc('get_user_organizations').execute()
                self.logger.debug(f"RPC get_user_organizations result: {len(result.data) if result.data else 0} records")
                
                organizations = []
                for member_data in result.data:
                    org_id = member_data.get('organization_id')
                    if org_id:
                        # Get full organization data
                        org_result = self.supabase.table('organizations').select('*').eq('id', org_id).execute()
                        if org_result.data:
                            org = org_result.data[0]
                            org['user_role'] = member_data.get('role', 'member')
                            # Add organization type information
                            org['organization_type'] = self.get_organization_type(org)
                            org['is_personal_workspace'] = self.is_personal_workspace(org)
                            organizations.append(org)
                            
                self.logger.info(f"Found {len(organizations)} organizations for user {uid}")
                return organizations
                
            except Exception as rpc_error:
                self.logger.warning(f"RPC call failed: {rpc_error}, falling back to direct query")
                
                # Fallback: Direct query
                result = self.supabase.table('organization_members')\
                    .select('organization_id, role, organizations(*)')\
                    .eq('user_id', uid)\
                    .eq('is_active', True)\
                    .execute()
                
                self.logger.debug(f"Organization members query result: {len(result.data)} records")
                
                organizations = []
                for member in result.data:
                    if member.get('organizations'):
                        org = member['organizations']
                        org['user_role'] = member['role']
                        # Add organization type information
                        org['organization_type'] = self.get_organization_type(org)
                        org['is_personal_workspace'] = self.is_personal_workspace(org)
                        organizations.append(org)
                        org_type = org.get('organization_type', 'unknown')
                        self.logger.debug(f"Added organization: {org.get('name', 'Unknown')} (Role: {member['role']}, Type: {org_type})")
                    else:
                        self.logger.warning(f"Member record missing organization data: {member}")
                
                self.logger.info(f"Found {len(organizations)} organizations for user {uid}")
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
            # Filter out fields that don't exist in the database schema
            # Note: 'is_postable' field is now stored in the database
            filtered_data = {k: v for k, v in account_data.items()}
            filtered_data['created_by'] = self.current_user_id
            
            # Convert account_type to lowercase to match database enum
            if 'account_type' in filtered_data:
                filtered_data['account_type'] = filtered_data['account_type'].lower()
            
            # Handle group field - ensure it's properly formatted
            if 'group' in filtered_data:
                group_value = filtered_data['group']
                # Convert empty string to None for database
                if group_value == '':
                    filtered_data['group'] = None
                print(f"🔍 DEBUG: Group field in create: {filtered_data['group']}")
            
            print(f"Debug: SupabaseManager.create_account attempting insert with filtered data: {filtered_data}")
            result = self.supabase.table('accounts').insert(filtered_data).execute()
            print(f"Debug: SupabaseManager.create_account result: {result}")
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Debug: SupabaseManager.create_account ERROR: {e}")
            self.logger.error(f"Error creating account: {e}")
            return None
    
    def update_account(self, account_id: int, updates: Dict[str, Any]) -> bool:
        """Update account."""
        try:
            print(f"🔍 DEBUG: SupabaseManager.update_account - account_id: {account_id}, updates: {updates}")
            
            # Filter out fields that don't exist in the database schema
            # Note: 'is_postable' field is now stored in the database
            filtered_updates = {k: v for k, v in updates.items()}
            filtered_updates['updated_at'] = datetime.now().isoformat()
            
            print(f"🔍 DEBUG: SupabaseManager filtered_updates: {filtered_updates}")
            
            # Convert account_type to lowercase to match database enum
            if 'account_type' in filtered_updates:
                filtered_updates['account_type'] = filtered_updates['account_type'].lower()
            
            # Handle group field - ensure it's properly formatted
            if 'group' in filtered_updates:
                group_value = filtered_updates['group']
                # Convert empty string to None for database
                if group_value == '':
                    filtered_updates['group'] = None
                print(f"🔍 DEBUG: Group field in update: {filtered_updates['group']}")
            
            result = self.supabase.table('accounts').update(filtered_updates).eq('id', account_id).execute()
            print(f"🔍 DEBUG: Supabase update result: {result.data if result else 'None'}")
            
            success = len(result.data) > 0
            print(f"🔍 DEBUG: Update success: {success}")
            return success
        except Exception as e:
            print(f"🔍 DEBUG: SupabaseManager.update_account exception: {e}")
            self.logger.error(f"Error updating account: {e}")
            return False
    
    def delete_account(self, account_id: int) -> bool:
        """Delete account (soft delete by setting is_active to False)."""
        try:
            # Soft delete - set is_active to False instead of actual deletion
            # This preserves referential integrity and audit trails
            result = self.supabase.table('accounts')\
                .update({'is_active': False, 'updated_at': datetime.now().isoformat()})\
                .eq('id', account_id)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return False

    # ================================
    # JOURNAL ENTRY OPERATIONS
    # ================================
    
    def get_journal_entries(self, org_id: str, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get journal entries for an organization with optional date filtering."""
        try:
            # Query with proper joins to include account information
            query = self.supabase.table('journal_entries')\
                .select('*, journal_entry_lines(*, accounts(code, name))')\
                .eq('organization_id', org_id)\
                .order('entry_date', desc=True)
            
            # Apply date filtering if provided
            if start_date:
                query = query.gte('entry_date', start_date)
            if end_date:
                query = query.lte('entry_date', end_date)
            
            if limit:
                query = query.limit(limit)
                
            result = query.execute()
            
            # Debug: Log what we got
            self.logger.info(f"Journal entries query returned {len(result.data)} entries")
            
            if result.data:
                # Check if journal_entry_lines are populated
                first_entry = result.data[0]
                lines = first_entry.get('journal_entry_lines', [])
                self.logger.info(f"First entry has {len(lines)} lines")
                
                if lines:
                    # Check if accounts data is present
                    first_line = lines[0]
                    accounts = first_line.get('accounts', {})
                    self.logger.info(f"First line accounts data: {accounts}")
                    if not accounts:
                        self.logger.warning("No accounts data in journal entry lines - check RLS policies")
                else:
                    self.logger.warning("No journal_entry_lines found - possible RLS policy issue")
            
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
    
    # ================================
    # ORGANIZATION TYPE AND PERSONAL WORKSPACE DETECTION
    # ================================
    
    def is_personal_workspace(self, organization: Dict[str, Any]) -> bool:
        """Check if an organization is a personal workspace (single-member organization)."""
        try:
            org_id = organization.get('id')
            if not org_id:
                return False
            
            # Method 1: Check organization_type column if it exists
            org_type = organization.get('organization_type')
            if org_type:
                return org_type == 'personal'
            
            # Method 2: Check metadata for organization_type
            metadata = organization.get('metadata', {})
            if isinstance(metadata, dict):
                return metadata.get('organization_type') == 'personal'
            
            # Method 3: Check metadata JSON string
            if isinstance(metadata, str):
                try:
                    import json
                    meta_dict = json.loads(metadata)
                    return meta_dict.get('organization_type') == 'personal'
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Method 4: Fallback - count active members
            return self._count_organization_members(org_id) == 1
            
        except Exception as e:
            self.logger.error(f"Error checking if organization is personal workspace: {e}")
            return False
    
    def _count_organization_members(self, org_id: str) -> int:
        """Count active members in an organization."""
        try:
            result = self.supabase.table('organization_members')\
                .select('id', count='exact')\
                .eq('organization_id', org_id)\
                .eq('is_active', True)\
                .execute()
            return result.count or 0
        except Exception as e:
            self.logger.error(f"Error counting organization members: {e}")
            return 0
    
    def get_organization_type(self, organization: Dict[str, Any]) -> str:
        """Get the type of organization ('personal' or 'team')."""
        if self.is_personal_workspace(organization):
            return 'personal'
        return 'team'
    
    def get_user_personal_workspace(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the user's personal workspace organization."""
        uid = user_id or self.current_user_id
        if not uid:
            return None
        
        try:
            # Get all user organizations
            organizations = self.get_organizations(uid)
            
            # Find the personal workspace
            for org in organizations:
                if self.is_personal_workspace(org):
                    return org
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting user personal workspace: {e}")
            return None
    
    def get_user_team_organizations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all team (multi-member) organizations for a user."""
        uid = user_id or self.current_user_id
        if not uid:
            return []
        
        try:
            # Get all user organizations
            organizations = self.get_organizations(uid)
            
            # Filter for team organizations only
            team_orgs = []
            for org in organizations:
                if not self.is_personal_workspace(org):
                    team_orgs.append(org)
            
            return team_orgs
        except Exception as e:
            self.logger.error(f"Error getting user team organizations: {e}")
            return []

    # ================================
    # ORGANIZATION OPERATIONS (CONTINUED)
    # ================================
