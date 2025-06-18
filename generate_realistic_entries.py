"""
Check Chart of Accounts and Generate Realistic Journal Entries
This script will first examine the actual chart of accounts in the system,
then generate journal entries using the correct account names.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.accounting_system import AccountingSystem
import pandas as pd
from datetime import datetime, timedelta
import random

def get_chart_of_accounts():
    """Get the actual chart of accounts from the system."""
    print("🔍 Examining Chart of Accounts...")
    system = AccountingSystem("accounting.db")
    
    # Get all postable accounts (accounts that can have entries)
    accounts = system.get_postable_accounts()
    
    print(f"\n📊 Found {len(accounts)} postable accounts:")
    print("=" * 80)
    
    # Group by type for better organization
    by_type = {}
    for name, acc_type, code, parent_code, level, is_postable, description in accounts:
        if acc_type not in by_type:
            by_type[acc_type] = []
        by_type[acc_type].append((name, code, description))
    
    # Print organized by type
    for acc_type in ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']:
        if acc_type in by_type:
            print(f"\n🏷️  {acc_type.upper()} ACCOUNTS:")
            print("-" * 40)
            for name, code, desc in by_type[acc_type]:
                print(f"  {code} - {name}")
                if desc and desc.strip():
                    print(f"      └─ {desc}")
    
    system.close()
    return accounts

def generate_realistic_entries(accounts):
    """Generate realistic journal entries using actual account names."""
    print("\n\n🏗️  Generating Business Story Entries...")
    print("=" * 80)
    
    # Create a mapping of account types for easy access
    accounts_by_type = {}
    account_names = {}
    
    for name, acc_type, code, parent_code, level, is_postable, description in accounts:
        if acc_type not in accounts_by_type:
            accounts_by_type[acc_type] = []
        accounts_by_type[acc_type].append(name)
        account_names[name] = {'type': acc_type, 'code': code, 'desc': description}
    
    print("📝 Available account types and counts:")
    for acc_type, names in accounts_by_type.items():
        print(f"  {acc_type}: {len(names)} accounts")
    
    # Helper function to find accounts by keyword
    def find_account(keyword, acc_type=None):
        """Find account by keyword in name."""
        matches = []
        for name in account_names:
            if keyword.lower() in name.lower():
                if acc_type is None or account_names[name]['type'] == acc_type:
                    matches.append(name)
        return matches[0] if matches else None
    
    # Helper function to get random account of type
    def get_account(acc_type, keyword=None):
        """Get account of specific type, optionally matching keyword."""
        if acc_type not in accounts_by_type:
            return None
        
        candidates = accounts_by_type[acc_type]
        if keyword:
            filtered = [acc for acc in candidates if keyword.lower() in acc.lower()]
            if filtered:
                return filtered[0]
        
        return candidates[0] if candidates else None
    
    # Find key accounts we'll need
    cash_account = find_account("cash", "Asset") or get_account("Asset", "cash")
    bank_account = find_account("bank", "Asset") or get_account("Asset", "bank")
    revenue_account = get_account("Revenue", "sales") or get_account("Revenue")
    
    print(f"\n🎯 Key accounts identified:")
    print(f"  Cash Account: {cash_account}")
    print(f"  Bank Account: {bank_account}")
    print(f"  Revenue Account: {revenue_account}")
    
    if not cash_account or not revenue_account:
        print("\n❌ Error: Could not find essential accounts (Cash, Revenue)")
        print("Please check that your chart of accounts has basic Asset and Revenue accounts.")
        return []
    
    entries = []
    start_date = datetime(2023, 6, 19)  # Two years ago
    current_date = start_date
    
    print(f"\n📅 Generating entries from {start_date.strftime('%Y-%m-%d')} to today...")
    
    # Business inception entries (June 2023)
    print("\n🚀 Phase 1: Business Inception (June 2023)")
    
    # 1. Initial capital investment
    if get_account("Equity"):
        entries.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'description': 'Initial capital investment by owner',
            'debit_account': cash_account,
            'credit_account': get_account("Equity"),
            'amount': 50000
        })
    
    # 2. Bank account opening
    if bank_account and bank_account != cash_account:
        entries.append({
            'date': (current_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'description': 'Transfer cash to business bank account',
            'debit_account': bank_account,
            'credit_account': cash_account,
            'amount': 45000
        })
    
    # Move to daily operations
    current_date = datetime(2023, 7, 1)
    
    # Generate entries for each month over 2 years
    months_to_generate = 24  # 2 years
    entries_per_month = 50   # As requested
    
    for month in range(months_to_generate):
        month_start = current_date + timedelta(days=month * 30)
        
        print(f"📊 Generating {entries_per_month} entries for {month_start.strftime('%B %Y')}")
        
        # Generate daily entries for this month
        for day in range(entries_per_month):
            entry_date = month_start + timedelta(days=day % 30)
            
            # Random business activities
            activity = random.choice([
                'sales', 'expense', 'purchase', 'payment', 'receipt'
            ])
            
            try:
                if activity == 'sales' and revenue_account:
                    # Sales transaction
                    cash_acct = random.choice([cash_account, bank_account]) if bank_account else cash_account
                    entries.append({
                        'date': entry_date.strftime('%Y-%m-%d'),
                        'description': f'Sales revenue - {random.choice(["Product sales", "Service revenue", "Consulting fees"])}',
                        'debit_account': cash_acct,
                        'credit_account': revenue_account,
                        'amount': random.randint(100, 5000)
                    })
                
                elif activity == 'expense':
                    # Expense transaction
                    expense_accounts = accounts_by_type.get('Expense', [])
                    if expense_accounts:
                        expense_acct = random.choice(expense_accounts)
                        cash_acct = random.choice([cash_account, bank_account]) if bank_account else cash_account
                        entries.append({
                            'date': entry_date.strftime('%Y-%m-%d'),
                            'description': f'Business expense - {expense_acct.split()[-1] if expense_acct else "General"}',
                            'debit_account': expense_acct,
                            'credit_account': cash_acct,
                            'amount': random.randint(50, 2000)
                        })
                
                elif activity == 'purchase':
                    # Asset purchase
                    asset_accounts = [acc for acc in accounts_by_type.get('Asset', []) 
                                    if acc not in [cash_account, bank_account]]
                    if asset_accounts:
                        asset_acct = random.choice(asset_accounts)
                        cash_acct = random.choice([cash_account, bank_account]) if bank_account else cash_account
                        entries.append({
                            'date': entry_date.strftime('%Y-%m-%d'),
                            'description': f'Purchase of {asset_acct.lower()}',
                            'debit_account': asset_acct,
                            'credit_account': cash_acct,
                            'amount': random.randint(200, 10000)
                        })
                
                elif activity == 'payment':
                    # Liability payment
                    liability_accounts = accounts_by_type.get('Liability', [])
                    if liability_accounts:
                        liability_acct = random.choice(liability_accounts)
                        cash_acct = random.choice([cash_account, bank_account]) if bank_account else cash_account
                        entries.append({
                            'date': entry_date.strftime('%Y-%m-%d'),
                            'description': f'Payment of {liability_acct.lower()}',
                            'debit_account': liability_acct,
                            'credit_account': cash_acct,
                            'amount': random.randint(100, 3000)
                        })
                
                elif activity == 'receipt' and revenue_account:
                    # Additional revenue
                    cash_acct = random.choice([cash_account, bank_account]) if bank_account else cash_account
                    entries.append({
                        'date': entry_date.strftime('%Y-%m-%d'),
                        'description': f'Other income - {random.choice(["Interest", "Rental", "Commission"])}',
                        'debit_account': cash_acct,
                        'credit_account': revenue_account,
                        'amount': random.randint(25, 1000)
                    })
                        
            except Exception as e:
                print(f"⚠️  Skipping entry due to error: {e}")
                continue
    
    print(f"\n✅ Generated {len(entries)} journal entries")
    return entries

def save_to_csv(entries):
    """Save entries to CSV for import."""
    if not entries:
        print("❌ No entries to save!")
        return
    
    df = pd.DataFrame(entries)
    filename = "realistic_business_entries.csv"
    df.to_csv(filename, index=False)
    print(f"\n💾 Entries saved to: {filename}")
    print(f"📁 File contains {len(entries)} entries ready for import")
    print("\n🔄 To import these entries:")
    print("1. Open the application")
    print("2. Go to Journal → Bulk Entry tab")
    print("3. Click 'Import from File'")
    print(f"4. Select the file: {filename}")
    
    # Show sample entries
    print(f"\n📋 Sample entries preview:")
    print("-" * 60)
    for i, entry in enumerate(entries[:5]):
        print(f"{i+1}. {entry['date']} - {entry['description'][:40]}...")
        print(f"   DR: {entry['debit_account'][:30]}")
        print(f"   CR: {entry['credit_account'][:30]}")
        print(f"   Amount: ${entry['amount']:,}")
        print()

if __name__ == "__main__":
    print("🏢 Realistic Business Journal Entries Generator")
    print("=" * 60)
    
    # Step 1: Get actual chart of accounts
    accounts = get_chart_of_accounts()
    
    if not accounts:
        print("❌ No accounts found! Please check your database.")
        exit(1)
    
    # Step 2: Generate realistic entries
    entries = generate_realistic_entries(accounts)
    
    # Step 3: Save to CSV
    save_to_csv(entries)
    
    print("\n🎉 Business story generation complete!")
    print("📈 Ready to import a complete 2-year business journey!")
