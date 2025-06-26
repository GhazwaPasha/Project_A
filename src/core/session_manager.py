"""
Clean Session Manager with proper organization type handling
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

class SessionManager:
    """Manages user session state and organization context with proper organization type handling"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self.current_organization = None
        self.current_role = None
        self.session_data = {}

    def initialize_session(self, user_data: Dict[str, Any]) -> bool:
        """Initialize a new session with user data"""
        try:
            if not user_data:
                return False
                
            # Set basic session data
            self.session_data = {
                'user_id': user_data.get('id'),
                'email': user_data.get('email'),
                'last_activity': datetime.now().isoformat()
            }
            
            # Get organizations and set initial active organization
            organizations = self.auth_manager.get_user_organizations()
            if not organizations:
                self.logger.warning(f"No organizations found for user {user_data.get('email')}")
                return False
            
            # Try to set active organization based on preference:
            # 1. First team organization (if exists)
            # 2. Personal workspace
            # 3. Any available organization
            team_orgs = [org for org in organizations if self._get_org_type(org) == 'team']
            personal_workspace = next((org for org in organizations if self._get_org_type(org) == 'personal'), None)
            
            target_org = None
            if team_orgs:
                target_org = team_orgs[0]
                self.logger.info("Setting team organization as active")
            elif personal_workspace:
                target_org = personal_workspace
                self.logger.info("Setting personal workspace as active")
            elif organizations:
                target_org = organizations[0]
                self.logger.info("Setting first available organization as active")
                
            if target_org:
                return self.set_active_organization(target_org['id'])
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize session: {e}")
            return False

    def set_active_organization(self, org_id: str) -> bool:
        """Set the active organization and update session context"""
        try:
            if not self.auth_manager:
                return False
                
            org_data = self.auth_manager.db_manager.get_organization(org_id)
            if not org_data:
                self.logger.error(f"Organization {org_id} not found")
                return False
                
            # Get user's role in organization
            role = self.auth_manager.get_user_role_in_organization(org_id)
            if not role:
                self.logger.error(f"No role found for user in organization {org_id}")
                return False
                
            # Set organization context
            self.current_organization = org_data
            self.current_role = role
            
            # Update session data
            self.session_data.update({
                'organization_id': org_id,
                'organization_name': org_data.get('name'),
                'organization_type': self._get_org_type(org_data),
                'role': role,
                'last_activity': datetime.now().isoformat()
            })
            
            # Set database context for RLS
            try:
                self.auth_manager.set_database_context(
                    user_id=self.session_data['user_id'],
                    organization_id=org_id,
                    role=role
                )
            except Exception as e:
                self.logger.error(f"Failed to set database context: {e}")
                # Continue anyway - database context error shouldn't fail org switch
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set active organization: {e}")
            return False

    def _get_org_type(self, org_data: Dict[str, Any]) -> str:
        """Determine organization type using multiple methods"""
        if not org_data:
            return 'team'  # Default to team if no data
            
        # Method 1: Check explicit organization_type field
        if 'organization_type' in org_data:
            return org_data['organization_type']
            
        # Method 2: Check if marked as personal workspace
        if org_data.get('is_personal_workspace'):
            return 'personal'
            
        # Method 3: Use SupabaseManager's logic if available
        if hasattr(self.auth_manager, 'db_manager'):
            return 'personal' if self.auth_manager.db_manager.is_personal_workspace(org_data) else 'team'
            
        # Default to team if no other information
        return 'team'

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            'user_id': self.session_data.get('user_id'),
            'email': self.session_data.get('email'),
            'organization_id': self.session_data.get('organization_id'),
            'organization_name': self.session_data.get('organization_name'),
            'organization_type': self.session_data.get('organization_type', 'team'),
            'role': self.session_data.get('role'),
            'last_activity': self.session_data.get('last_activity')
        }

    def get_active_organization_id(self) -> Optional[str]:
        """Get the ID of the currently active organization"""
        return self.current_organization['id'] if self.current_organization else None
        
    def get_current_organization(self) -> Optional[Dict[str, Any]]:
        """Get current organization data"""
        return self.current_organization
        
    def get_current_role(self) -> Optional[str]:
        """Get current user role"""
        return self.current_role
        
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self.session_data.get('user_id')
        
    def get_current_user_role(self) -> Optional[str]:
        """Get current user's role in the active organization"""
        return self.current_role
        
    def is_super_admin(self) -> bool:
        """Check if current user is a super admin by querying the database"""
        if not self.auth_manager:
            print("🔍 Debug: SessionManager.is_super_admin - No auth_manager")
            return False
        result = self.auth_manager.is_super_admin()
        print(f"🔍 Debug: SessionManager.is_super_admin result: {result}")
        return result
        
    def _get_user_permissions(self) -> Dict[str, Any]:
        """Get user permissions from database-driven permissions"""
        if not self.current_organization:
            return {}
        
        # Get all page permissions for current user in current organization
        org_id = self.current_organization['id']
        return self.auth_manager.get_user_page_permissions(org_id)

    def get_current_context(self) -> Dict[str, Any]:
        """Get current user and organization context for database operations"""
        return {
            'user_id': self.session_data.get('user_id'),
            'organization_id': self.session_data.get('organization_id'),
            'role': self.session_data.get('role'),
            'permissions': self._get_user_permissions()
        }

    def get_organization_summary(self) -> Dict[str, Any]:
        """Get summary of available organizations"""
        if not self.auth_manager:
            return {
                'total_count': 0,
                'personal_workspace': None,
                'team_organizations': [],
                'has_multiple': False
            }
            
        try:
            orgs = self.auth_manager.get_user_organizations()
            
            # Categorize organizations
            personal = None
            teams = []
            
            for org in orgs:
                org_type = self._get_org_type(org)
                if org_type == 'personal':
                    personal = self._format_org_info(org)
                else:
                    teams.append(self._format_org_info(org))
                    
            return {
                'total_count': len(orgs),
                'personal_workspace': personal,
                'team_organizations': teams,
                'has_multiple': len(orgs) > 1 or len(teams) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get organization summary: {e}")
            return {
                'total_count': 0,
                'personal_workspace': None,
                'team_organizations': [],
                'has_multiple': False
            }

    def _format_org_info(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format organization info for display"""
        org_type = self._get_org_type(org_data)
        display_name = org_data.get('name', 'Unnamed Organization')
        if org_type == 'personal':
            display_name += ' (Personal)'
            
        return {
            'id': org_data.get('id'),
            'name': org_data.get('name'),
            'display_name': display_name,
            'type': org_type,
            'role': org_data.get('role', 'member'),
            'member_count': org_data.get('member_count'),
            'created_at': org_data.get('created_at')
        }

    # Permission checks
    def can_manage_organization(self) -> bool:
        """Check if user can manage current organization settings"""
        if not self.current_organization:
            return False
        return self.auth_manager.can_access_page('organization_settings', self.current_organization['id'], 'edit')

    def can_invite_users(self) -> bool:
        """Check if user can invite others to current organization"""
        if not self.current_organization:
            return False
        if self._get_org_type(self.current_organization) == 'personal':
            return False
        return self.auth_manager.can_access_page('user_management', self.current_organization['id'], 'create')

    def can_manage_team(self) -> bool:
        """Check if user can manage team members"""
        if not self.current_organization:
            return False
        if self._get_org_type(self.current_organization) == 'personal':
            return False
        return self.auth_manager.can_access_page('team_management', self.current_organization['id'], 'edit')

    def can_manage_users(self) -> bool:
        """Check if current user can manage users in the organization"""
        if not self.current_organization:
            return False
        return self.auth_manager.can_access_page('user_management', self.current_organization['id'], 'edit')

    def has_permission(self, permission: str) -> bool:
        """Check if current user has a specific permission using database-driven permissions"""
        if not self.current_organization:
            return False
            
        # Super admin has all permissions
        if self.current_role == 'super_admin':
            return True
        
        # Parse permission string and map to database page permissions
        parts = permission.split('.')
        if len(parts) != 2:
            return False
        
        category, action = parts
        org_id = self.current_organization['id']
        
        # Map legacy permission categories to database page keys
        page_mapping = {
            'accounting': 'journal_entries',
            'users': 'user_management',
            'organization': 'organization_settings',
            'reports': 'reports',
            'settings': 'settings'
        }
        
        # Map legacy actions to database permission types
        action_mapping = {
            'read': 'view',
            'create': 'create',
            'update': 'edit',
            'edit': 'edit',
            'delete': 'delete',
            'manage': 'edit',
            'view': 'view'
        }
        
        page_key = page_mapping.get(category)
        permission_type = action_mapping.get(action)
        
        if page_key and permission_type:
            return self.auth_manager.can_access_page(page_key, org_id, permission_type)
        
        return False
        
    def can_access_accounting(self) -> bool:
        """Check if user can access accounting features"""
        return self.has_permission('accounting.read')
        
    def can_manage_accounting(self) -> bool:
        """Check if user can manage accounting data"""
        return self.has_permission('accounting.create') and self.has_permission('accounting.update')
        
    def can_close_periods(self) -> bool:
        """Check if user can close accounting periods"""
        if not self.current_organization:
            return False
        return self.auth_manager.can_access_page('settings', self.current_organization['id'], 'edit')
        
    def is_accountant(self) -> bool:
        """Check if user is an accountant"""
        return self.current_role == 'accountant'
        
    def should_show_switcher(self) -> bool:
        """Check if organization switcher should be shown"""
        try:
            summary = self.get_organization_summary()
            return summary['has_multiple']
        except Exception as e:
            self.logger.error(f"Error checking switcher visibility: {e}")
            return False

    def clear_session(self):
        """Clear all session data"""
        self.current_organization = None
        self.current_role = None
        self.session_data = {}
        self.logger.info("Session cleared")

    def get_available_organizations(self) -> List[Dict[str, Any]]:
        """Get list of organizations available to current user"""
        try:
            if not self.auth_manager:
                return []

            # Get organizations from auth manager
            orgs = self.auth_manager.get_user_organizations()
            if not orgs:
                return []
                
            # Format each organization with additional info
            formatted_orgs = []
            for org in orgs:
                # Get full org data and enrich with type info
                org_data = dict(org)  # Create a copy to avoid modifying original
                
                # Add organization type if not present
                if 'organization_type' not in org_data:
                    org_data['organization_type'] = self._get_org_type(org_data)
                    
                # Add display info
                formatted = self._format_org_info(org_data)
                formatted_orgs.append(formatted)
                
            return formatted_orgs
            
        except Exception as e:
            self.logger.error(f"Failed to get available organizations: {e}")
            return []

    def get_current_organization_type(self) -> str:
        """Get the type of the current organization ('personal' or 'team')"""
        if not self.current_organization:
            return 'unknown'
        return self._get_org_type(self.current_organization)

    def set_current_organization(self, org_data: Dict[str, Any]) -> bool:
        """Set the current organization directly (for compatibility)"""
        try:
            if isinstance(org_data, dict) and 'id' in org_data:
                return self.set_active_organization(org_data['id'])
            return False
        except Exception as e:
            self.logger.error(f"Failed to set current organization: {e}")
            return False
