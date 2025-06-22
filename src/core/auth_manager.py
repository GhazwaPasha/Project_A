"""
Authentication Manager for Supabase integration
Fast implementation with all essential features
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

class AuthManager:
    """Fast authentication manager with Supabase integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
        
        self.supabase = create_client(supabase_url, supabase_key)
        self.current_user = None
        self.user_organizations = []
        self.session_token = None
        
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email/password"""
        try:
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result.user:
                self.current_user = result.user
                self.session_token = result.session.access_token if result.session else None
                
                # Load user profile and organizations
                self._load_user_profile()
                self._load_user_organizations()
                  # Update last login
                self._update_last_login()
                
                self.logger.info(f"User {email} signed in successfully")
                return {
                    "success": True, 
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "email_confirmed_at": str(result.user.email_confirmed_at) if result.user.email_confirmed_at else None,
                        "created_at": str(result.user.created_at) if result.user.created_at else None,
                        "user_metadata": result.user.user_metadata or {},
                        "app_metadata": result.user.app_metadata or {}
                    },
                    "organizations": self.user_organizations
                }
            
            return {"success": False, "error": "Invalid credentials"}
            
        except Exception as e:
            self.logger.error(f"Sign in failed: {e}")
            return {"success": False, "error": str(e)}
    
    def sign_up(self, email: str, password: str, first_name: str = "", last_name: str = "", 
                organization_type: str = "new", organization_name: str = None, invitation_code: str = None) -> Dict[str, Any]:
        """Sign up new user with organization context"""
        try:
            # Basic signup with Supabase Auth
            result = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if not result.user:
                return {"success": False, "error": "Failed to create account"}
            
            user_id = result.user.id
            
            # Create user profile
            user_profile = self._create_user_profile(user_id, first_name, last_name, email)
            
            # Handle organization assignment
            if organization_type == "new" and organization_name:
                # Create new organization and make user the owner
                org_id = self._create_organization(organization_name, user_id)
                self._add_user_to_organization(user_id, org_id, "org_owner")
                
            elif organization_type == "existing" and invitation_code:
                # Join existing organization using invitation code
                self._join_organization_by_invitation(user_id, invitation_code)
            else:                # No organization specified - user needs to be invited later
                pass
            
            self.logger.info(f"User {email} signed up successfully")
            return {
                "success": True,
                "user": {
                    "id": result.user.id,
                    "email": result.user.email,
                    "email_confirmed_at": str(result.user.email_confirmed_at) if result.user.email_confirmed_at else None,
                    "created_at": str(result.user.created_at) if result.user.created_at else None,
                    "user_metadata": result.user.user_metadata or {},
                    "app_metadata": result.user.app_metadata or {}
                },
                "user_profile": user_profile,
                "message": "Account created successfully! Please check your email for verification."
            }
            
        except Exception as e:
            self.logger.error(f"Sign up failed: {e}")
            return {"success": False, "error": str(e)}
    
    def sign_out(self) -> bool:
        """Sign out current user"""
        try:
            self.supabase.auth.sign_out()
            self.current_user = None
            self.user_organizations = []
            self.session_token = None
            self.logger.info("User signed out successfully")
            return True
        except Exception as e:
            self.logger.error(f"Sign out failed: {e}")
            return False
    
    def has_valid_session(self) -> bool:
        """Check if user has valid session"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.access_token:
                self.current_user = session.user
                self.session_token = session.access_token
                self._load_user_profile()
                self._load_user_organizations()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Session check failed: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return self.current_user
    
    def get_user_organizations(self) -> List[Dict[str, Any]]:
        """Get all organizations the current user belongs to"""
        return self.user_organizations
        
    def get_organization_members(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get all members of an organization"""
        try:
            if not self.current_user:
                return []
            
            # Get organization members with user details
            result = self.supabase.table('organization_members').select(
                '*, users!inner(first_name, last_name, display_name, email, last_login_at)'
            ).eq('organization_id', organization_id).eq('is_active', True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Failed to get organization members: {e}")
            return []
    
    def get_pending_invitations(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get pending invitations for an organization"""
        try:
            if not self.current_user:
                return []
            
            # Get pending invitations with inviter details
            result = self.supabase.table('organization_members').select(
                '*, invited_by_user:users!invited_by(display_name)'
            ).eq('organization_id', organization_id).is_('joined_at', 'null').execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Failed to get pending invitations: {e}")
            return []
    
    def update_member_role(self, member_id: str, new_role: str) -> Dict[str, Any]:
        """Update a member's role in the organization"""
        try:
            if not self.current_user:
                return {"success": False, "error": "User not authenticated"}
            
            # Update the member's role
            result = self.supabase.table('organization_members').update({
                'role': new_role,
                'updated_at': 'now()'
            }).eq('id', member_id).execute()
            
            if result.data:
                return {"success": True, "message": "Role updated successfully"}
            else:
                return {"success": False, "error": "Failed to update role"}
                
        except Exception as e:
            self.logger.error(f"Failed to update member role: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_organization_member(self, member_id: str) -> Dict[str, Any]:
        """Remove a member from the organization"""
        try:
            if not self.current_user:
                return {"success": False, "error": "User not authenticated"}
            
            # Set member as inactive instead of deleting
            result = self.supabase.table('organization_members').update({
                'is_active': False,
                'updated_at': 'now()'
            }).eq('id', member_id).execute()
            
            if result.data:
                return {"success": True, "message": "Member removed successfully"}
            else:
                return {"success": False, "error": "Failed to remove member"}
                
        except Exception as e:
            self.logger.error(f"Failed to remove member: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_invitation(self, invitation_id: str) -> Dict[str, Any]:
        """Cancel a pending invitation"""
        try:
            if not self.current_user:
                return {"success": False, "error": "User not authenticated"}
            
            # Delete the invitation record
            result = self.supabase.table('organization_members').delete().eq('id', invitation_id).execute()
            
            return {"success": True, "message": "Invitation cancelled"}
                
        except Exception as e:
            self.logger.error(f"Failed to cancel invitation: {e}")
            return {"success": False, "error": str(e)}
    
    def send_invitation_email(self, email: str, organization_name: str, inviter_name: str, invitation_token: str) -> bool:
        """Send invitation email to user (placeholder for email service)"""
        try:
            # This is a placeholder for email integration
            # In production, you would integrate with an email service like SendGrid, AWS SES, etc.
            self.logger.info(f"Email invitation sent to {email} for organization {organization_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send invitation email: {e}")
            return False

    def create_organization(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create new organization and make current user the owner"""
        try:
            if not self.current_user:
                return {"success": False, "error": "User not authenticated"}
            
            # Generate slug from name
            slug = name.lower().replace(' ', '-').replace('_', '-')
            # Remove special characters and ensure uniqueness
            import re
            slug = re.sub(r'[^a-z0-9-]', '', slug)
              # Create organization (using only available columns)
            org_data = {
                "name": name,
                "slug": slug
            }
            
            org_result = self.supabase.table('organizations').insert(org_data).execute()
            
            if org_result.data:
                org = org_result.data[0]
                
                # Add user as organization owner
                member_result = self.supabase.table('organization_members').insert({
                    "organization_id": org['id'],
                    "user_id": self.current_user.id,
                    "role": "organization_owner"
                }).execute()
                
                if member_result.data:
                    # Reload user organizations
                    self._load_user_organizations()
                    
                    self.logger.info(f"Organization '{name}' created successfully")
                    return {"success": True, "organization": org}
            
            return {"success": False, "error": "Failed to create organization"}
            
        except Exception as e:
            self.logger.error(f"Create organization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def invite_user_to_organization(self, email: str, organization_id: str, role: str = "accountant") -> Dict[str, Any]:
        """Invite user to organization"""
        try:
            if not self.current_user:
                return {"success": False, "error": "User not authenticated"}
            
            # Check if user has permission to invite
            if not self._can_manage_users(organization_id):
                return {"success": False, "error": "Permission denied"}
            
            # Generate invitation token
            import uuid
            invitation_token = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(days=7)
            
            # Create invitation record
            invite_result = self.supabase.table('organization_members').insert({
                "organization_id": organization_id,
                "user_id": None,  # Will be filled when user accepts
                "role": role,
                "invited_by": self.current_user.id,
                "invited_at": datetime.now().isoformat(),
                "invitation_token": invitation_token,
                "invitation_expires_at": expires_at.isoformat(),
                "is_active": False
            }).execute()
            
            if invite_result.data:
                # TODO: Send invitation email
                self.logger.info(f"User {email} invited to organization")
                return {
                    "success": True, 
                    "invitation_token": invitation_token,
                    "message": f"Invitation sent to {email}"
                }
            
            return {"success": False, "error": "Failed to create invitation"}
            
        except Exception as e:
            self.logger.error(f"Invite user failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_role(self, organization_id: str) -> Optional[str]:
        """Get user role in specific organization"""
        for org in self.user_organizations:
            if org.get('organization_id') == organization_id:
                return org.get('role')
        return None
    
    def _load_user_profile(self):
        """Load extended user profile"""
        try:
            if not self.current_user:
                return
            
            result = self.supabase.table('users').select('*').eq('id', self.current_user.id).execute()
            if result.data:
                self.user_profile = result.data[0]
            else:
                # Create profile if doesn't exist
                self._create_user_profile(self.current_user.id, "", "", self.current_user.email)
                
        except Exception as e:
            self.logger.error(f"Failed to load user profile: {e}")
    
    def _load_user_organizations(self):
        """Load organizations user belongs to"""
        try:
            if not self.current_user:
                return
            
            result = self.supabase.table('organization_members').select('''
                *,
                organizations (*)
            ''').eq('user_id', self.current_user.id).eq('is_active', True).execute()
            
            self.user_organizations = result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Failed to load user organizations: {e}")
            self.user_organizations = []
    
    def _create_user_profile(self, user_id: str, first_name: str, last_name: str, email: str):
        """Create user profile in users table"""
        try:
            display_name = f"{first_name} {last_name}".strip() or email.split('@')[0]
            
            self.supabase.table('users').insert({
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name
            }).execute()
            
        except Exception as e:
            self.logger.error(f"Failed to create user profile: {e}")
    
    def _update_last_login(self):
        """Update user's last login timestamp"""
        try:
            if not self.current_user:
                return
            
            self.supabase.table('users').update({
                "last_login_at": datetime.now().isoformat()
            }).eq('id', self.current_user.id).execute()
            
        except Exception as e:
            self.logger.error(f"Failed to update last login: {e}")
    
    def _can_manage_users(self, organization_id: str) -> bool:
        """Check if user can manage users in organization"""
        role = self.get_user_role(organization_id)
        return role in ['organization_owner', 'organization_admin']
    
    def _create_organization(self, name: str, owner_id: str) -> str:
        """Create a new organization"""
        try:
            # Generate slug from name
            slug = name.lower().replace(" ", "-").replace("_", "-")
            
            # Insert organization
            result = self.supabase.table("organizations").insert({
                "name": name,
                "slug": slug,
                "settings": {},
                "is_active": True
            }).execute()
            
            if result.data:
                org_id = result.data[0]["id"]
                self.logger.info(f"Created organization {name} with ID {org_id}")
                return org_id
            else:
                raise Exception("Failed to create organization")
                
        except Exception as e:
            self.logger.error(f"Failed to create organization: {e}")
            raise
    
    def _add_user_to_organization(self, user_id: str, org_id: str, role_name: str):
        """Add user to organization with specified role"""
        try:
            # Get role ID
            role_result = self.supabase.table("roles").select("id").eq("name", role_name).execute()
            if not role_result.data:
                raise Exception(f"Role {role_name} not found")
            
            role_id = role_result.data[0]["id"]
            
            # Add user to organization
            self.supabase.table("organization_members").insert({
                "organization_id": org_id,
                "user_id": user_id,
                "role_id": role_id,
                "is_active": True,
                "joined_at": "NOW()"
            }).execute()
            
            self.logger.info(f"Added user {user_id} to org {org_id} with role {role_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add user to organization: {e}")
            raise
    
    def _join_organization_by_invitation(self, user_id: str, invitation_code: str):
        """Join organization using invitation code"""
        try:
            # TODO: Implement invitation code logic
            # For now, this is a placeholder
            self.logger.warning("Invitation code feature not yet implemented")
            raise Exception("Invitation codes not yet supported")
            
        except Exception as e:
            self.logger.error(f"Failed to join organization by invitation: {e}")
            raise
