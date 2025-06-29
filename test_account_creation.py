#!/usr/bin/env python3
"""
Test script to verify account creation functionality.
This tests the same methods that the UI uses.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.enhanced_accounting_system import EnhancedAccountingSystem
from src.core.session_manager import SessionManager

def test_account_creation():
    """Test account creation using the same methods as the UI."""
    
    print("🧪 Testing Account Creation")
    print("=" * 50)
    
    # Initialize the session manager
    session_manager = SessionManager()
    
    # Set organization context (same as UI does)
    org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"  # Your org ID from terminal output
    session_manager.set_current_organization(org_id)
    
    print(f"✅ Organization set: {org_id}")
    
    # Initialize enhanced accounting system (same as UI)
    system = EnhancedAccountingSystem(session_manager=session_manager)
    
    print(f"✅ System initialized")
    print(f"   Type: {type(system)}")
    print(f"   Has base_system: {hasattr(system, 'base_system')}")
    
    if hasattr(system, 'base_system'):
        print(f"   Base system type: {type(system.base_system)}")
    
    # Test account data (same structure as UI creates)
    test_account_data = {
        'name': 'Test Cash Account',
        'account_type': 'Asset',
        'code': 'TEST001',
        'parent_id': None,  # Top-level account
        'is_postable': True,
        'description': 'Test account created via script'
    }
    
    print(f"\n📝 Creating test account:")
    print(f"   Data: {test_account_data}")
    
    try:
        # Use the same method path as the UI
        if hasattr(system, 'base_system'):
            print("   Using base_system.create_account")
            result = system.base_system.create_account(test_account_data)
        else:
            print("   Using system.create_account")
            result = system.create_account(test_account_data)
        
        print(f"\n✅ Account creation result: {result}")
        
        if result:
            print(f"   Created account ID: {result.get('id', 'No ID returned')}")
            print("   ✅ SUCCESS: Account created successfully!")
        else:
            print("   ❌ FAILED: No result returned")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test fetching all accounts to see if our new account appears
    print(f"\n📊 Fetching all accounts to verify:")
    try:
        if hasattr(system, 'base_system'):
            accounts = system.base_system.get_all_accounts()
        else:
            accounts = system.get_all_accounts()
        
        print(f"   Total accounts found: {len(accounts) if accounts else 0}")
        
        # Look for our test account
        test_account_found = False
        if accounts:
            for account in accounts:
                if account.get('name') == 'Test Cash Account':
                    test_account_found = True
                    print(f"   ✅ Found our test account: {account}")
                    break
        
        if not test_account_found:
            print("   ❌ Test account not found in database")
            print("   📋 All accounts:")
            for i, account in enumerate(accounts[:5] if accounts else []):  # Show first 5
                print(f"      {i+1}. {account.get('name', 'No name')} ({account.get('account_type', 'No type')})")
                
    except Exception as e:
        print(f"   ❌ ERROR fetching accounts: {e}")

if __name__ == "__main__":
    test_account_creation()
