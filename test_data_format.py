#!/usr/bin/env python3
"""
Quick test to identify the data format issue causing the 'list' object has no attribute 'get' error.
"""

import logging
logging.basicConfig(level=logging.INFO)

try:
    from src.core.accounting_system_postgresql import AccountingSystem
    
    print("Testing PostgreSQL accounting system data formats...")
    
    system = AccountingSystem()
    
    # Test account data format
    accounts = system.get_all_accounts()
    print(f"✅ Retrieved {len(accounts)} accounts")
    
    if accounts:
        print(f"Account data type: {type(accounts[0])}")
        print(f"Account sample: {accounts[0]}")
        print(f"Account fields: {accounts[0]._fields if hasattr(accounts[0], '_fields') else 'No _fields'}")
        
        # Test if it's a named tuple or regular tuple
        try:
            print(f"First field access [0]: {accounts[0][0]}")
            print(f"Second field access [1]: {accounts[0][1]}")
        except Exception as e:
            print(f"Tuple access error: {e}")
        
        # Test if it has .get() method
        try:
            print(f"Has .get() method: {hasattr(accounts[0], 'get')}")
            if hasattr(accounts[0], 'get'):
                print(f"Get test: {accounts[0].get('name', 'default')}")
        except Exception as e:
            print(f"Get method error: {e}")
    
    print("✅ Data format test completed")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
