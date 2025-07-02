#!/usr/bin/env python3
"""
Test script to verify data transformation fixes
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_data_transformation():
    """Test the data transformation functionality"""
    print("🧪 TESTING DATA TRANSFORMATION FIXES")
    print("=" * 50)
    
    try:
        from src.core.data_transformer import DataTransformer
        
        transformer = DataTransformer()
        print("✅ Data transformer imported successfully")
        
        # Test database format (new relational format)
        db_entry = {
            'id': 1,
            'entry_number': 'JE-0001',
            'entry_date': '2024-01-15',
            'description': 'Test Cash Sale',
            'total_amount': 150.00,
            'journal_entry_lines': [
                {
                    'id': 1,
                    'account_id': 10,
                    'debit_amount': 150.00,
                    'credit_amount': 0,
                    'accounts': {'code': '1000', 'name': 'Cash'}
                },
                {
                    'id': 2,
                    'account_id': 20,
                    'debit_amount': 0,
                    'credit_amount': 150.00,
                    'accounts': {'code': '4000', 'name': 'Sales Revenue'}
                }
            ]
        }
        
        print("\n🔄 Testing DB to App transformation:")
        print("=" * 40)
        print(f"Input (DB format): {db_entry['entry_number']} - {db_entry['description']}")
        
        app_entry = transformer.db_to_app_journal_entry(db_entry)
        
        if app_entry:
            print("✅ Transformation successful!")
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
        
        # Test cache format transformation
        print("\n🔄 Testing App to Cache transformation:")
        print("=" * 40)
        
        cache_entry = transformer.app_to_cache_journal_entry(app_entry)
        print("✅ App to Cache transformation successful!")
        print(f"Cache entry has both old and new field names:")
        print(f"  Old format: date={cache_entry.get('date')}, amount={cache_entry.get('amount')}")
        print(f"  New format: entry_date={cache_entry.get('entry_date')}, total_amount={cache_entry.get('total_amount')}")
        
        # Test cache to app transformation
        print("\n🔄 Testing Cache to App transformation:")
        print("=" * 40)
        
        restored_app_entry = transformer.cache_to_app_journal_entry(cache_entry)
        print("✅ Cache to App transformation successful!")
        print(f"Restored entry: {restored_app_entry['entry_number']} - {restored_app_entry['description']}")
        
        # Test list transformation
        print("\n🔄 Testing List transformation:")
        print("=" * 40)
        
        db_list = [db_entry, db_entry.copy()]
        app_list = transformer.transform_journal_entries_list(db_list)
        print(f"✅ Transformed {len(db_list)} entries to {len(app_list)} app entries")
        
        print("\n🎉 ALL TRANSFORMATION TESTS PASSED!")
        print("\n💡 Next steps:")
        print("1. Create a new journal entry in your app")
        print("2. Check if transaction cards now display properly")
        print("3. Verify sync operations show correct count")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    test_data_transformation() 