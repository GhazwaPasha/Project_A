#!/usr/bin/env python3
"""
Test script to reproduce and verify the account validation bug
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.accounting_system import AccountingSystem
from datetime import datetime

def test_account_validation():
    """Test various account formats to identify the validation issue."""
    
    print("=== Account Validation Test ===")
    
    # Initialize accounting system
    system = AccountingSystem()
    
    # Get some actual accounts from the system
    accounts = system.get_postable_accounts()
    print(f"\nFound {len(accounts)} postable accounts in the system")
      # Test with a few sample accounts
    test_accounts = accounts[:3] if accounts else []
    
    for name, account_type, code, parent_code, level, is_postable, description in test_accounts:
        print(f"\n--- Testing Account: {name} (Type: {account_type}, Code: {code}) ---")
        
        # Test different formats
        formats_to_test = [
            name,  # Just the name
            code,  # Just the code  
            f"{code} - {name}"  # Code - Name format (UI format)
        ]
        
        for account_format in formats_to_test:
            print(f"\nTesting format: '{account_format}'")
            
            try:
                # Test if account exists and is postable
                is_postable = system.is_account_postable(account_format)
                print(f"  Is postable: {is_postable}")
                
                # Try to create a test journal entry
                try:
                    entry_id = system.add_journal_entry(
                        date="2024-01-01",
                        description="Test Entry",
                        debit_account=account_format,
                        credit_account=account_format,  # Same account for simplicity
                        amount=100.0
                    )
                    print(f"  ✓ Journal entry created successfully: {entry_id}")
                    
                    # Clean up - delete the test entry
                    cursor = system.conn.cursor()
                    cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
                    system.conn.commit()
                    
                except Exception as e:
                    print(f"  ✗ Journal entry failed: {e}")
                    
            except Exception as e:
                print(f"  ✗ General error: {e}")

if __name__ == "__main__":
    test_account_validation()
