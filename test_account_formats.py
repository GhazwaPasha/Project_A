#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

def test_account_formats():
    """Test what format accounts are returned in"""
    print("🔍 Testing Account Formats")
    print("=" * 40)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Login
        result = auth_manager.sign_in("ghazwairshad@gmail.com", "test123")
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
        print(f"📊 Found {len(accounts)} accounts")
        
        if accounts:
            print(f"First account type: {type(accounts[0])}")
            print(f"First account: {accounts[0]}")
            
            # Check if it's a dict with expected keys
            if isinstance(accounts[0], dict):
                print("✅ Accounts are dictionaries")
                keys = list(accounts[0].keys())
                print(f"Keys: {keys}")
            else:
                print("❌ Accounts are NOT dictionaries")
        
        # Test get_all_accounts for comparison
        print("\n🧪 Testing get_all_accounts()...")
        all_accounts = accounting_system.get_all_accounts()
        print(f"📊 Found {len(all_accounts)} accounts")
        
        if all_accounts:
            print(f"First account type: {type(all_accounts[0])}")
            print(f"First account: {all_accounts[0]}")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_account_formats()
