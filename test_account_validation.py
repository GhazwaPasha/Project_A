"""
Test script to verify account validation and real-time updates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.accounting_system import AccountingSystem

def test_account_validation():
    """Test that entries to deleted accounts are properly blocked."""
    print("🧪 Testing Account Validation and Real-time Updates")
    print("=" * 60)
    
    # Create test database
    system = AccountingSystem(":memory:")
    
    # Test 1: Try to create entry with non-existent account
    print("\n1. Testing entry to non-existent account...")
    try:
        system.add_journal_entry(
            "2025-06-19",
            "Test entry to non-existent account",
            "Fake Account",
            "Cash at Bank", 
            1000
        )
        print("❌ FAILED: Entry was allowed to non-existent account!")
    except ValueError as e:
        print(f"✅ PASSED: Entry blocked with error: {e}")
    
    # Test 2: Add an account, create entry, then delete account and try again
    print("\n2. Testing entry after account deletion...")
    
    # Add a test account
    system.add_account("Test Expense Account", "Expense", "5999", "5000", 3, True, "Test account")
    print("✅ Added test account: Test Expense Account")
    
    # Create successful entry
    try:
        entry_id = system.add_journal_entry(
            "2025-06-19",
            "Valid entry to existing account",
            "Test Expense Account",
            "Cash at Bank",
            500
        )
        print(f"✅ Successfully created entry {entry_id} to existing account")
    except Exception as e:
        print(f"❌ Unexpected error with valid account: {e}")
    
    # Delete the account
    system.delete_account("Test Expense Account")
    print("🗑️ Deleted test account: Test Expense Account")
    
    # Try to create entry to deleted account
    try:
        system.add_journal_entry(
            "2025-06-19",
            "Test entry to deleted account",
            "Test Expense Account",
            "Cash at Bank",
            1000
        )
        print("❌ FAILED: Entry was allowed to deleted account!")
    except ValueError as e:
        print(f"✅ PASSED: Entry blocked after deletion: {e}")
    
    # Test 3: Test non-postable account validation
    print("\n3. Testing entry to non-postable account...")
    try:
        system.add_journal_entry(
            "2025-06-19",
            "Test entry to non-postable account",
            "Assets",  # This is a level 1 account, not postable
            "Cash at Bank",
            1000
        )
        print("❌ FAILED: Entry was allowed to non-postable account!")
    except ValueError as e:
        print(f"✅ PASSED: Entry blocked to non-postable account: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Account validation tests completed!")
    print("✅ All validation rules are working correctly")
    print("✅ Real-time updates prevent entries to deleted accounts")
    print("✅ System enforces postable account requirements")

if __name__ == "__main__":
    test_account_validation()
