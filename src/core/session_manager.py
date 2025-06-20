"""
Session Manager for handling user context and organization state
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

class SessionManager:
    """Manages user session state and organization context"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
        # Current session state
        self.current_organization = None
        self.current_role = None
        self.session_data = {}
        
    def set_current_organization(self, organization_data: Dict[str, Any]) -> bool:
        """Set the current active organization"""
        try:
            if not self.auth_manager.current_user:
                self.logger.error("No authenticated user")
                return False
            
            # Extract organization info
            if 'organizations' in organization_data:
                # From organization_members join
                self.current_organization = organization_data['organizations']
                self.current_role = organization_data['role']
            else:
                # Direct organization data
                self.current_organization = organization_data
                self.current_role = self.auth_manager.get_user_role(organization_data['id'])
            
            # Store session data
            self.session_data = {
                'user_id': self.auth_manager.current_user.id,
                'organization_id': self.current_organization['id'],
                'role': self.current_role,
                'organization_name': self.current_organization['name'],
                'last_activity': datetime.now().isoformat()
            }
            
            self.logger.info(f"Organization context set: {self.current_organization['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set organization context: {e}")
            return False
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current user and organization context for database operations"""
        return {
            'user_id': self.session_data.get('user_id'),
            'organization_id': self.session_data.get('organization_id'),
            'role': self.session_data.get('role'),
            'permissions': self._get_user_permissions()
        }
    
    def get_current_organization(self) -> Optional[Dict[str, Any]]:
        """Get current organization data"""
        return self.current_organization
    
    def get_current_role(self) -> Optional[str]:
        """Get current user role"""
        return self.current_role
    
    def has_permission(self, permission: str) -> bool:
        """Check if current user has specific permission"""
        permissions = self._get_user_permissions()
        
        # Super admin has all permissions
        if self.current_role == 'super_admin':
            return True
        
        # Parse permission string (e.g., "accounting.create", "users.manage")
        parts = permission.split('.')
        if len(parts) != 2:
            return False
        
        category, action = parts
        
        if category in permissions:
            if isinstance(permissions[category], dict):
                return permissions[category].get(action, False)
            else:
                return permissions[category] == True
        
        return False
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.current_role in ['super_admin', 'organization_owner', 'organization_admin']
    
    def can_manage_organization(self) -> bool:
        """Check if user can manage organization settings"""
        return self.current_role in ['super_admin', 'organization_owner', 'organization_admin']
    
    def can_delete_organization(self) -> bool:
        """Check if user can delete organization"""
        return self.current_role in ['super_admin', 'organization_owner']
    
    def clear_session(self):
        """Clear current session data"""
        self.current_organization = None
        self.current_role = None
        self.session_data = {}
        self.logger.info("Session cleared")
    
    def _get_user_permissions(self) -> Dict[str, Any]:
        """Get user permissions based on role"""
        role_permissions = {
            'super_admin': {
                'platform': {'manage': True, 'view': True},
                'organizations': {'create': True, 'delete': True, 'manage': True, 'view': True},
                'users': {'create': True, 'delete': True, 'manage': True, 'view': True},
                'accounting': {'create': True, 'read': True, 'update': True, 'delete': True}
            },
            'organization_owner': {
                'organization': {'manage': True, 'delete': True, 'billing': True},
                'users': {'invite': True, 'remove': True, 'manage_roles': True},
                'accounting': {'create': True, 'read': True, 'update': True, 'delete': True}
            },
            'organization_admin': {
                'organization': {'manage': True, 'settings': True},
                'users': {'invite': True, 'remove': True, 'assign_accountant': True},
                'accounting': {'create': True, 'read': True, 'update': True, 'delete': True}
            },
            'accountant': {
                'accounting': {'create': True, 'read': True, 'update': True, 'delete': True},
                'reports': {'generate': True, 'export': True}
            }
        }
        
        return role_permissions.get(self.current_role, {})
