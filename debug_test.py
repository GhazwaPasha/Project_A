#!/usr/bin/env python3
"""
Debug test to see what's happening with journal entry form
"""

from src.core.accounting_system import AccountingSystem

def test_entry_values():
    """Test what happens when we try to save empty values"""
    
    # Simulate form values
    date = "2025-06-17"
    description = ""  # Empty
    debit_account = ""  # Empty  
    credit_account = ""  # Empty
    amount = ""  # Empty
    
    print(f"Test 1 - Empty values:")
    print(f"  Date: '{date}'")
    print(f"  Description: '{description}'")
    print(f"  Debit Account: '{debit_account}'")
    print(f"  Credit Account: '{credit_account}'")
    print(f"  Amount: '{amount}'")
    
    # Validation check like in the form
    if not all([description, debit_account, credit_account, amount]):
        print("  VALIDATION FAILED: Not all fields filled")
        return
    else:
        print("  VALIDATION PASSED")
        
    # Test with valid values
    print("\nTest 2 - Valid values:")
    description = "Test transaction"
    debit_account = "1101 - Cash in Hand"
    credit_account = "4001 - Sales Revenue"
    amount = "100.00"
    
    print(f"  Date: '{date}'")
    print(f"  Description: '{description}'")
    print(f"  Debit Account: '{debit_account}'")
    print(f"  Credit Account: '{credit_account}'")
    print(f"  Amount: '{amount}'")
    
    if not all([description, debit_account, credit_account, amount]):
        print("  VALIDATION FAILED: Not all fields filled")
        return
    else:
        print("  VALIDATION PASSED")
        
    # Try saving to system
    try:
        system = AccountingSystem('accounting.db')
        result = system.add_journal_entry(date, description, debit_account, credit_account, amount)
        print(f"  SAVE SUCCESSFUL: Entry ID {result}")
        
        # Check if it was saved
        entries = system.get_recent_journal_entries(1)
        if entries:
            latest = entries[0]
            print(f"  VERIFIED: Latest entry = {latest['description']}, {latest['debit_account']}, {latest['credit_account']}, {latest['amount']}")
        
    except Exception as e:
        print(f"  SAVE FAILED: {e}")

if __name__ == "__main__":
    test_entry_values()
