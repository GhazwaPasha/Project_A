"""
Clean Authentication Manager for Supabase
Works with the new multi-tenant schema (NEW_SCHEMA.sql)
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .config import DatabaseConfig
from .supabase_manager import SupabaseManager

class AuthManager:
    """Clean authentication manager with Supabase integration"""
    
    def __init__(self):
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
        
        self.db_manager = None
        self.current_user = None
        self.current_session = None
        
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email/password"""
        try:
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result.user:
                self.current_user = result.user
                self.current_session = result.session
                
                # Initialize database manager with authenticated client
                self.db_manager = SupabaseManager(result.user.id, authenticated_client=self.supabase)
                
                # Update last sign in
                self.db_manager.update_user_profile(result.user.id, {
                    'last_sign_in_at': datetime.now().isoformat()
                })
                
                # Get user's organizations
                organizations = self.get_user_organizations()
                self.logger.debug(f"Retrieved {len(organizations)} organizations for user {result.user.email}")
                
                # Convert user object to dict
                user_data = {
                    'id': result.user.id,
                    'email': result.user.email,
                    'created_at': result.user.created_at,
                    'updated_at': result.user.updated_at,
                    'email_confirmed_at': getattr(result.user, 'email_confirmed_at', None),
                    'last_sign_in_at': getattr(result.user, 'last_sign_in_at', None)
                }
                
                return {
                    'success': True,
                    'user': user_data,
                    'organizations': organizations,
                    'session': result.session,
                    'message': 'Successfully signed in'
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid credentials',
                    'message': 'Email or password is incorrect'
                }
                
        except Exception as e:
            self.logger.error(f"Sign in error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Sign in failed'
            }
    
    def sign_up(self, email: str, password: str, full_name: str = None, 
                first_name: str = None, last_name: str = None,
                organization_type: str = "personal", organization_name: str = None,
                invitation_code: str = None) -> Dict[str, Any]:
        """Sign up new user with organization setup"""
        try:
            # Combine first and last name if provided
            if first_name and last_name:
                full_name = f"{first_name} {last_name}"
            elif not full_name:
                full_name = email.split('@')[0]
            
            self.logger.info(f"Starting signup for email: {email}")
            
            # Sign up with user metadata
            result = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "first_name": first_name or "",
                        "last_name": last_name or ""
                    }
                }
            })
            
            self.logger.info(f"Supabase auth.sign_up result: user={result.user is not None}")
            
            if result.user:
                self.logger.info(f"User created successfully: {result.user.id}")
                
                # The user profile will be created automatically by the trigger
                # Wait a moment and then set up organization
                import time
                time.sleep(1)  # Wait for trigger to complete
                
                self.logger.info("Creating SupabaseManager for organization setup")
                temp_manager = SupabaseManager(result.user.id, authenticated_client=self.supabase)
                
                self.logger.info(f"Setting up organization: type={organization_type}")
                
                # Handle organization setup based on type
                org_result = self._setup_user_organization(
                    temp_manager, result.user.id, organization_type, 
                    organization_name, invitation_code
                )
                
                self.logger.info(f"Organization setup result: {org_result}")
                
                return {
                    'success': True,
                    'user': result.user,
                    'organization': org_result,
                    'message': 'Account created successfully'
                }
            else:
                self.logger.error("Supabase auth.sign_up returned no user")
                return {
                    'success': False,
                    'error': 'Failed to create account',
                    'message': 'Account creation failed'
                }
                
        except Exception as e:
            self.logger.error(f"Sign up error: {e}")
            import traceback
            self.logger.error(f"Sign up traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f"Database error saving new user",
                'message': 'Account creation failed'
            }
    
    def sign_out(self) -> Dict[str, Any]:
        """Sign out current user"""
        try:
            result = self.supabase.auth.sign_out()
            self.current_user = None
            self.current_session = None
            self.db_manager = None
            
            return {
                'success': True,
                'message': 'Successfully signed out'
            }
        except Exception as e:
            self.logger.error(f"Sign out error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Sign out failed'
            }
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        if not self.current_user:
            return None
            
        return {
            'id': self.current_user.id,
            'email': self.current_user.email,
            'created_at': self.current_user.created_at
        }
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get current user's profile"""
        if not self.current_user or not self.db_manager:
            return None
        
        return self.db_manager.get_user_profile()
    
    def get_user_organizations(self) -> List[Dict[str, Any]]:
        """Get organizations for current user"""
        if not self.current_user:
            self.logger.debug("🔍 Debug: get_user_organizations - No current user")
            return []
        
        if not self.db_manager:
            self.logger.debug("🔍 Debug: get_user_organizations - No db_manager")
            return []
        
        self.logger.debug(f"🔍 Debug: Getting organizations for user {self.current_user.email}")
        organizations = self.db_manager.get_organizations()
        self.logger.debug(f"🔍 Debug: Found {len(organizations)} organizations")
        
        return organizations
    
    def is_super_admin(self) -> bool:
        """Check if current user is super admin"""
        if not self.current_user or not self.db_manager:
            self.logger.debug("🔍 Debug: is_super_admin - No current user or db_manager")
            return False
        
        user_id = self.current_user.id
        self.logger.debug(f"🔍 Debug: Checking super admin status for user {user_id}")
        result = self.db_manager.is_super_admin(user_id)
        self.logger.debug(f"🔍 Debug: Super admin check result: {result}")
        return result
    
    def get_user_role_in_organization(self, org_id: str) -> Optional[str]:
        """Get current user's role in specific organization"""
        if not self.current_user or not self.db_manager:
            return None
        
        return self.db_manager.get_user_role_in_organization(org_id)
    
    def has_permission(self, org_id: str, required_roles: List[str]) -> bool:
        """Check if user has required permission in organization"""
        if self.is_super_admin():
            return True
        
        user_role = self.get_user_role_in_organization(org_id)
        return user_role in required_roles if user_role else False
    
    def can_read_accounting_data(self, org_id: str) -> bool:
        """Check if user can read accounting data - use database permissions"""
        return self.can_access_page('journal_entries', org_id, 'view')
    
    def can_modify_accounting_data(self, org_id: str) -> bool:
        """Check if user can modify accounting data - use database permissions"""
        return self.can_access_page('journal_entries', org_id, 'create') or self.can_access_page('journal_entries', org_id, 'edit')
    
    def can_manage_organization(self, org_id: str) -> bool:
        """Check if user can manage organization - use database permissions"""
        return self.can_access_page('organization_settings', org_id, 'edit')
    
    def can_close_periods(self, org_id: str) -> bool:
        """Check if user can close periods - use database permissions"""
        return self.can_access_page('settings', org_id, 'edit')
    
    def can_create_journal_entries(self, org_id: str) -> bool:
        """Check if user can create journal entries"""
        return self.can_access_page('journal_entries', org_id, 'create')
    
    def can_create_accounts(self, org_id: str) -> bool:
        """Check if user can create accounts"""
        return self.can_access_page('accounts', org_id, 'create')
    
    def can_edit_accounts(self, org_id: str) -> bool:
        """Check if user can edit accounts"""
        return self.can_access_page('accounts', org_id, 'edit')
    
    def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            result = self.supabase.auth.reset_password_email(email)
            return {
                'success': True,
                'message': 'Password reset email sent'
            }
        except Exception as e:
            self.logger.error(f"Password reset error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send password reset email'
            }
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information"""
        if not self.current_session:
            return None
            
        return {
            'access_token': self.current_session.access_token,
            'refresh_token': self.current_session.refresh_token,
            'expires_at': self.current_session.expires_at,
            'user': self.get_current_user()
        }
    
    def _setup_user_organization(self, db_manager: SupabaseManager, user_id: str, 
                                org_type: str, org_name: str = None, 
                                invitation_code: str = None) -> Dict[str, Any]:
        """Setup user organization based on signup type"""
        try:
            self.logger.info(f"Setting up organization for user {user_id}, type: {org_type}")
            
            # Wait a moment for the user profile trigger to complete
            import time
            time.sleep(1.0)  # Increased wait time for trigger completion
            
            # Every user automatically gets a personal workspace from the database trigger
            # We should always find their auto-created personal workspace first
            self.logger.info("Looking for auto-created personal workspace")
            
            try:
                # Find the user's personal workspace (created by trigger)
                result = self.supabase.table('organizations')\
                    .select('*')\
                    .eq('settings->>workspace_type', 'personal')\
                    .in_('id', 
                         self.supabase.table('organization_members')\
                         .select('organization_id')\
                         .eq('user_id', user_id)\
                         .eq('role', 'organization_owner')
                    )\
                    .execute()
                
                personal_workspace = result.data[0] if result.data else None
                
                if personal_workspace:
                    self.logger.info(f"Found auto-created personal workspace: {personal_workspace['id']}")
                else:
                    self.logger.warning("No auto-created personal workspace found - creating one manually")
                    # Fallback: create personal workspace manually if trigger failed
                    org_data = {
                        'name': f"Personal Workspace",
                        'description': 'Personal accounting workspace',
                        'settings': {'workspace_type': 'personal', 'created_manually': True}
                    }
                    
                    personal_workspace = db_manager.create_organization(org_data)
                    if personal_workspace:
                        db_manager.add_organization_member(
                            personal_workspace['id'], user_id, 'organization_owner'
                        )
                    
            except Exception as e:
                self.logger.error(f"Error finding personal workspace: {e}")
                return {'error': 'Failed to find or create personal workspace'}
            
            # Now handle the requested organization type
            if org_type == "personal" or not org_type:
                # User just wants their personal workspace (this is the default)
                self.logger.info("User choosing personal workspace only")
                return {
                    'type': 'personal', 
                    'organization': personal_workspace,
                    'message': 'Personal workspace ready'
                }
                
            elif org_type == "new":
                # User wants to create an additional multi-user organization
                if not org_name:
                    return {'error': 'Organization name required for new organization'}
                
                self.logger.info(f"Creating additional multi-user organization: {org_name}")
                org_data = {
                    'name': org_name,
                    'description': f'Multi-user organization: {org_name}',
                    'settings': {'workspace_type': 'organization'}
                }
                
                new_org = db_manager.create_organization(org_data)
                if new_org:
                    # Add user as organization owner
                    membership = db_manager.add_organization_member(
                        new_org['id'], user_id, 'organization_owner'
                    )
                    return {
                        'type': 'new', 
                        'organization': new_org, 
                        'personal_workspace': personal_workspace,
                        'membership': membership,
                        'message': f'Created organization "{org_name}" - you also have access to your personal workspace'
                    }
                else:
                    return {'error': 'Failed to create organization'}
                
            elif org_type == "existing":
                # Join existing organization via invitation code (personal workspace still exists)
                # For now, return a placeholder - this would need invitation system
                return {
                    'type': 'existing', 
                    'personal_workspace': personal_workspace,
                    'message': 'Invitation system not yet implemented - you can use your personal workspace',
                    'invitation_code': invitation_code
                }
            
            return {'error': f'Unknown organization type: {org_type}'}
            
        except Exception as e:
            self.logger.error(f"Organization setup error: {e}")
            import traceback
            self.logger.error(f"Organization setup traceback: {traceback.format_exc()}")
            return {'error': str(e)}

    def get_page_permissions(self, page_key: str, org_id: str) -> Dict[str, Any]:
        """Get user's permissions for a specific page in an organization"""
        try:
            if not self.db_manager:
                self.logger.warning("No database manager available for permission check")
                return {'view': False, 'create': False, 'edit': False, 'delete': False}
            
            # Call the database function to get permissions
            result = self.supabase.rpc('get_page_permissions', {
                'page_key': page_key,
                'org_id': org_id
            })
            
            if result.data:
                return result.data
            else:
                self.logger.warning(f"No permissions found for page {page_key} in org {org_id}")
                return {'view': False, 'create': False, 'edit': False, 'delete': False}
                
        except Exception as e:
            self.logger.error(f"Failed to get page permissions for {page_key}: {e}")
            return {'view': False, 'create': False, 'edit': False, 'delete': False}
    
    def can_access_page(self, page_key: str, org_id: str, permission_type: str = 'view') -> bool:
        """Check if the current user can access a specific page with given permission"""
        try:
            if not self.db_manager:
                print(f"🔍 DEBUG can_access_page: No database manager available")
                self.logger.warning("No database manager available for permission check")
                return False
            
            print(f"🔍 DEBUG can_access_page: Checking {page_key} for org {org_id} with permission {permission_type}")
            
            # FIRST: Try database RPC call (if available)
            try:
                print(f"🔍 DEBUG can_access_page: Attempting RPC call...")
                result = self.supabase.rpc('can_access_page', {
                    'p_page_key': page_key,
                    'p_org_id': org_id,
                    'p_permission_type': permission_type
                }).execute()
                
                print(f"🔍 DEBUG can_access_page: RPC success! Result = {result.data}")
                return bool(result.data) if result.data is not None else False
                
            except Exception as rpc_error:
                print(f"🔍 DEBUG can_access_page: RPC failed - {rpc_error}")
                # Fall through to role-based check
            
            # FALLBACK: Use role-based permission check
            try:
                print(f"🔍 DEBUG can_access_page: Using role-based fallback...")
                # Try to get user's role in the organization
                user_role = self.get_user_role_in_organization(org_id)
                if not user_role:
                    print(f"🔍 DEBUG can_access_page: No role found for user in org {org_id}")
                    return False
                
                # Define permissions based on role and page
                role_permissions = {
                    'organization_owner': {
                        'dashboard': ['view', 'create', 'edit'],
                        'journal_entries': ['view', 'create', 'edit', 'delete'],
                        'accounts': ['view', 'create', 'edit', 'delete'],
                        'reports': ['view', 'create'],
                        'settings': ['view', 'edit'],
                        'period_closing': ['view', 'create', 'edit'],
                    },
                    'accountant': {
                        'dashboard': ['view'],
                        'journal_entries': ['view', 'create', 'edit'],
                        'accounts': ['view'],
                        'reports': ['view'],
                        'settings': ['view'],
                    },
                    'member': {
                        'dashboard': ['view'],
                        'reports': ['view'],
                    }
                }
                
                # Check if user has permission
                page_perms = role_permissions.get(user_role, {}).get(page_key, [])
                has_permission = permission_type in page_perms
                
                print(f"🔍 DEBUG can_access_page: Role-based check - {user_role} -> {page_key} -> {permission_type} = {has_permission}")
                return has_permission
                
            except Exception as role_error:
                print(f"🔍 DEBUG can_access_page: Role check error = {role_error}")
                return False
                
        except Exception as e:
            print(f"🔍 DEBUG can_access_page: Exception = {e}")
            self.logger.error(f"Failed to check page access for {page_key}: {e}")
            return False

    def get_user_page_permissions(self, org_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all page permissions for the current user in an organization"""
        try:
            if not self.db_manager:
                self.logger.warning("No database manager available for permission check")
                return {}
            
            # Define all pages that need permission checks
            pages = [
                'dashboard', 'accounts', 'journal_entries', 'reports', 
                'settings', 'user_management', 'team_management', 'organization_settings'
            ]
            
            permissions = {}
            for page in pages:
                permissions[page] = self.get_page_permissions(page, org_id)
            
            return permissions
                
        except Exception as e:
            self.logger.error(f"Failed to get user page permissions: {e}")
            return {}
    
    def set_database_context(self, user_id: str, organization_id: str, role: str):
        """Set PostgreSQL context for RLS policies"""
        try:
            if not self.supabase:
                self.logger.warning("No Supabase client available for database context")
                return
            
            # Call the set_app_context RPC function to set PostgreSQL session variables
            result = self.supabase.rpc('set_app_context', {
                'user_id': user_id,
                'organization_id': organization_id,
                'role': role
            }).execute()
            
            self.logger.info(f"✅ Database context set for user {user_id}, org {organization_id}, role {role}")
            
        except Exception as e:
            self.logger.error(f"Failed to set database context: {e}")
            # Don't raise the exception - this shouldn't break organization switching
