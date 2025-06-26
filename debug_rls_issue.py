#!/usr/bin/env python3
"""
Debug RLS and authentication context issues
The organization exists but queries return 0 results - likely RLS blocking access
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.supabase_manager import SupabaseManager

def debug_rls_issue():
    """Debug RLS and authentication context"""
    
    user_id = "e1b68757-3e5c-4ca1-951c-f28c26893b96"
    user_email = "ghazwairshad@gmail.com"
    org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"
    
    print(f"🔍 Debugging RLS and authentication context")
    print("=" * 80)
    
    try:
        db = SupabaseManager()
        
        # 1. Check current session/user context
        print("\n1. CHECKING AUTHENTICATION CONTEXT:")
        try:
            session = db.supabase.auth.get_session()
            if session and session.user:
                print(f"   ✅ Authenticated as: {session.user.email} (ID: {session.user.id})")
                print(f"   Session expires: {session.expires_at}")
            else:
                print("   ❌ No active session - this explains the issue!")
                print("   RLS policies require authentication to access user data")
        except Exception as e:
            print(f"   ❌ Error checking session: {e}")
        
        # 2. Try to authenticate and then query
        print("\n2. ATTEMPTING TO AUTHENTICATE:")
        print("   Note: We can't actually sign in here without password")
        print("   But we can check if that's the issue...")
        
        # 3. Check if we can query organizations without authentication (should fail with RLS)
        print("\n3. TESTING QUERIES WITHOUT PROPER AUTH:")
        try:
            # This should fail due to RLS if policies are properly set up
            orgs = db.supabase.table('organizations').select('id, name, organization_type').execute()
            print(f"   Organizations visible without auth: {len(orgs.data) if orgs.data else 0}")
            if orgs.data:
                print("   ⚠️  RLS might not be properly configured - can see orgs without auth!")
                for org in orgs.data[:3]:  # Show first 3
                    print(f"     - {org.get('name')} ({org.get('organization_type')})")
            else:
                print("   ✅ No organizations visible - RLS is working")
        except Exception as e:
            print(f"   ✅ Query blocked by RLS: {e}")
        
        # 4. Check users table access
        print("\n4. TESTING USERS TABLE ACCESS:")
        try:
            users = db.supabase.table('users').select('id, email').execute()
            print(f"   Users visible without auth: {len(users.data) if users.data else 0}")
            if users.data:
                print("   ⚠️  Can see users without authentication!")
            else:
                print("   ✅ No users visible - RLS is working")
        except Exception as e:
            print(f"   ✅ Users query blocked by RLS: {e}")
        
        # 5. Try to directly check the specific organization by ID
        print("\n5. TESTING DIRECT ORGANIZATION ACCESS:")
        try:
            specific_org = db.supabase.table('organizations').select('*').eq('id', org_id).execute()
            print(f"   Can access specific org by ID: {len(specific_org.data) if specific_org.data else 0}")
            if specific_org.data:
                org = specific_org.data[0]
                print(f"     Found: {org.get('name')} created by {org.get('created_by')}")
            else:
                print("   ❌ Cannot access specific organization")
        except Exception as e:
            print(f"   ❌ Direct org access blocked: {e}")
        
        # 6. Check what auth.uid() returns in context
        print("\n6. CHECKING AUTH CONTEXT IN DATABASE:")
        try:
            # Try to get current auth context from database perspective
            auth_check = db.supabase.rpc('auth_uid').execute()
            print(f"   Database auth.uid(): {auth_check.data}")
        except Exception as e:
            print(f"   Cannot check auth.uid(): {e}")
        
        print("\n" + "=" * 80)
        print("DIAGNOSIS:")
        print("The organization exists in the database but queries return 0 results.")
        print("This is most likely due to:")
        print("1. 🎯 NO ACTIVE AUTHENTICATION SESSION")
        print("   - The SupabaseManager is not authenticated as the user")
        print("   - RLS policies require auth.uid() = user_id to see user data")
        print("   - AuthManager needs to authenticate before querying")
        print("")
        print("2. Row Level Security (RLS) policies are working correctly")
        print("   - They prevent access to user data without proper authentication")
        print("   - This is good for security but breaks unauthenticated queries")
        print("")
        print("SOLUTION:")
        print("- AuthManager.get_user_organizations() should only be called AFTER sign_in")
        print("- Or queries need to be made in the context of the authenticated user")
        print("- Check if sign_in properly sets the session in SupabaseManager")
        
    except Exception as e:
        print(f"❌ Critical error during RLS debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rls_issue()
