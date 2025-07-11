#!/usr/bin/env python3
"""
Test permissions for hasnain@test.com
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.auth_manager import AuthManager

def test_hasnain_permissions():
    """Test permissions for hasnain@test.com"""
    
    print("🔍 Testing permissions for hasnain@test.com...")
    print("=" * 50)
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Sign in as hasnain@test.com
    print("1. Signing in as hasnain@test.com...")
    try:
        signin_result = auth_manager.sign_in("hasnain@test.com", "password")
        if signin_result.get('success'):
            print("✅ Sign in successful!")
        else:
            print(f"❌ Sign in failed: {signin_result.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ Sign in error: {e}")
        return
    
    # Get current user
    current_user = auth_manager.get_current_user()
    if not current_user:
        print("❌ No current user found after sign in")
        return
    
    print(f"✅ Authenticated as: {current_user.get('email', 'Unknown')}")
    print(f"   User ID: {current_user.get('id', 'Unknown')}")
    
    # Get user's organizations
    print("\n2. Getting user's organizations...")
    organizations = auth_manager.get_user_organizations()
    print(f"✅ Found {len(organizations)} organizations for user:")
    for org in organizations:
        print(f"   {org.get('name', 'Unknown')} (ID: {org.get('id', 'Unknown')}) - Role: {org.get('user_role', 'Unknown')}")
    
    if not organizations:
        print("❌ No organizations found for user")
        return
    
    # Test permissions for the first organization
    org_id = organizations[0]['id']
    org_name = organizations[0].get('name', 'Unknown')
    user_role = organizations[0].get('user_role', 'Unknown')
    
    print(f"\n3. Testing permissions for organization: {org_name} (ID: {org_id})")
    print(f"   User role: {user_role}")
    
    # Test individual page permissions
    print("\n4. Testing individual page permissions...")
    pages = ['dashboard', 'accounts', 'journal_entries', 'reports', 'settings', 'team_management', 'organization_settings', 'user_management']
    for page in pages:
        can_view = auth_manager.can_access_page(page, org_id, 'view')
        print(f"   {page}: can_view = {can_view}")
    
    # Test get_all_page_permissions_single_rpc
    print(f"\n5. Testing get_all_page_permissions_single_rpc...")
    all_permissions = auth_manager.get_all_page_permissions_single_rpc(org_id)
    print(f"   Result: {all_permissions}")
    
    # Test get_user_role_in_organization
    print(f"\n6. Testing get_user_role_in_organization...")
    role = auth_manager.get_user_role_in_organization(org_id)
    print(f"   Role: {role}")
    
    # Test is_super_admin
    print(f"\n7. Testing is_super_admin...")
    is_super = auth_manager.is_super_admin()
    print(f"   Is super admin: {is_super}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_hasnain_permissions() 