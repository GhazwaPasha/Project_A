import sys
sys.path.append('src')

from core.accounting_system import AccountingSystem
from datetime import datetime, timedelta

# Initialize the system
system = AccountingSystem()

print("=== TESTING BALANCE CALCULATIONS ===")

# Test date range (last 30 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

from_date_str = start_date.strftime("%Y-%m-%d")
to_date_str = end_date.strftime("%Y-%m-%d")

print(f"Date range: {from_date_str} to {to_date_str}")

# Get all entries in the date range
entries = system.get_journal_entries_by_date_range(from_date_str, to_date_str)
print(f"Total entries in range: {len(entries)}")

# Calculate balances for each account (similar to _refresh_balances method)
account_balances = {}
account_counts = {}

for entry in entries:
    if len(entry) >= 6:
        debit_account = entry[3]
        credit_account = entry[4]
        amount = float(entry[5])
        
        # Update debit account
        if debit_account not in account_balances:
            account_balances[debit_account] = 0.0
            account_counts[debit_account] = 0
        account_balances[debit_account] += amount
        account_counts[debit_account] += 1
        
        # Update credit account
        if credit_account not in account_balances:
            account_balances[credit_account] = 0.0
            account_counts[credit_account] = 0
        account_balances[credit_account] -= amount
        account_counts[credit_account] += 1

print(f"\n=== TOP 10 ACCOUNTS BY BALANCE ===")
# Sort accounts by absolute balance value
sorted_accounts = sorted(account_balances.items(), key=lambda x: abs(x[1]), reverse=True)

for i, (account, balance) in enumerate(sorted_accounts[:10]):
    count = account_counts[account]
    print(f"{i+1:2d}. {account:30s} Balance: ${balance:>10.2f} ({count} transactions)")

print(f"\n=== TESTING LEDGER METHOD FOR TOP ACCOUNT ===")
if sorted_accounts:
    top_account = sorted_accounts[0][0]
    print(f"Testing ledger for: {top_account}")
    
    # Get the account name without code if it has one
    if " - " in top_account:
        clean_account_name = top_account.split(" - ", 1)[1]
    else:
        clean_account_name = top_account
    
    print(f"Clean account name: {clean_account_name}")
    
    # Test the ledger method
    ledger_entries = system.get_ledger(clean_account_name, from_date_str, to_date_str)
    print(f"Ledger entries found: {len(ledger_entries)}")
    
    if ledger_entries:
        print("Sample ledger entries:")
        for i, entry in enumerate(ledger_entries[:3]):
            date, description, debit_account, credit_account, amount = entry
            print(f"  {i+1}. {date} - Dr: {debit_account} Cr: {credit_account} Amount: ${amount}")
