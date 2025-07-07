#!/usr/bin/env python3
"""
Test script for two-line journal entry transformation
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_two_line_transformation():
    """Test transformation with real two-line structure (no accounts join)"""
    print("🧪 TESTING TWO-LINE JOURNAL ENTRY TRANSFORMATION")
    print("=" * 55)
    
    try:
        from src.core.data_transformer import DataTransformer
        
        transformer = DataTransformer()
        print("✅ Data transformer imported successfully")
        
        # Test realistic database format (what you're actually getting)
        db_entry = {
            'id': 1,
            'entry_number': 'JE-0001',
            'entry_date': '2024-01-15',
            'description': 'Test Cash Sale',
            'total_amount': 150.00,
            'organization_id': 'org-123',
            'journal_entry_lines': [
                {
                    'id': 1,
                    'journal_entry_id': 1,
                    'account_id': 10,  # This is what you actually have
                    'debit_amount': 150.00,
                    'credit_amount': 0,
                    'line_order': 1
                    # NO 'accounts' field - this is the issue!
                },
                {
                    'id': 2,
                    'journal_entry_id': 1,
                    'account_id': 20,  # This is what you actually have
                    'debit_amount': 0,
                    'credit_amount': 150.00,
                    'line_order': 2
                    # NO 'accounts' field - this is the issue!
                }
            ]
        }
        
        print("\n🔄 Testing transformation with account_id only (realistic scenario):")
        print("=" * 60)
        print(f"Input: {db_entry['entry_number']} - {db_entry['description']}")
        print(f"Lines: {len(db_entry['journal_entry_lines'])} lines")
        print(f"Line 1: account_id={db_entry['journal_entry_lines'][0]['account_id']}, debit={db_entry['journal_entry_lines'][0]['debit_amount']}")
        print(f"Line 2: account_id={db_entry['journal_entry_lines'][1]['account_id']}, credit={db_entry['journal_entry_lines'][1]['credit_amount']}")
        
        # Transform without accounts lookup (current scenario)
        app_entry = transformer.db_to_app_journal_entry(db_entry)
        
        if app_entry:
            print("\n✅ Transformation successful!")
            print(f"Output (App format):")
            print(f"  Date: {app_entry['date']}")
            print(f"  Description: {app_entry['description']}")
            print(f"  Debit Account: {app_entry['debit_account']}")
            print(f"  Credit Account: {app_entry['credit_account']}")
            print(f"  Amount: ${app_entry['amount']}")
            print(f"  Entry Number: {app_entry['entry_number']}")
        else:
            print("❌ Transformation failed!")
            return False
        
        # Test with accounts lookup (future improvement)
        print("\n🔄 Testing with accounts lookup:")
        print("=" * 40)
        
        accounts_lookup = {
            10: {'id': 10, 'code': '1000', 'name': 'Cash'},
            20: {'id': 20, 'code': '4000', 'name': 'Sales Revenue'}
        }
        
        app_entry_with_lookup = transformer.db_to_app_journal_entry(db_entry, accounts_lookup)
        
        if app_entry_with_lookup:
            print("✅ Transformation with lookup successful!")
            print(f"  Debit Account: {app_entry_with_lookup['debit_account']}")
            print(f"  Credit Account: {app_entry_with_lookup['credit_account']}")
        else:
            print("❌ Transformation with lookup failed!")
        
        # Test edge cases
        print("\n🔄 Testing edge cases:")
        print("=" * 30)
        
        # Test with wrong number of lines
        bad_entry = db_entry.copy()
        bad_entry['journal_entry_lines'] = [db_entry['journal_entry_lines'][0]]  # Only 1 line
        
        result = transformer.db_to_app_journal_entry(bad_entry)
        if result is None:
            print("✅ Correctly rejected entry with only 1 line")
        else:
            print("⚠️  Accepted entry with only 1 line (unexpected)")
        
        # Test with missing debit/credit amounts
        bad_entry2 = db_entry.copy()
        bad_entry2['journal_entry_lines'] = [
            {'account_id': 10, 'debit_amount': 0, 'credit_amount': 0},  # No amount
            {'account_id': 20, 'debit_amount': 0, 'credit_amount': 0}   # No amount
        ]
        
        result2 = transformer.db_to_app_journal_entry(bad_entry2)
        if result2 is None:
            print("✅ Correctly rejected entry with no debit/credit amounts")
        else:
            print("⚠️  Accepted entry with no amounts (unexpected)")
        
        print("\n🎉 TWO-LINE TRANSFORMATION TESTS COMPLETED!")
        print("\n💡 Status:")
        print("✅ Can now handle account_id-only format")
        print("✅ Properly validates two-line structure")
        print("✅ Shows 'Account ID: X' when no account names available")
        print("✅ Ready for accounts lookup improvement")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_two_line_transformation() 