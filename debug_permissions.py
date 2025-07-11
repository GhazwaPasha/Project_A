#!/usr/bin/env python3
"""
Debug script to diagnose permission issues for newly created users
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from src.core.auth_manager import AuthManager

def debug_permissions():
    """Debug permission issues for newly created users"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Supabase credentials not found in .env file")
        return
    
    supabase: Client = create_client(url, key)
    
    print("🔍 Debugging permission issues for newly created users")
    print("=" * 60)
    
    # 1. Check if page_permissions table has the right data
    print("\n1. Checking page_permissions table...")
    try:
        result = supabase.table('page_permissions').select('*').execute()
        print(f"✅ Found {len(result.data)} permission records")
        
        # Group by role
        roles = {}
        for perm in result.data:
            role = perm.get('role')
            if role not in roles:
                roles[role] = []
            roles[role].append(perm.get('page_key'))
        
        for role, pages in roles.items():
            print(f"   {role}: {len(pages)} pages ({', '.join(pages)})")
            
    except Exception as e:
        print(f"❌ Error checking page_permissions: {e}")
    
    # 2. Check organization_members table
    print("\n2. Checking organization_members table...")
    try:
        result = supabase.table('organization_members').select('*').execute()
        print(f"✅ Found {len(result.data)} organization members")
        
        # Group by role
        roles = {}
        for member in result.data:
            role = member.get('role')
            if role not in roles:
                roles[role] = 0
            roles[role] += 1
        
        for role, count in roles.items():
            print(f"   {role}: {count} members")
            
    except Exception as e:
        print(f"❌ Error checking organization_members: {e}")
    
    # 3. Check organizations table
    print("\n3. Checking organizations table...")
    try:
        result = supabase.table('organizations').select('*').execute()
        print(f"✅ Found {len(result.data)} organizations")
        
        # Check organization types
        types = {}
        for org in result.data:
            org_type = org.get('organization_type', 'unknown')
            if org_type not in types:
                types[org_type] = 0
            types[org_type] += 1
        
        for org_type, count in types.items():
            print(f"   {org_type}: {count} organizations")
            
    except Exception as e:
        print(f"❌ Error checking organizations: {e}")
    
    # 4. Test the can_access_page function
    print("\n4. Testing can_access_page function...")
    try:
        # Get a sample organization
        org_result = supabase.table('organizations').select('id').limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]['id']
            print(f"   Testing with organization: {org_id}")
            
            # Test different pages
            test_pages = ['dashboard', 'journal_entries', 'accounts', 'reports', 'settings']
            for page in test_pages:
                try:
                    result = supabase.rpc('can_access_page', {
                        'page_key': page,
                        'org_id': org_id,
                        'permission_type': 'view'
                    }).execute()
                    print(f"   {page}: {result.data}")
                except Exception as e:
                    print(f"   {page}: ❌ Error - {e}")
        else:
            print("   No organizations found to test with")
            
    except Exception as e:
        print(f"❌ Error testing can_access_page: {e}")
    
    # 5. Test the get_user_organization_role function
    print("\n5. Testing get_user_organization_role function...")
    try:
        # Get a sample organization
        org_result = supabase.table('organizations').select('id').limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]['id']
            print(f"   Testing with organization: {org_id}")
            
            try:
                result = supabase.rpc('get_user_organization_role', {
                    'org_id': org_id
                }).execute()
                print(f"   User role: {result.data}")
            except Exception as e:
                print(f"   ❌ Error getting user role: {e}")
        else:
            print("   No organizations found to test with")
            
    except Exception as e:
        print(f"❌ Error testing get_user_organization_role: {e}")
    
    # 6. Check if RPC functions exist
    print("\n6. Checking if RPC functions exist...")
    try:
        # This is a bit hacky but we can test by calling the functions
        test_functions = [
            'can_access_page',
            'get_user_organization_role', 
            'get_page_permissions',
            'get_all_page_permissions'
        ]
        
        for func in test_functions:
            try:
                # Try to call with minimal parameters
                if func == 'can_access_page':
                    result = supabase.rpc(func, {
                        'page_key': 'dashboard',
                        'org_id': '00000000-0000-0000-0000-000000000000',
                        'permission_type': 'view'
                    }).execute()
                elif func == 'get_user_organization_role':
                    result = supabase.rpc(func, {
                        'org_id': '00000000-0000-0000-0000-000000000000'
                    }).execute()
                elif func == 'get_page_permissions':
                    result = supabase.rpc(func, {
                        'page_key': 'dashboard',
                        'org_id': '00000000-0000-0000-0000-000000000000'
                    }).execute()
                elif func == 'get_all_page_permissions':
                    result = supabase.rpc(func, {
                        'p_org_id': '00000000-0000-0000-0000-000000000000',
                        'p_pages': ['dashboard']
                    }).execute()
                
                print(f"   ✅ {func}: Function exists")
            except Exception as e:
                if "function" in str(e).lower() and "does not exist" in str(e).lower():
                    print(f"   ❌ {func}: Function does not exist")
                else:
                    print(f"   ⚠️  {func}: Function exists but error calling it - {e}")
                    
    except Exception as e:
        print(f"❌ Error checking RPC functions: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Debug complete!")
    print("\nNext steps:")
    print("1. Run the FIX_PERMISSIONS_FOR_NEW_USERS.sql script in Supabase SQL Editor")
    print("2. Test creating a new user to see if permissions work")
    print("3. Check the logs for any permission-related errors")

if __name__ == "__main__":
    debug_permissions() 