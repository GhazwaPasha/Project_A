#!/usr/bin/env python3
"""
Test script to verify journal entry creation is working correctly
"""

import os
import sys
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_journal_entry_transformation():
    """Test the journal entry data transformation logic"""
    print("🧪 Testing journal entry transformation...")
    
    # Mock frontend data
    frontend_data = {
        'date': '2024-01-15',
        'description': 'Test Cash Sale',
        'debit_account': 'Cash',
        'credit_account': 'Sales Revenue',
        'amount': '150.00'
    }
    
    print(f"Frontend data: {frontend_data}")
    
    try:
        from src.core.auth_manager import AuthManager
        from src.core.unified_accounting_system import UnifiedAccountingSystem
        
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Initialize accounting system
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Test the transformation method directly
        try:
            journal_data, journal_lines = accounting_system._transform_journal_entry_data(frontend_data)
            
            print("✅ Transformation successful!")
            print(f"Journal Entry Data: {journal_data}")
            print(f"Journal Lines: {journal_lines}")
            
            # Validate the result
            assert journal_data['description'] == 'Test Cash Sale'
            assert journal_data['total_amount'] == 150.0
            assert len(journal_lines) == 2
            assert journal_lines[0]['debit_amount'] == 150.0
            assert journal_lines[1]['credit_amount'] == 150.0
            
            print("✅ All validations passed!")
            return True
            
        except Exception as e:
            print(f"❌ Transformation failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def test_account_resolution():
    """Test account name to ID resolution"""
    print("\n🧪 Testing account resolution...")
    
    try:
        from src.core.auth_manager import AuthManager
        from src.core.unified_accounting_system import UnifiedAccountingSystem
        
        # Initialize system
        auth_manager = AuthManager()
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Test account resolution for common account names
        test_accounts = ['Cash', 'Sales Revenue', 'Accounts Receivable', 'Equipment']
        
        for account_name in test_accounts:
            try:
                account_id = accounting_system._resolve_account_name_to_id(account_name)
                if account_id:
                    print(f"✅ '{account_name}' → ID: {account_id}")
                else:
                    print(f"⚠️ '{account_name}' → Not found")
            except Exception as e:
                print(f"❌ Error resolving '{account_name}': {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Account resolution test failed: {e}")
        return False

def test_full_journal_entry_flow():
    """Test the complete journal entry creation flow"""
    print("\n🧪 Testing full journal entry flow...")
    
    try:
        from src.core.auth_manager import AuthManager
        from src.core.unified_accounting_system import UnifiedAccountingSystem
        
        # Initialize system
        auth_manager = AuthManager()
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Try to set organization context (this might fail if no organization is set up)
        user = auth_manager.get_current_user()
        if user:
            orgs = auth_manager.get_user_organizations()
            if orgs:
                accounting_system.set_organization(orgs[0]['id'])
                print(f"✅ Organization context set: {orgs[0].get('name', 'Unknown')}")
            else:
                print("⚠️ No organizations found - continuing without org context")
        else:
            print("⚠️ No authenticated user - continuing in test mode")
        
        # Test journal entry creation
        test_entry = {
            'date': '2024-01-15',
            'description': 'Test Transaction - Cash Sale',
            'debit_account': 'Cash',
            'credit_account': 'Sales Revenue',
            'amount': '100.00'
        }
        
        print(f"Creating journal entry: {test_entry}")
        
        try:
            result = accounting_system.add_journal_entry(test_entry)
            
            if result:
                print(f"✅ Journal entry created successfully!")
                print(f"Entry Number: {result.get('entry_number', 'N/A')}")
                print(f"Description: {result.get('description', 'N/A')}")
                print(f"Amount: ${result.get('total_amount', 0)}")
                if result.get('queued'):
                    print("📱 Entry was queued for offline sync")
                return True
            else:
                print("❌ Journal entry creation returned None")
                return False
                
        except Exception as e:
            print(f"❌ Journal entry creation failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Full flow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Journal Entry Creation Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Data transformation
    if test_journal_entry_transformation():
        tests_passed += 1
    
    # Test 2: Account resolution
    if test_account_resolution():
        tests_passed += 1
    
    # Test 3: Full flow
    if test_full_journal_entry_flow():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Journal entry creation should be working.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 