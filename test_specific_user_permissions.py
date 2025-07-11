#!/usr/bin/env python3
"""
Test permissions for a specific user and organization
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client

def test_specific_user_permissions():
    """Test permissions for a specific user and organization"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Supabase credentials not found in .env file")
        return
    
    supabase: Client = create_client(url, key)
    
    print("🔍 Testing permissions for specific user and organization...")
    print("=" * 50)
    
    # Check 1: Get all organizations
    print("\n1. Checking all organizations...")
    try:
        result = supabase.table('organizations').select('*').execute()
        print(f"✅ Found {len(result.data)} organizations:")
        for org in result.data:
            print(f"   {org['name']} (ID: {org['id']}): type={org.get('organization_type', 'unknown')}")
    except Exception as e:
        print(f"❌ Error checking organizations: {e}")
    
    # Check 2: Get all organization members
    print("\n2. Checking all organization members...")
    try:
        result = supabase.table('organization_members').select('*').execute()
        print(f"✅ Found {len(result.data)} organization members:")
        for member in result.data:
            print(f"   User {member['user_id']} in org {member['organization_id']}: role={member['role']}, active={member['is_active']}")
    except Exception as e:
        print(f"❌ Error checking organization_members: {e}")
    
    # Check 3: Get all users
    print("\n3. Checking all users...")
    try:
        result = supabase.table('users').select('*').execute()
        print(f"✅ Found {len(result.data)} users:")
        for user in result.data:
            print(f"   {user.get('email', 'No email')} (ID: {user['id']})")
    except Exception as e:
        print(f"❌ Error checking users: {e}")
    
    # If we have organizations and members, test the RPC functions
    if result.data and len(result.data) > 0:
        org_id = result.data[0]['id']  # Use the first organization
        print(f"\n4. Testing RPC functions with org_id: {org_id}")
        
        # Test can_access_page function
        try:
            result = supabase.rpc('can_access_page', {
                'p_page_key': 'dashboard',
                'p_org_id': org_id,
                'p_permission_type': 'view'
            }).execute()
            print(f"✅ can_access_page('dashboard', '{org_id}', 'view') = {result.data}")
        except Exception as e:
            print(f"❌ can_access_page failed: {e}")
        
        # Test get_all_page_permissions function
        try:
            result = supabase.rpc('get_all_page_permissions', {
                'p_org_id': org_id,
                'p_pages': ['dashboard', 'accounts', 'journal_entries']
            }).execute()
            print(f"✅ get_all_page_permissions result: {result.data}")
        except Exception as e:
            print(f"❌ get_all_page_permissions failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_specific_user_permissions() 