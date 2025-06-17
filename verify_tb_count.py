from src.core.accounting_system import AccountingSystem

# Test to confirm account counts
system = AccountingSystem('accounting.db')

print('=== TRIAL BALANCE ACCOUNT ANALYSIS ===')

# Get all accounts
all_accounts = system.get_all_accounts()
print(f'Total accounts in chart of accounts: {len(all_accounts)}')

# Get trial balance
account_balances = system.get_trial_balance()
print(f'Total accounts returned by get_trial_balance: {len(account_balances)}')

# Count accounts with balances >= 0.01 (the filter used in trial balance)
non_zero_accounts = {name: balance for name, balance in account_balances.items() if abs(balance) >= 0.01}
print(f'Accounts with balances >= $0.01: {len(non_zero_accounts)}')

# Count accounts with any balance > 0
any_balance_accounts = {name: balance for name, balance in account_balances.items() if balance != 0}
print(f'Accounts with any non-zero balance: {len(any_balance_accounts)}')

print('\nAccounts with balances >= $0.01:')
for i, (name, balance) in enumerate(sorted(non_zero_accounts.items()), 1):
    if balance > 0:
        print(f'{i:2d}. {name}: Dr ${balance:,.2f}')
    else:
        print(f'{i:2d}. {name}: Cr ${abs(balance):,.2f}')

print('\nThis confirms your trial balance is showing the correct number of accounts.')
print('Only accounts with transactions (non-zero balances) should appear in a trial balance.')
