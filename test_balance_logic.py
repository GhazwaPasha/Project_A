#!/usr/bin/env python3
"""
Test ledger balance calculation logic
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

def test_ledger_balance_logic():
    """Test the ledger balance calculation logic"""
    print("🔍 Testing Ledger Balance Logic")
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
        
        # Get sample data
        accounts = accounting_system.get_chart_of_accounts(active_only=False)
        entries = accounting_system.get_journal_entries()
        
        print(f"\n📊 Found {len(accounts)} accounts and {len(entries)} journal entries")
        
        # Test the matching logic
        def find_matching_account_name(journal_account, card_account_name, card_account_code):
            """Check if the journal account matches the card account."""
            # Direct name match
            if journal_account == card_account_name:
                return True
            
            # Check if journal account is in "code - name" format
            if ' - ' in journal_account:
                parts = journal_account.split(' - ', 1)
                if len(parts) == 2:
                    j_code, j_name = parts
                    # Match by code and name
                    if j_code == card_account_code and j_name == card_account_name:
                        return True
                    # Match by name only (in case code is slightly different)
                    if j_name == card_account_name:
                        return True
            
            # Partial match for cases where formatting might be inconsistent
            if card_account_name in journal_account or journal_account in card_account_name:
                return True
                
            return False
        
        # Calculate balances for each account
        account_balances = {}
        account_counts = {}
        
        print("\n🧮 Calculating balances...")
        
        for entry in entries:
            debit_account = entry.get('debit_account', '')
            credit_account = entry.get('credit_account', '')
            amount = float(entry.get('amount', 0))
            
            print(f"Entry: {debit_account} -> {credit_account} : ${amount}")
            
            # Process each account
            for account in accounts:
                account_name = account['name']
                account_code = account.get('code', '')
                
                # Check if this entry affects this account
                is_debit_match = find_matching_account_name(debit_account, account_name, account_code)
                is_credit_match = find_matching_account_name(credit_account, account_name, account_code)
                
                if is_debit_match or is_credit_match:
                    if account_name not in account_balances:
                        account_balances[account_name] = 0.0
                        account_counts[account_name] = 0
                    
                    if is_debit_match:
                        account_balances[account_name] += amount
                        account_counts[account_name] += 1
                        print(f"  ✅ Debit match: {account_name} (+${amount})")
                    
                    if is_credit_match:
                        account_balances[account_name] -= amount
                        account_counts[account_name] += 1
                        print(f"  ✅ Credit match: {account_name} (-${amount})")
        
        # Show results
        print(f"\n📈 Balance Results:")
        for account_name, balance in account_balances.items():
            count = account_counts.get(account_name, 0)
            print(f"  {account_name}: ${balance:.2f} ({count} transactions)")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ledger_balance_logic()
