from src.core.accounting_system import AccountingSystem

# Quick test to verify the trial balance fix works
system = AccountingSystem('accounting.db')

print('=== TESTING FIXED GET_TRIAL_BALANCE METHOD ===')

# Test the fixed get_trial_balance method
trial_balance = system.get_trial_balance()
print(f"Trial balance contains {len(trial_balance)} accounts")

# Show accounts with non-zero balances
non_zero_accounts = [(name, balance) for name, balance in trial_balance.items() if abs(balance) >= 0.01]
print(f"Accounts with non-zero balances: {len(non_zero_accounts)}")

# Calculate totals
total_debits = sum(balance for balance in trial_balance.values() if balance > 0)
total_credits = sum(abs(balance) for balance in trial_balance.values() if balance < 0)
difference = abs(total_debits - total_credits)

print(f"Total Debits: ${total_debits:,.2f}")
print(f"Total Credits: ${total_credits:,.2f}")
print(f"Difference: ${difference:,.2f}")
print(f"Balanced: {difference < 0.01}")

# Show top 5 accounts by balance
print(f"\nTop 5 accounts by balance:")
sorted_accounts = sorted(non_zero_accounts, key=lambda x: abs(x[1]), reverse=True)
for i, (name, balance) in enumerate(sorted_accounts[:5]):
    print(f"  {i+1}. {name}: ${balance:,.2f}")

print("\n=== DONE ===")
