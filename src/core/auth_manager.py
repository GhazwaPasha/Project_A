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
        """Check if user can read accounting data"""
        return self.has_permission(org_id, ['organization_owner', 'accountant', 'member'])
    
    def can_modify_accounting_data(self, org_id: str) -> bool:
        """Check if user can modify accounting data"""
        return self.has_permission(org_id, ['organization_owner', 'accountant'])
    
    def can_manage_organization(self, org_id: str) -> bool:
        """Check if user can manage organization"""
        return self.has_permission(org_id, ['organization_owner'])
    
    def can_close_periods(self, org_id: str) -> bool:
        """Check if user can close periods"""
        return self.has_permission(org_id, ['organization_owner'])
    
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
            time.sleep(0.5)
            
            if org_type == "personal":
                self.logger.info("Creating personal workspace")
                # Create personal workspace
                org_data = {
                    'name': f"Personal Workspace",
                    'description': 'Personal accounting workspace',
                    'settings': {'workspace_type': 'personal'}
                }
                
                self.logger.info(f"Creating organization with data: {org_data}")
                org = db_manager.create_organization(org_data)
                self.logger.info(f"Organization created: {org}")
                
                if org:
                    # Add user as organization owner
                    self.logger.info(f"Adding user {user_id} as organization owner")
                    membership = db_manager.add_organization_member(
                        org['id'], user_id, 'organization_owner'
                    )
                    self.logger.info(f"Membership created: {membership}")
                    return {'type': 'personal', 'organization': org, 'membership': membership}
                else:
                    self.logger.error("Failed to create organization")
                    return {'error': 'Failed to create personal workspace'}
                
            elif org_type == "new":
                # Create new organization
                if not org_name:
                    return {'error': 'Organization name required for new organization'}
                
                self.logger.info(f"Creating new organization: {org_name}")
                org_data = {
                    'name': org_name,
                    'description': f'Organization: {org_name}',
                    'settings': {'workspace_type': 'organization'}
                }
                
                org = db_manager.create_organization(org_data)
                if org:
                    # Add user as organization owner
                    membership = db_manager.add_organization_member(
                        org['id'], user_id, 'organization_owner'
                    )
                    return {'type': 'new', 'organization': org, 'membership': membership}
                else:
                    return {'error': 'Failed to create organization'}
                
            elif org_type == "existing":
                # Join existing organization via invitation code
                # For now, return a placeholder - this would need invitation system
                return {
                    'type': 'existing', 
                    'message': 'Invitation system not yet implemented',
                    'invitation_code': invitation_code
                }
            
            return {'error': f'Unknown organization type: {org_type}'}
            
        except Exception as e:
            self.logger.error(f"Organization setup error: {e}")
            import traceback
            self.logger.error(f"Organization setup traceback: {traceback.format_exc()}")
            return {'error': str(e)}
