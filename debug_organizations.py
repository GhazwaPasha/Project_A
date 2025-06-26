#!/usr/bin/env python3
"""Debug script to check organization loading"""

import os
import sys
import getpass

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.auth_manager import AuthManager
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_organization_loading():
    """Test organization loading for current user"""
    try:
        print("=== Organization Loading Debug ===")
        
        # Get login credentials
        email = input("Enter email: ").strip()
        if not email:
            print("No email provided")
            return
            
        # Get password with visible input
        password = input("Enter password: ").strip()
        
        if not password:
            print("No password provided")
            return
        
        # Initialize auth manager and sign in
        auth_manager = AuthManager()
        
        print(f"\nAttempting to sign in as: {email}")
        result = auth_manager.sign_in(email, password)
        
        if not result.get('success'):
            print(f"Login failed: {result.get('message', 'Unknown error')}")
            return
            
        print("Login successful!")
        user = result.get('user')
        organizations = result.get('organizations', [])
        
        print(f"User ID: {user.get('id')}")
        print(f"User Email: {user.get('email')}")
        print(f"Organizations from login: {len(organizations)}")
        
        for i, org in enumerate(organizations):
            print(f"  {i+1}. {org.get('name', 'Unknown')} (ID: {org.get('id')}, Role: {org.get('user_role', 'Unknown')})")
        
        # Test organization loading again
        print("\n=== Testing get_user_organizations again ===")
        organizations2 = auth_manager.get_user_organizations()
        print(f"Found {len(organizations2)} organizations:")
        for i, org in enumerate(organizations2):
            print(f"  {i+1}. {org.get('name', 'Unknown')} (ID: {org.get('id')}, Role: {org.get('user_role', 'Unknown')})")
        
        # Check organization_members table directly
        print("\n=== Checking organization_members table directly ===")
        try:
            db_manager = auth_manager.db_manager
            user_id = user.get('id')
            
            result = db_manager.supabase.table('organization_members')\
                .select('*, organizations(*)') \
                .eq('user_id', user_id) \
                .execute()
            
            print(f"Direct query found {len(result.data)} membership records:")
            for i, member in enumerate(result.data):
                org_data = member.get('organizations', {})
                print(f"  {i+1}. Organization: {org_data.get('name', 'Unknown')} (Role: {member.get('role', 'Unknown')}, Active: {member.get('is_active', False)})")
        except Exception as e:
            print(f"Error querying organization_members: {e}")
        
        # Check organizations table directly
        print("\n=== Checking organizations table ===")
        try:
            result = db_manager.supabase.table('organizations').select('*').execute()
            print(f"Total organizations in database: {len(result.data)}")
            for i, org in enumerate(result.data):
                print(f"  {i+1}. {org.get('name', 'Unknown')} (ID: {org.get('id')}, Type: {org.get('organization_type', 'Unknown')})")
        except Exception as e:
            print(f"Error querying organizations: {e}")
            
        # Check if user has a personal workspace
        print("\n=== Checking for personal workspace ===")
        try:
            # First try with proper columns (after schema fix)
            try:
                result = db_manager.supabase.table('organizations')\
                    .select('*')\
                    .eq('created_by', user_id)\
                    .eq('organization_type', 'personal')\
                    .execute()
                
                if result.data:
                    print(f"Found {len(result.data)} personal workspace(s) using organization_type:")
                    for workspace in result.data:
                        print(f"  - {workspace.get('name', 'Unknown')} (ID: {workspace.get('id')})")
                else:
                    print("No personal workspace found using organization_type column.")
            except Exception as e:
                print(f"Query with organization_type failed: {e}")
                
                # Fallback: try with JSON settings
                print("Trying fallback query with JSON settings...")
                result = db_manager.supabase.table('organizations')\
                    .select('*')\
                    .execute()
                
                personal_workspaces = []
                for org in result.data:
                    settings = org.get('settings', {})
                    if isinstance(settings, dict) and settings.get('workspace_type') == 'personal':
                        personal_workspaces.append(org)
                    elif "'s Workspace" in org.get('name', ''):
                        personal_workspaces.append(org)
                
                if personal_workspaces:
                    print(f"Found {len(personal_workspaces)} personal workspace(s) using fallback:")
                    for workspace in personal_workspaces:
                        print(f"  - {workspace.get('name', 'Unknown')} (ID: {workspace.get('id')})")
                        # Check if this belongs to current user
                        members_result = db_manager.supabase.table('organization_members')\
                            .select('*')\
                            .eq('organization_id', workspace.get('id'))\
                            .eq('user_id', user_id)\
                            .execute()
                        if members_result.data:
                            print(f"    ^ This workspace belongs to the current user!")
                else:
                    print("No personal workspace found with fallback method either!")
            
            # Check if trigger should have created one
            print("\nChecking if user should have a personal workspace...")
            
            # First check auth.users table
            print("\n=== Checking auth.users table ===")
            try:
                auth_result = db_manager.supabase.table('auth.users').select('id, email, created_at').eq('id', user_id).execute()
                if auth_result.data:
                    auth_user = auth_result.data[0]
                    print(f"User exists in auth.users: {auth_user.get('email')} (ID: {auth_user.get('id')}, created: {auth_user.get('created_at')})")
                else:
                    print("User NOT found in auth.users table!")
            except Exception as e:
                print(f"Error checking auth.users: {e}")
                # Try alternative query method
                try:
                    print("Trying RPC call to check auth user...")
                    rpc_result = db_manager.supabase.rpc('get_current_user_id').execute()
                    print(f"Current user ID from RPC: {rpc_result.data}")
                except Exception as e2:
                    print(f"RPC call also failed: {e2}")
            
            # Then check custom users table
            print("\n=== Checking custom users table ===")
            result = db_manager.supabase.table('users').select('*').eq('id', user_id).execute()
            if result.data:
                custom_user = result.data[0]
                print(f"User exists in users table: {custom_user.get('email')} (created: {custom_user.get('created_at')})")
                
                # Check user_profiles too
                profile_result = db_manager.supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
                if profile_result.data:
                    print(f"User profile exists: {profile_result.data[0]}")
                else:
                    print("User profile NOT found!")
            else:
                print("User NOT found in users table - trigger might not have run!")
                print("This means the user creation trigger is not working properly.")
                
                # Let's try to manually trigger user creation
                print("\n=== Attempting manual user sync ===")
                try:
                    # Call the function that should create the user record
                    sync_result = db_manager.supabase.rpc('handle_new_user').execute()
                    print(f"Manual user sync result: {sync_result.data}")
                    
                    # Check again
                    result2 = db_manager.supabase.table('users').select('*').eq('id', user_id).execute()
                    if result2.data:
                        print("SUCCESS: User now exists in users table after manual sync!")
                    else:
                        print("Manual sync didn't work either.")
                        
                except Exception as e:
                    print(f"Manual sync failed: {e}")
                    
            # Also check what organizations exist for debugging
            print("\n=== Organizations created by this user ===")
            try:
                orgs_by_user = db_manager.supabase.table('organizations')\
                    .select('*')\
                    .eq('created_by', user_id)\
                    .execute()
                print(f"Found {len(orgs_by_user.data)} organizations created by user {user_id}")
                for org in orgs_by_user.data:
                    print(f"  - {org.get('name')} (Type: {org.get('organization_type', 'Unknown')})")
            except Exception as e:
                print(f"Error checking organizations by user: {e}")
            
        except Exception as e:
            print(f"Error checking personal workspace: {e}")
            
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_organization_loading()
