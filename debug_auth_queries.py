#!/usr/bin/env python3
"""
Debug the exact queries that AuthManager is using
Since the organization exists but AuthManager isn't finding it
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.auth_manager import AuthManager
from src.core.supabase_manager import SupabaseManager

def debug_auth_queries():
    """Debug the exact queries used by AuthManager"""
    
    user_id = "e1b68757-3e5c-4ca1-951c-f28c26893b96"
    user_email = "ghazwairshad@gmail.com"
    org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"
    
    print(f"🔍 Debugging AuthManager queries for {user_email}")
    print("=" * 80)
    
    try:
        # Test direct database queries first
        print("\n1. DIRECT DATABASE QUERIES:")
        db = SupabaseManager()
        
        print("\n   1a. Direct organization query by created_by:")
        orgs_by_creator = db.supabase.table('organizations').select('*').eq('created_by', user_id).execute()
        print(f"      Result: {len(orgs_by_creator.data) if orgs_by_creator.data else 0} organizations")
        if orgs_by_creator.data:
            for org in orgs_by_creator.data:
                print(f"        - {org.get('name')} (ID: {org.get('id')}, Type: {org.get('organization_type')})")
        
        print("\n   1b. Direct organization_members query:")
        members = db.supabase.table('organization_members').select('*').eq('user_id', user_id).execute()
        print(f"      Result: {len(members.data) if members.data else 0} memberships")
        if members.data:
            for member in members.data:
                print(f"        - Org: {member.get('organization_id')}, Role: {member.get('role')}")
        
        print("\n   1c. Check if organization_members record exists for our org:")
        specific_member = db.supabase.table('organization_members').select('*').eq('user_id', user_id).eq('organization_id', org_id).execute()
        print(f"      Result: {len(specific_member.data) if specific_member.data else 0} memberships for this org")
        if specific_member.data:
            print(f"        Data: {specific_member.data[0]}")
        
        # Test AuthManager queries
        print("\n2. AUTHMANAGER QUERIES:")
        
        # Mock a user session for AuthManager
        auth = AuthManager()
        
        # Simulate current_user being set (normally done during sign_in)
        auth.current_user = type('User', (), {
            'id': user_id,
            'email': user_email
        })()
        
        print("\n   2a. Using AuthManager.get_user_organizations():")
        try:
            auth_orgs = auth.get_user_organizations()
            print(f"      Result: {len(auth_orgs) if auth_orgs else 0} organizations")
            if auth_orgs:
                for org in auth_orgs:
                    print(f"        - {org.get('name')} (ID: {org.get('id')}, Type: {org.get('organization_type')})")
            else:
                print("      ❌ AuthManager returned no organizations!")
        except Exception as e:
            print(f"      ❌ AuthManager query failed: {e}")
        
        # Test SupabaseManager.get_organizations() method directly
        print("\n   2b. Using SupabaseManager.get_organizations():")
        try:
            if not auth.db_manager:
                auth.db_manager = SupabaseManager()
            
            supabase_orgs = auth.db_manager.get_organizations(user_id)
            print(f"      Result: {len(supabase_orgs) if supabase_orgs else 0} organizations")
            if supabase_orgs:
                for org in supabase_orgs:
                    print(f"        - {org.get('name')} (ID: {org.get('id')}, Type: {org.get('organization_type')})")
            else:
                print("      ❌ SupabaseManager returned no organizations!")
        except Exception as e:
            print(f"      ❌ SupabaseManager query failed: {e}")
        
        # Test the exact query logic
        print("\n3. TESTING SPECIFIC QUERY LOGIC:")
        
        print("\n   3a. Testing JOIN query (like AuthManager likely uses):")
        try:
            # This is probably what AuthManager is doing - JOIN organizations with organization_members
            join_result = db.supabase.table('organization_members')\
                .select('*, organizations(*)')\
                .eq('user_id', user_id)\
                .execute()
            
            print(f"      Result: {len(join_result.data) if join_result.data else 0} joined records")
            if join_result.data:
                for record in join_result.data:
                    org_data = record.get('organizations', {})
                    print(f"        - {org_data.get('name')} via membership (Role: {record.get('role')})")
            else:
                print("      ❌ JOIN query returned no results!")
                print("      This suggests missing organization_members record!")
        except Exception as e:
            print(f"      ❌ JOIN query failed: {e}")
        
        print("\n4. DIAGNOSIS:")
        if orgs_by_creator.data and not members.data:
            print("   🎯 FOUND THE ISSUE!")
            print("   - Organization exists in organizations table")
            print("   - But NO record in organization_members table")
            print("   - AuthManager queries organization_members, so it finds nothing")
            print("   - The user creation trigger created the org but not the membership!")
            
            print("\n   🔧 SOLUTION:")
            print("   Need to create the missing organization_members record:")
            print(f"   INSERT INTO organization_members (user_id, organization_id, role)")
            print(f"   VALUES ('{user_id}', '{org_id}', 'owner')")
            
        elif not orgs_by_creator.data and not members.data:
            print("   - No organization and no memberships (user creation trigger didn't run)")
        elif orgs_by_creator.data and members.data:
            print("   - Organization and memberships exist - AuthManager query logic issue")
        
    except Exception as e:
        print(f"❌ Critical error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_auth_queries()
