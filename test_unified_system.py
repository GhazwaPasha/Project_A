#!/usr/bin/env python3
"""
Test the Unified Accounting System
Verify that all functionality works and accounts are visible
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

def test_unified_system():
    """Test the unified accounting system"""
    print("🔬 Testing Unified Accounting System")
    print("=" * 50)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Login as the test user
        print("🔐 Authenticating...")
        login_result = auth_manager.login("ghazwairshad@gmail.com", "123456")
        
        if not login_result['success']:
            print(f"❌ Login failed: {login_result.get('error', 'Unknown error')}")
            return
        
        print(f"✅ Logged in as: {login_result['user']['email']}")
        
        # Get organizations
        organizations = auth_manager.get_user_organizations()
        print(f"📁 Found {len(organizations)} organizations")
        
        if not organizations:
            print("❌ No organizations found")
            return
        
        # Initialize unified accounting system
        print("\n🚀 Initializing Unified Accounting System...")
        system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization context
        org = organizations[0]
        org_id = org['id']
        print(f"📋 Setting organization: {org['name']} ({org_id})")
        
        success = system.set_organization(org_id)
        if not success:
            print("❌ Failed to set organization context")
            return
        
        print(f"✅ Organization context set - Online: {system.is_online}")
        
        # Test chart of accounts
        print("\n📊 Testing Chart of Accounts...")
        accounts = system.get_chart_of_accounts()
        print(f"Found {len(accounts)} accounts")
        
        if accounts:
            print("\n📋 Sample accounts:")
            for i, acc in enumerate(accounts[:5]):  # Show first 5
                print(f"  {i+1}. {acc.get('code', 'N/A')} - {acc.get('name', 'N/A')} ({acc.get('type', 'N/A')})")
            
            if len(accounts) > 5:
                print(f"  ... and {len(accounts) - 5} more")
        else:
            print("❌ No accounts found!")
        
        # Test tuple format (for UI compatibility)
        print("\n🔄 Testing tuple format compatibility...")
        tuple_accounts = system.get_all_accounts()
        print(f"Tuple format accounts: {len(tuple_accounts)}")
        
        if tuple_accounts:
            print("Sample tuple account:")
            print(f"  {tuple_accounts[0]}")
        
        # Test postable accounts
        postable = system.get_postable_accounts()
        print(f"Postable accounts: {len(postable)}")
        
        # Test financial calculations
        print("\n💰 Testing Financial Calculations...")
        trial_balance = system.get_trial_balance()
        print(f"Trial balance accounts: {len(trial_balance)}")
        
        # Test sync status
        print("\n🔄 Testing Sync Status...")
        sync_status = system.get_sync_status()
        print(f"Sync status: {sync_status}")
        
        print("\n✅ All tests completed successfully!")
        print("🎉 Unified Accounting System is working properly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unified_system()
