#!/usr/bin/env python3
"""
Test get_ledger method for specific accounts
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

def test_get_ledger():
    """Test get_ledger method for Cash in Hand account"""
    print("🔍 Testing get_ledger method")
    print("=" * 40)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Login
        result = auth_manager.sign_in("ghazwairshad@gmail.com", "test123")
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
        print(f"📁 Organization: {org['name']} (ID: {org['id']})")
        
        # Initialize unified accounting system
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization context
        if not accounting_system.set_organization(org['id']):
            print("❌ Failed to set organization context")
            return
        
        print("🔧 Organization context set")
        
        # Test get_ledger for "Cash in Hand"
        print("\n🧪 Testing get_ledger for 'Cash in Hand'...")
        ledger_entries = accounting_system.get_ledger("Cash in Hand")
        print(f"📊 Found {len(ledger_entries)} ledger entries")
        
        if ledger_entries:
            print("📋 Ledger entries:")
            for entry in ledger_entries:
                print(f"   {entry}")
        else:
            print("❌ No ledger entries found")
        
        # Test get_ledger for "Rent"
        print("\n🧪 Testing get_ledger for 'Rent'...")
        ledger_entries = accounting_system.get_ledger("Rent")
        print(f"📊 Found {len(ledger_entries)} ledger entries")
        
        if ledger_entries:
            print("📋 Ledger entries:")
            for entry in ledger_entries:
                print(f"   {entry}")
        else:
            print("❌ No ledger entries found")
        
        # Test get_ledger for "Accounts Payable"
        print("\n🧪 Testing get_ledger for 'Accounts Payable'...")
        ledger_entries = accounting_system.get_ledger("Accounts Payable")
        print(f"📊 Found {len(ledger_entries)} ledger entries")
        
        if ledger_entries:
            print("📋 Ledger entries:")
            for entry in ledger_entries:
                print(f"   {entry}")
        else:
            print("❌ No ledger entries found")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_ledger()
