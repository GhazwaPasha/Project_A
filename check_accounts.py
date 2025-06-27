#!/usr/bin/env python3
"""
Check accounts and their codes
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.accounting_system_unified import AccountingSystem

def check_accounts():
    """Check what accounts exist"""
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
        print(f"📁 Organization: {org['name']}")
        
        # Initialize accounting system
        accounting_system = AccountingSystem(auth_manager)
        
        # Set organization context
        if not accounting_system.set_organization(org['id']):
            print("❌ Failed to set organization context")
            return
        
        print("🔧 Organization context set")
        
        # Get accounts
        accounts = accounting_system.get_chart_of_accounts()
        print(f"\n📊 Found {len(accounts)} accounts")
        
        # Look for cash-related accounts
        print("\n🔍 Cash-related accounts:")
        cash_accounts = [acc for acc in accounts if 'cash' in acc.get('name', '').lower()]
        for acc in cash_accounts:
            print(f"  • {acc.get('code', '')} - {acc.get('name', '')} (Type: {acc.get('type', '')})")
        
        # Look for account with code 1001
        print("\n🔍 Account with code 1001:")
        code_1001 = [acc for acc in accounts if acc.get('code') == '1001']
        if code_1001:
            for acc in code_1001:
                print(f"  • {acc.get('code', '')} - {acc.get('name', '')} (Type: {acc.get('type', '')})")
        else:
            print("  No account found with code 1001")
        
        # Get journal entries to see what we're trying to match
        print("\n🔍 Journal entries with 'cash' accounts:")
        entries = accounting_system.get_journal_entries()
        cash_entries = [e for e in entries if 'cash' in e.get('debit_account', '').lower() or 'cash' in e.get('credit_account', '').lower()]
        for entry in cash_entries:
            print(f"  • {entry.get('date')}: {entry.get('debit_account')} → {entry.get('credit_account')} (${entry.get('amount')})")
        
        print("\n✅ Check completed!")
        
    except Exception as e:
        print(f"❌ Check failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_accounts()
