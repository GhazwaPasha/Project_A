#!/usr/bin/env python3
"""
Test script to verify permission fix is working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client

def test_permissions():
    """Test that permissions are working correctly"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Supabase credentials not found in .env file")
        return
    
    supabase: Client = create_client(url, key)
    
    print("🧪 Testing permission fix...")
    print("=" * 50)
    
    # 1. Test the can_access_page function directly
    print("\n1. Testing can_access_page function...")
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
                        'p_page_key': page,
                        'p_org_id': org_id,
                        'p_permission_type': 'view'
                    }).execute()
                    print(f"   ✅ {page}: {result.data}")
                except Exception as e:
                    print(f"   ❌ {page}: Error - {e}")
        else:
            print("   No organizations found to test with")
            
    except Exception as e:
        print(f"❌ Error testing can_access_page: {e}")
    
    # 2. Test get_page_permissions function
    print("\n2. Testing get_page_permissions function...")
    try:
        if org_result.data:
            org_id = org_result.data[0]['id']
            for page in test_pages:
                try:
                    result = supabase.rpc('get_page_permissions', {
                        'p_page_key': page,
                        'p_org_id': org_id
                    }).execute()
                    print(f"   ✅ {page}: {result.data}")
                except Exception as e:
                    print(f"   ❌ {page}: Error - {e}")
                    
    except Exception as e:
        print(f"❌ Error testing get_page_permissions: {e}")
    
    # 3. Check page_permissions table
    print("\n3. Checking page_permissions table...")
    try:
        result = supabase.table('page_permissions').select('*').execute()
        print(f"   ✅ Found {len(result.data)} permission records")
        
        # Count by role
        roles = {}
        for perm in result.data:
            role = perm.get('role')
            if role not in roles:
                roles[role] = 0
            roles[role] += 1
        
        for role, count in roles.items():
            print(f"   {role}: {count} permissions")
            
    except Exception as e:
        print(f"❌ Error checking page_permissions: {e}")
    
    # 4. Test organization types
    print("\n4. Checking organization types...")
    try:
        result = supabase.table('organizations').select('id, name, organization_type').execute()
        print(f"   ✅ Found {len(result.data)} organizations")
        
        for org in result.data:
            print(f"   {org.get('name', 'Unknown')}: {org.get('organization_type', 'unknown')}")
            
    except Exception as e:
        print(f"❌ Error checking organizations: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Permission fix test complete!")
    print("\nNext steps:")
    print("1. Create a new user to test if permissions work")
    print("2. Check that all navigation tabs are visible")
    print("3. Verify that personal workspace restrictions work")

if __name__ == "__main__":
    test_permissions() 