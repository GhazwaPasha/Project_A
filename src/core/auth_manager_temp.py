"""
Temporary minimal auth manager for testing
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

class AuthManager:
    """Minimal authentication manager for testing"""
    
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
                
                # Load user organizations
                self._load_user_organizations()
                
                self.logger.info(f"User {email} signed in successfully")
                return {
                    "success": True, 
                    "user": result.user,
                    "organizations": self.user_organizations
                }
            
            return {"success": False, "error": "Invalid credentials"}
            
        except Exception as e:
            self.logger.error(f"Sign in failed: {e}")
            return {"success": False, "error": str(e)}
    
    def sign_up(self, email: str, password: str, first_name: str = "", last_name: str = "", 
                organization_type: str = "new", organization_name: str = None, invitation_code: str = None) -> Dict[str, Any]:
        """Sign up new user"""
        try:
            # Basic signup with Supabase Auth
            result = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if not result.user:
                return {"success": False, "error": "Failed to create account"}
            
            user_id = result.user.id
            
            # Create user profile (simplified version)
            try:
                display_name = f"{first_name} {last_name}".strip() or email.split('@')[0]
                self.supabase.table('users').insert({
                    "id": user_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "display_name": display_name
                }).execute()
            except Exception as e:
                self.logger.warning(f"Failed to create user profile: {e}")
            
            self.logger.info(f"User {email} signed up successfully")
            return {
                "success": True,
                "user": result.user,
                "message": "Account created successfully. Please check your email for verification."
            }
            
        except Exception as e:
            self.logger.error(f"Sign up failed: {e}")
            return {"success": False, "error": str(e)}

    def _load_user_organizations(self):
        """Load organizations user belongs to"""
        try:
            if not self.current_user:
                self.user_organizations = []
                return
            
            # For now, return empty list if RLS is causing issues
            # In production, this would query organization_members table
            result = self.supabase.table('organizations').select('*').execute()
            self.user_organizations = result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Failed to load user organizations: {e}")
            self.user_organizations = []
    
    def create_organization(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create new organization"""
        try:
            if not self.current_user:
                return {"success": False, "error": "User not authenticated"}
            
            # Generate slug from name
            slug = name.lower().replace(' ', '-').replace('_', '-')
            import re
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            
            # Create organization
            org_data = {
                "name": name,
                "slug": slug
            }
            
            org_result = self.supabase.table('organizations').insert(org_data).execute()
            
            if org_result.data:
                org = org_result.data[0]
                self.logger.info(f"Organization '{name}' created successfully")
                return {"success": True, "organization": org}
            else:
                return {"success": False, "error": "Failed to create organization"}
                
        except Exception as e:
            self.logger.error(f"Organization creation failed: {e}")
            return {"success": False, "error": str(e)}
