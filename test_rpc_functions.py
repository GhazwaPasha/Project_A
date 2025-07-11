#!/usr/bin/env python3
"""
Test RPC functions to debug permission issues
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client

def test_rpc_functions():
    """Test RPC functions to debug permission issues"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Supabase credentials not found in .env file")
        return
    
    supabase: Client = create_client(url, key)
    
    print("🧪 Testing RPC functions...")
    print("=" * 50)
    
    # Test 1: Check if can_access_page function exists and works
    print("\n1. Testing can_access_page function...")
    try:
        result = supabase.rpc('can_access_page', {
            'page_key': 'dashboard',
            'org_id': '00000000-0000-0000-0000-000000000000',  # Test with dummy UUID
            'permission_type': 'view'
        }).execute()
        print(f"✅ can_access_page result: {result.data}")
    except Exception as e:
        print(f"❌ can_access_page failed: {e}")
    
    # Test 2: Check if get_all_page_permissions function exists and works
    print("\n2. Testing get_all_page_permissions function...")
    try:
        result = supabase.rpc('get_all_page_permissions', {
            'p_org_id': '00000000-0000-0000-0000-000000000000',  # Test with dummy UUID
            'p_pages': ['dashboard', 'accounts', 'journal_entries']
        }).execute()
        print(f"✅ get_all_page_permissions result: {result.data}")
    except Exception as e:
        print(f"❌ get_all_page_permissions failed: {e}")
    
    # Test 3: Check if get_user_organization_role function exists and works
    print("\n3. Testing get_user_organization_role function...")
    try:
        result = supabase.rpc('get_user_organization_role', {
            'p_org_id': '00000000-0000-0000-0000-000000000000'  # Test with dummy UUID
        }).execute()
        print(f"✅ get_user_organization_role result: {result.data}")
    except Exception as e:
        print(f"❌ get_user_organization_role failed: {e}")
    
    # Test 4: Check if is_super_admin function exists and works
    print("\n4. Testing is_super_admin function...")
    try:
        result = supabase.rpc('is_super_admin', {}).execute()
        print(f"✅ is_super_admin result: {result.data}")
    except Exception as e:
        print(f"❌ is_super_admin failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_rpc_functions() 