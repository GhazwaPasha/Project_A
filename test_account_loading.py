#!/usr/bin/env python3
"""Test account loading functionality."""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.config import DatabaseConfig
from core.database_manager import DatabaseManager
from core.accounting_system_postgresql import AccountingSystemPostgreSQL

def test_account_loading():
    """Test if accounts are being loaded properly."""
    print("Testing account loading...")
    
    try:
        # Initialize the system
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        system = AccountingSystemPostgreSQL(config)
        
        print("✓ System initialized successfully")
        
        # Test get_all_accounts
        print("\nTesting get_all_accounts()...")
        accounts = system.get_all_accounts()
        print(f"✓ Found {len(accounts)} accounts")
        
        if accounts:
            print("\nFirst 5 accounts:")
            for i, acc in enumerate(accounts[:5]):
                print(f"  {i+1}. {acc}")
                
        # Test get_postable_accounts
        print("\nTesting get_postable_accounts()...")
        postable_accounts = system.get_postable_accounts()
        print(f"✓ Found {len(postable_accounts)} postable accounts")
        
        if postable_accounts:
            print("\nFirst 5 postable accounts:")
            for i, acc in enumerate(postable_accounts[:5]):
                print(f"  {i+1}. {acc}")
        
        # Test how the UI would process them
        print("\nTesting UI account formatting...")
        accounts_for_ui = [f"{acc['code']} - {acc['name']}" for acc in accounts if acc['is_postable']]
        print(f"✓ Formatted {len(accounts_for_ui)} accounts for UI")
        
        if accounts_for_ui:
            print("\nFirst 5 formatted accounts:")
            for i, acc in enumerate(accounts_for_ui[:5]):
                print(f"  {i+1}. {acc}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_account_loading()
