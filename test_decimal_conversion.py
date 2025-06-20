#!/usr/bin/env python3
"""Test decimal conversion to identify the exact issue."""

from decimal import Decimal
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.config import DatabaseConfig
from core.database_manager import DatabaseManager
from core.accounting_system_postgresql import AccountingSystemPostgreSQL

def test_decimal_conversion():
    """Test various decimal conversion scenarios."""
    print("Testing decimal conversion scenarios...")
    
    test_values = [
        "100",
        "100.50",
        "1000.00",
        "$100.50",
        "1,000.50",
        "$1,000.50",
        100,
        100.50,
        "",
        "abc",
        "100.50.50",
        None
    ]
    
    for value in test_values:
        try:
            print(f"\nTesting value: {repr(value)}")
            
            # Clean and convert amount to Decimal
            if isinstance(value, str):
                # Remove currency symbols, commas, and extra whitespace
                cleaned_amount = value.replace('$', '').replace(',', '').strip()
                if not cleaned_amount:
                    raise ValueError("Empty amount")
                amount_decimal = Decimal(cleaned_amount)
            elif value is None:
                raise ValueError("None amount")
            else:
                amount_decimal = Decimal(str(value))
            
            # Ensure positive amount
            if amount_decimal < 0:
                raise ValueError("Amount cannot be negative")
                
            print(f"  ✓ Success: {amount_decimal}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")

def test_journal_entry():
    """Test adding a journal entry with the accounting system."""
    print("\n" + "="*50)
    print("Testing journal entry addition...")
    
    try:        # Initialize the system
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        system = AccountingSystemPostgreSQL(config)
          # Test with a simple entry
        print("\nTesting with amount '100.50'...")
        entry_id = system.add_journal_entry(
            date=datetime.now().date(),
            description="Test entry",
            debit_account="Cash",
            credit_account="Revenue",
            amount="100.50"
        )
        print(f"✓ Successfully added journal entry: {entry_id}")
        
        # Test with formatted amount
        print("\nTesting with amount '$1,000.50'...")
        entry_id = system.add_journal_entry(
            date=datetime.now().date(),
            description="Test entry with formatting",
            debit_account="Cash",
            credit_account="Revenue", 
            amount="$1,000.50"
        )
        print(f"✓ Successfully added journal entry: {entry_id}")
        
    except Exception as e:
        print(f"✗ Error adding journal entry: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_decimal_conversion()
    test_journal_entry()
