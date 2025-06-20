#!/usr/bin/env python3
"""
Script to check the current data in the PostgreSQL database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.accounting_system_postgresql import AccountingSystemPostgreSQL
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    try:
        # Initialize the system
        print("Connecting to PostgreSQL database...")
        system = AccountingSystemPostgreSQL()
        
        # Get statistics
        stats = system.get_statistics()
        print('\n=== Database Statistics ===')
        for key, value in stats.items():
            print(f'  {key}: {value}')
        
        # Get accounts
        print('\n=== Sample Accounts ===')
        accounts = system.get_all_accounts()
        for i, acc in enumerate(accounts[:5]):
            print(f'  {i+1}. {acc["name"]} ({acc["code"]}) - {acc["type"]}')
        
        print(f'\nTotal accounts: {len(accounts)}')
        
        # Get journal entries
        print('\n=== Sample Journal Entries ===')
        entries = system.get_journal_entries(limit=5)
        for i, entry in enumerate(entries[:3]):
            print(f'  {i+1}. {entry["debit_account_name"]} -> {entry["credit_account_name"]}: ${entry["amount"]} ({entry["entry_date"]})')
        
        all_entries = system.get_journal_entries()
        print(f'\nTotal journal entries: {len(all_entries)}')
          # Check trial balance
        print('\n=== Trial Balance Summary ===')
        trial_balance = system.get_trial_balance()
        total_debits = sum(float(item["debit_total"]) for item in trial_balance if item["debit_total"])
        total_credits = sum(float(item["credit_total"]) for item in trial_balance if item["credit_total"])
        print(f'Total Debits: ${total_debits:,.2f}')
        print(f'Total Credits: ${total_credits:,.2f}')
        print(f'Difference: ${abs(total_debits - total_credits):,.2f}')
        
        print(f'Trial Balance Items: {len(trial_balance)}')
        
        # Show some sample trial balance items
        print('\nSample Trial Balance Items:')
        for i, item in enumerate(trial_balance[:5]):
            debit_bal = float(item["debit_total"]) if item["debit_total"] else 0
            credit_bal = float(item["credit_total"]) if item["credit_total"] else 0
            net_balance = debit_bal - credit_bal
            print(f'  {i+1}. {item["name"]} ({item["code"]}): Dr ${debit_bal:,.2f}, Cr ${credit_bal:,.2f}, Net ${net_balance:,.2f}')
        
        print('\n=== Connection Status ===')
        print('✅ PostgreSQL connection successful')
        print('✅ Data retrieval working')
        print('✅ All systems operational')
        
    except Exception as e:
        print(f'\n❌ Error: {e}')
        logging.error(f"Error checking data: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
