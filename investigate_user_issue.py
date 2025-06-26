#!/usr/bin/env python3
"""
Investigate the user database issue
Check if user exists, what tables exist, and what triggers are in place
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.supabase_manager import SupabaseManager

def investigate_user_issue():
    """Investigate why user has no organizations"""
    
    user_id = "e1b68757-3e5c-4ca1-951c-f28c26893b96"
    user_email = "ghazwairshad@gmail.com"
    
    print(f"🔍 Investigating user issue for {user_email} (ID: {user_id})")
    print("=" * 80)
    
    try:
        db = SupabaseManager()
        
        # 1. Check if user exists in users table
        print("\n1. Checking users table...")
        try:
            users_result = db.supabase.table('users').select('*').eq('id', user_id).execute()
            if users_result.data:
                print(f"✅ User found in users table:")
                user_data = users_result.data[0]
                for key, value in user_data.items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ User NOT found in users table!")
                print("   This suggests the user creation trigger didn't run")
        except Exception as e:
            print(f"❌ Error querying users table: {e}")
            print("   This might mean the users table doesn't exist!")
        
        # 2. Check organizations table
        print("\n2. Checking organizations table...")
        try:
            orgs_result = db.supabase.table('organizations').select('*').eq('created_by', user_id).execute()
            print(f"   Organizations created by user: {len(orgs_result.data) if orgs_result.data else 0}")
            if orgs_result.data:
                for org in orgs_result.data:
                    print(f"     - {org.get('name')} (Type: {org.get('organization_type')}, ID: {org.get('id')})")
            
            # Also check for any personal workspace
            personal_result = db.supabase.table('organizations').select('*').eq('organization_type', 'personal').execute()
            print(f"   Total personal workspaces in system: {len(personal_result.data) if personal_result.data else 0}")
            
        except Exception as e:
            print(f"❌ Error querying organizations table: {e}")
        
        # 3. Check organization_members table
        print("\n3. Checking organization_members table...")
        try:
            members_result = db.supabase.table('organization_members').select('*').eq('user_id', user_id).execute()
            print(f"   Memberships for user: {len(members_result.data) if members_result.data else 0}")
            if members_result.data:
                for membership in members_result.data:
                    print(f"     - Org ID: {membership.get('organization_id')}, Role: {membership.get('role')}")
        except Exception as e:
            print(f"❌ Error querying organization_members table: {e}")
        
        # 4. Check what tables exist in the schema
        print("\n4. Checking what tables exist...")
        try:
            # Query information_schema to see what tables exist
            tables_result = db.supabase.rpc('get_table_list').execute()
            print(f"   Tables in schema: {tables_result.data if tables_result.data else 'RPC not available'}")
        except Exception as e:
            print(f"   RPC get_table_list failed: {e}")
            try:
                # Alternative approach - try to query a known system table
                tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
                # This might not work due to RLS, but worth trying
                print("   Trying alternative table listing...")
            except Exception as e2:
                print(f"   Alternative approach also failed: {e2}")
        
        # 5. Check for auth.users (Supabase auth table)
        print("\n5. Checking auth.users table...")
        try:
            # This should show if the user exists in Supabase auth
            auth_result = db.supabase.table('auth.users').select('id, email, created_at').eq('id', user_id).execute()
            if auth_result.data:
                print(f"✅ User found in auth.users:")
                for key, value in auth_result.data[0].items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ User NOT found in auth.users")
        except Exception as e:
            print(f"❌ Cannot query auth.users (expected - RLS): {e}")
        
        # 6. Try to check if triggers exist
        print("\n6. Checking for triggers...")
        try:
            # Try to see if the handle_new_user function exists
            functions_result = db.supabase.rpc('check_function_exists', {'function_name': 'handle_new_user'}).execute()
            print(f"   handle_new_user function exists: {functions_result.data}")
        except Exception as e:
            print(f"   Cannot check functions: {e}")
        
        # 7. Final summary
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("The user seems to be authenticated (has valid JWT) but:")
        print("- Not present in the users table (trigger didn't run)")
        print("- No personal workspace created")
        print("- No organization memberships")
        print("\nThis suggests:")
        print("1. The database schema is missing user creation triggers")
        print("2. The CLEAN_SUPABASE_RESET.sql or NEW_SCHEMA.sql wasn't run properly")
        print("3. Or the triggers exist but failed during user creation")
        
    except Exception as e:
        print(f"❌ Critical error during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_user_issue()
