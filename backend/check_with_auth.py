#!/usr/bin/env python3
"""
Check database with proper authentication
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.auth_manager import AuthManager

def check_with_auth():
    """Check database with proper authentication"""
    
    print("🔍 Checking database with authentication...")
    print("=" * 50)
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Check if we have a current user
    current_user = auth_manager.get_current_user()
    if not current_user:
        print("❌ No authenticated user found")
        return
    
    print(f"✅ Authenticated as: {current_user.get('email', 'Unknown')}")
    print(f"   User ID: {current_user.get('id', 'Unknown')}")
    
    # Get user's organizations
    organizations = auth_manager.get_user_organizations()
    print(f"✅ Found {len(organizations)} organizations for user:")
    for org in organizations:
        print(f"   {org.get('name', 'Unknown')} (ID: {org.get('id', 'Unknown')}) - Role: {org.get('user_role', 'Unknown')}")
    
    if organizations:
        # Test permissions for the first organization
        org_id = organizations[0]['id']
        print(f"\n🔍 Testing permissions for organization: {org_id}")
        
        # Test individual page permissions
        pages = ['dashboard', 'accounts', 'journal_entries', 'reports', 'settings']
        for page in pages:
            can_view = auth_manager.can_access_page(page, org_id, 'view')
            print(f"   {page}: can_view = {can_view}")
        
        # Test get_all_page_permissions_single_rpc
        print(f"\n🔍 Testing get_all_page_permissions_single_rpc...")
        all_permissions = auth_manager.get_all_page_permissions_single_rpc(org_id)
        print(f"   Result: {all_permissions}")
    
    print("\n" + "=" * 50)
    print("Authentication check completed!")

if __name__ == "__main__":
    check_with_auth() 