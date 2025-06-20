#!/usr/bin/env python3
"""
View existing data in Supabase database
"""

def view_existing_data():
    try:
        from src.core.accounting_system_postgresql import AccountingSystem
        
        print("🔍 Viewing existing data in Supabase database...")
        system = AccountingSystem()
        print("✅ Connected to database")
        
        # Get all accounts
        print("\n📁 ACCOUNTS:")
        print("=" * 60)
        accounts = system.get_all_accounts()
        print(f"Total accounts: {len(accounts)}")
        
        if accounts:
            print("\nAccount List:")
            for i, acc in enumerate(accounts, 1):
                print(f"{i:2d}. {acc['name']} ({acc['type']}) - Code: {acc['code']} - Postable: {acc['is_postable']}")
        
        # Get journal entries
        print(f"\n📝 JOURNAL ENTRIES:")
        print("=" * 60)
        entries = system.get_journal_entries(limit=20)
        print(f"Total entries (showing last 20): {len(entries)}")
        
        if entries:
            print("\nJournal Entries:")
            for i, entry in enumerate(entries, 1):
                print(f"{i:2d}. {entry['entry_date']} | {entry['debit_account_name']} -> {entry['credit_account_name']} | ${entry['amount']} | {entry['description']}")
        
        # Get statistics
        print(f"\n📊 DATABASE STATISTICS:")
        print("=" * 60)
        stats = system.get_statistics()
        print(f"Total accounts: {stats['total_accounts']}")
        print(f"Postable accounts: {stats['postable_accounts']}")
        print(f"Total journal entries: {stats['total_entries']}")
        print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}" if stats['date_range'][0] else "No entries")
        
        # Test trial balance
        print(f"\n⚖️  TRIAL BALANCE TEST:")
        print("=" * 60)
        trial_balance = system.get_trial_balance()
        print(f"Accounts with balances: {len(trial_balance)}")
        
        if trial_balance:
            print("\nAccount Balances:")
            total_debits = 0
            total_credits = 0
            for acc in trial_balance:
                debit_total = float(acc['debit_total'])
                credit_total = float(acc['credit_total'])
                net_balance = debit_total - credit_total
                total_debits += debit_total
                total_credits += credit_total
                print(f"  {acc['name']} ({acc['code']}): Dr {debit_total:.2f} Cr {credit_total:.2f} Net: {net_balance:.2f}")
            
            print(f"\nTotals: Dr {total_debits:.2f} Cr {total_credits:.2f}")
            print(f"Difference: {abs(total_debits - total_credits):.2f}")
        
        print(f"\n✅ Data review completed!")
        
    except Exception as e:
        print(f"❌ Error viewing data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    view_existing_data()
