"""
Check Database Users Script
Simple script to check what users and organizations exist in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.supabase_manager import SupabaseManager

def check_database_state():
    """Check the current state of users and organizations in the database."""
    print("🔍 Checking Database State")
    print("=" * 50)
    
    try:
        db_manager = SupabaseManager()
        
        # Check user_profiles table
        print("📊 User Profiles:")
        user_profiles = db_manager.supabase.table('user_profiles').select('*').execute()
        if user_profiles.data:
            for user in user_profiles.data:
                print(f"   - {user.get('email', 'No email')} | {user.get('full_name', 'No name')} | ID: {user.get('id', 'No ID')}")
        else:
            print("   No user profiles found")
        
        print("\n🏢 Organizations:")
        organizations = db_manager.supabase.table('organizations').select('*').execute()
        if organizations.data:
            for org in organizations.data:
                print(f"   - {org.get('name', 'No name')} | Type: {org.get('organization_type', 'No type')} | ID: {org.get('id', 'No ID')}")
        else:
            print("   No organizations found")
        
        print("\n👥 Organization Members:")
        members = db_manager.supabase.table('organization_members').select('*, organizations(name), user_profiles(email, full_name)').execute()
        if members.data:
            for member in members.data:
                org_name = member.get('organizations', {}).get('name', 'Unknown Org') if member.get('organizations') else 'Unknown Org'
                user_email = member.get('user_profiles', {}).get('email', 'Unknown Email') if member.get('user_profiles') else 'Unknown Email'
                print(f"   - {user_email} in {org_name} (Role: {member.get('role', 'No role')})")
        else:
            print("   No organization members found")
        
        print("\n📊 Chart of Accounts:")
        accounts = db_manager.supabase.table('chart_of_accounts').select('code, name, organization_id').execute()
        if accounts.data:
            print(f"   Found {len(accounts.data)} accounts across all organizations")
            # Group by organization
            org_accounts = {}
            for account in accounts.data:
                org_id = account.get('organization_id', 'Unknown')
                if org_id not in org_accounts:
                    org_accounts[org_id] = []
                org_accounts[org_id].append(account)
            
            for org_id, accounts_list in org_accounts.items():
                print(f"   Organization {org_id}: {len(accounts_list)} accounts")
        else:
            print("   No chart of accounts found")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_state()
