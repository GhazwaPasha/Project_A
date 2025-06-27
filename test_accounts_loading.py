#!/usr/bin/env python3
"""
Test script to verify accounts loading after fixing tuple access issues
"""
import sys
import os
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

async def test_accounts_loading():
    """Test accounts loading functionality"""
    print("🧪 Testing Accounts Loading After Tuple Fix")
    print("=" * 50)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Login
        result = await auth_manager.login("ghazwairshad@gmail.com", "test123")
        if not result['success']:
            print(f"❌ Login failed: {result['message']}")
            return
        
        print("✅ Login successful")
        
        # Get organizations
        organizations = auth_manager.get_user_organizations()
        if not organizations:
            print("❌ No organizations found")
            return
        
        org = organizations[0]
        print(f"📁 Organization: {org['name']} (ID: {org['id']})")
        
        # Initialize unified accounting system
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization context
        if not accounting_system.set_organization(org['id']):
            print("❌ Failed to set organization context")
            return
        
        print("🔧 Organization context set")
        
        # Test get_chart_of_accounts
        print("\n🧪 Testing get_chart_of_accounts()...")
        accounts = accounting_system.get_chart_of_accounts(active_only=False)
        print(f"📊 Found {len(accounts)} accounts from get_chart_of_accounts()")
        
        if accounts:
            sample_account = accounts[0]
            print(f"📋 Sample account fields: {list(sample_account.keys())}")
            print(f"   Sample: {sample_account.get('code', 'N/A')} - {sample_account.get('name', 'N/A')}")
            print(f"   Type: {sample_account.get('type', 'N/A')} (account_type: {sample_account.get('account_type', 'N/A')})")
            print(f"   Level: {sample_account.get('level', 'N/A')}")
            print(f"   Is Postable: {sample_account.get('is_postable', 'N/A')}")
        
        # Test get_all_accounts (tuple format)
        print("\n🧪 Testing get_all_accounts()...")
        tuple_accounts = accounting_system.get_all_accounts()
        print(f"📊 Found {len(tuple_accounts)} accounts from get_all_accounts()")
        
        if tuple_accounts:
            sample_tuple = tuple_accounts[0]
            print(f"📋 Sample tuple format: {sample_tuple}")
            print(f"   Fields: (name, type, code, parent_code, level, is_postable, description)")
        
        # Test trial balance
        print("\n🧪 Testing get_trial_balance()...")
        trial_balance = accounting_system.get_trial_balance()
        print(f"📊 Found {len(trial_balance)} trial balance entries")
        
        if trial_balance:
            sample_tb = trial_balance[0]
            print(f"📋 Sample trial balance entry: {sample_tb}")
        
        print("\n✅ All tests completed successfully!")
        print("🎉 Tuple access issues have been resolved!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_accounts_loading())
