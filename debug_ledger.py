#!/usr/bin/env python3
"""
Debug script to check ledger data
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

def debug_ledger_data():
    """Debug ledger data to see what's happening"""
    print("🔍 Debug Ledger Data")
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
        
        # Debug journal entries
        print("\n🧪 Checking journal entries...")
        entries = accounting_system.get_journal_entries()
        print(f"📊 Found {len(entries)} journal entries")
        
        if entries:
            print("📋 Sample entries:")
            for i, entry in enumerate(entries[:3]):  # Show first 3 entries
                print(f"   Entry {i+1}: {entry}")
        
        # Debug accounts
        print("\n🧪 Checking accounts...")
        accounts = accounting_system.get_all_accounts()
        print(f"📊 Found {len(accounts)} accounts")
        
        if accounts:
            print("📋 Sample accounts (tuple format):")
            for i, account in enumerate(accounts[:5]):  # Show first 5 accounts
                print(f"   Account {i+1}: {account}")
        
        # Debug trial balance
        print("\n🧪 Checking trial balance...")
        trial_balance = accounting_system.get_trial_balance()
        print(f"📊 Trial balance has {len(trial_balance)} entries")
        
        if trial_balance:
            print("📋 Trial balance entries:")
            for entry in trial_balance:
                print(f"   {entry}")
        
        # Debug ledger for a specific account
        if accounts:
            test_account = accounts[0][0]  # Get first account name
            print(f"\n🧪 Checking ledger for account: {test_account}")
            ledger_entries = accounting_system.get_ledger(test_account)
            print(f"📊 Found {len(ledger_entries)} ledger entries for {test_account}")
            
            if ledger_entries:
                print("📋 Ledger entries:")
                for entry in ledger_entries[:3]:
                    print(f"   {entry}")
        
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ledger_data()
