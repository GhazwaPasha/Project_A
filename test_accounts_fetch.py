#!/usr/bin/env python3
"""Test script to check account data structure."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.supabase_manager import SupabaseManager
from src.core.accounting_system import AccountingSystem
from src.core.enhanced_accounting_system import EnhancedAccountingSystem
from dotenv import load_dotenv

load_dotenv()

def test_account_fetching():
    """Test how accounts are fetched and structured."""
    try:
        # Test direct database manager
        print("=== Testing SupabaseManager directly ===")
        db = SupabaseManager()
        db.set_user('43f33c5b-9e0d-403d-bee8-eca32b04a43e')  # ghazwairshad@gmail.com
        accounts = db.get_accounts('0946405f-3b8a-4fe5-8c29-125b39d9ca8e')  # The organization
        
        print(f"Found {len(accounts)} accounts from database")
        if accounts:
            print("Sample account structure:")
            sample = accounts[0]
            print(f"  Type: {type(sample)}")
            print(f"  Keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
            print(f"  Sample: {sample}")
            
            print("\nFirst 5 accounts:")
            for i, acc in enumerate(accounts[:5]):
                print(f"  {i+1}. {acc.get('code', 'N/A')} - {acc.get('name', 'N/A')}")
        
        # Test base accounting system
        print("\n=== Testing AccountingSystem ===")
        base_system = AccountingSystem(db)
        base_system.set_current_organization('0946405f-3b8a-4fe5-8c29-125b39d9ca8e')
        base_accounts = base_system.get_chart_of_accounts()
        
        print(f"Found {len(base_accounts)} accounts from base system")
        if base_accounts:
            print("Sample account from base system:")
            print(f"  Type: {type(base_accounts[0])}")
            print(f"  Sample: {base_accounts[0]}")
        
        # Test enhanced accounting system  
        print("\n=== Testing EnhancedAccountingSystem ===")
        enhanced_system = EnhancedAccountingSystem(base_system)
        enhanced_accounts = enhanced_system.get_all_accounts()
        
        print(f"Found {len(enhanced_accounts)} accounts from enhanced system")
        if enhanced_accounts:
            print("Sample account from enhanced system:")
            print(f"  Type: {type(enhanced_accounts[0])}")
            print(f"  Sample: {enhanced_accounts[0]}")
            
            print("\nFirst 5 accounts from enhanced system:")
            for i, acc in enumerate(enhanced_accounts[:5]):
                print(f"  {i+1}. {acc.get('code', 'N/A')} - {acc.get('name', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_account_fetching()
