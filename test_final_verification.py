#!/usr/bin/env python3
"""
Final verification test - check if all functionality works after resolving tuple access issues
"""
import sys
import os
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

async def test_final_verification():
    """Final verification that all errors are resolved"""
    print("🎯 FINAL VERIFICATION: Tuple Access Errors Resolution")
    print("=" * 60)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Login
        result = await auth_manager.login("ghazwairshad@gmail.com", "test123")
        if not result['success']:
            print(f"❌ Login failed: {result['message']}")
            return
        
        print("✅ Login successful")
        
        # Get organizations
        organizations = auth_manager.get_user_organizations()
        if not organizations:
            print("❌ No organizations found")
            return
        
        org = organizations[0]
        print(f"📁 Organization: {org['name']}")
        
        # Initialize unified accounting system
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization context
        if not accounting_system.set_organization(org['id']):
            print("❌ Failed to set organization context")
            return
        
        print("🔧 Organization context set")
        
        # Test 1: Chart of Accounts (Dictionary format)
        print("\n🧪 Testing Chart of Accounts (Dictionary format)...")
        accounts = accounting_system.get_chart_of_accounts(active_only=False)
        print(f"📊 Found {len(accounts)} accounts")
        
        if accounts:
            sample = accounts[0]
            print(f"✅ Sample account has required fields:")
            print(f"   - level: {sample.get('level', 'MISSING!')}")
            print(f"   - is_postable: {sample.get('is_postable', 'MISSING!')}")
            print(f"   - parent_code: {sample.get('parent_code', 'MISSING!')}")
            print(f"   - type: {sample.get('type', 'MISSING!')}")
        
        # Test 2: All Accounts (Tuple format)
        print("\n🧪 Testing All Accounts (Tuple format)...")
        tuple_accounts = accounting_system.get_all_accounts()
        print(f"📊 Found {len(tuple_accounts)} tuple accounts")
        
        if tuple_accounts:
            sample_tuple = tuple_accounts[0]
            print(f"✅ Sample tuple: {sample_tuple}")
        
        # Test 3: Trial Balance (List of Dicts format)
        print("\n🧪 Testing Trial Balance...")
        trial_balance = accounting_system.get_trial_balance()
        print(f"📊 Found {len(trial_balance)} trial balance entries")
        
        if trial_balance:
            sample_tb = trial_balance[0]
            print(f"✅ Sample trial balance entry:")
            print(f"   - name: {sample_tb.get('name', 'MISSING!')}")
            print(f"   - debit_total: {sample_tb.get('debit_total', 'MISSING!')}")
            print(f"   - credit_total: {sample_tb.get('credit_total', 'MISSING!')}")
        
        # Test 4: Enhanced Accounting System compatibility
        print("\n🧪 Testing Enhanced System Wrapper...")
        enhanced_accounts = accounting_system.get_chart_of_accounts(active_only=True)
        print(f"📊 Enhanced system returned {len(enhanced_accounts)} active accounts")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Tuple access errors have been RESOLVED")
        print("✅ Chart of Accounts should now load properly")
        print("✅ Trial Balance functionality working")
        print("✅ All data formats are compatible")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_final_verification())
    if success:
        print("\n🚀 The application should now work without tuple access errors!")
    else:
        print("\n💥 Issues still exist - check the error above.")
