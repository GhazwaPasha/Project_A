#!/usr/bin/env python3
"""
Test script to verify that deleted accounts are properly filtered out
from journal entry account dropdowns.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_account_filtering():
    """Test that deleted accounts are filtered out from account lists."""
    
    try:
        from src.core.auth_manager import AuthManager
        from src.core.accounting_system import AccountingSystem
        
        print("🔍 Testing account filtering for deleted accounts...")
        
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Check if we have a valid session
        current_user = auth_manager.get_current_user()
        if not current_user:
            print("❌ No user session found. Please log in first.")
            return False
        
        # Get current organization
        organizations = auth_manager.get_user_organizations()
        if not organizations:
            print("❌ No organizations found.")
            return False
        
        current_org = organizations[0]
        print(f"✅ Testing with organization: {current_org.get('name', 'Unknown')}")
        
        # Initialize accounting system
        system = AccountingSystem(auth_manager)
        system.set_organization(current_org['id'])
        
        # Test 1: Check get_chart_of_accounts with active_only=True
        print("\n📋 Test 1: get_chart_of_accounts(active_only=True)")
        active_accounts = system.get_chart_of_accounts(active_only=True)
        print(f"   Active accounts: {len(active_accounts)}")
        
        # Test 2: Check get_chart_of_accounts with active_only=False
        print("\n📋 Test 2: get_chart_of_accounts(active_only=False)")
        all_accounts = system.get_chart_of_accounts(active_only=False)
        print(f"   All accounts (including deleted): {len(all_accounts)}")
        
        # Test 3: Check get_postable_accounts (should only include active)
        print("\n📋 Test 3: get_postable_accounts()")
        postable_accounts = system.get_postable_accounts()
        print(f"   Postable accounts: {len(postable_accounts)}")
        
        # Test 4: Check if there are any deleted accounts in postable_accounts
        print("\n📋 Test 4: Checking for deleted accounts in postable_accounts")
        deleted_in_postable = [acc for acc in postable_accounts if not acc.get('is_active', True)]
        if deleted_in_postable:
            print(f"   ❌ Found {len(deleted_in_postable)} deleted accounts in postable_accounts:")
            for acc in deleted_in_postable[:5]:  # Show first 5
                print(f"      - {acc.get('code', '')} - {acc.get('name', '')} (active: {acc.get('is_active', True)})")
        else:
            print("   ✅ No deleted accounts found in postable_accounts")
        
        # Test 5: Check the difference between all and active accounts
        print("\n📋 Test 5: Comparing all vs active accounts")
        deleted_accounts = [acc for acc in all_accounts if not acc.get('is_active', True)]
        print(f"   Deleted accounts found: {len(deleted_accounts)}")
        if deleted_accounts:
            print("   Sample deleted accounts:")
            for acc in deleted_accounts[:3]:  # Show first 3
                print(f"      - {acc.get('code', '')} - {acc.get('name', '')}")
        
        # Test 6: Verify that postable_accounts only contains active accounts
        print("\n📋 Test 6: Verifying postable_accounts filtering")
        active_postable = [acc for acc in postable_accounts if acc.get('is_active', True)]
        print(f"   Active postable accounts: {len(active_postable)}")
        print(f"   Total postable accounts: {len(postable_accounts)}")
        
        if len(active_postable) == len(postable_accounts):
            print("   ✅ All postable accounts are active (no deleted accounts)")
            return True
        else:
            print("   ❌ Found deleted accounts in postable_accounts")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False

if __name__ == "__main__":
    success = test_account_filtering()
    if success:
        print("\n✅ Account filtering test PASSED - deleted accounts are properly filtered out")
    else:
        print("\n❌ Account filtering test FAILED - deleted accounts are still appearing")
    
    sys.exit(0 if success else 1) 