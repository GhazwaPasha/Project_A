#!/usr/bin/env python3
"""
Add sample accounting data to Supabase database
"""

def add_sample_data():
    try:
        from src.core.accounting_system_postgresql import AccountingSystem
        from datetime import datetime, date
        
        print("🚀 Adding sample accounting data to Supabase...")
        system = AccountingSystem()
        print("✅ Connected to accounting system")
        
        # Check if we already have accounts
        existing_accounts = system.get_all_accounts()
        print(f"📊 Found {len(existing_accounts)} existing accounts")
        
        sample_accounts = [
            # Assets
            ("Cash", "Asset", "1001", None, True, "Main cash account"),
            ("Bank Account", "Asset", "1002", None, True, "Primary bank account"),
            ("Accounts Receivable", "Asset", "1100", None, True, "Money owed by customers"),
            ("Inventory", "Asset", "1200", None, True, "Goods for sale"),
            ("Equipment", "Asset", "1500", None, False, "Office equipment"),
            
            # Liabilities
            ("Accounts Payable", "Liability", "2001", None, True, "Money owed to suppliers"),
            ("Credit Card", "Liability", "2100", None, True, "Credit card debt"),
            ("Loan Payable", "Liability", "2500", None, True, "Business loan"),
            
            # Equity
            ("Owner's Equity", "Equity", "3000", None, False, "Owner's investment"),
            ("Retained Earnings", "Equity", "3100", None, False, "Accumulated earnings"),
            
            # Revenue
            ("Sales Revenue", "Revenue", "4000", None, True, "Income from sales"),
            ("Service Revenue", "Revenue", "4100", None, True, "Income from services"),
            
            # Expenses
            ("Office Supplies", "Expense", "5001", None, True, "Office supplies expense"),
            ("Rent Expense", "Expense", "5100", None, True, "Monthly rent"),
            ("Utilities", "Expense", "5200", None, True, "Electricity, water, etc."),
            ("Marketing", "Expense", "5300", None, True, "Advertising and marketing"),
        ]
        
        # Create accounts if they don't exist
        created_count = 0
        for name, acc_type, code, parent_code, is_postable, description in sample_accounts:
            try:
                # Check if account already exists
                existing = system.get_account_by_name(name)
                if not existing:
                    system.create_account(name, acc_type, code, parent_code, is_postable, description)
                    print(f"  ✅ Created account: {name} ({acc_type})")
                    created_count += 1
                else:
                    print(f"  ⏭️  Account already exists: {name}")
            except Exception as e:
                print(f"  ❌ Failed to create {name}: {e}")
        
        print(f"\n📁 Created {created_count} new accounts")
        
        # Add sample journal entries
        print(f"\n📝 Adding sample journal entries...")
        
        sample_entries = [
            # Initial investment
            ("Cash", "Owner's Equity", 10000, "Initial business investment", date(2024, 1, 1)),
            
            # Purchase equipment
            ("Equipment", "Cash", 2000, "Purchased office equipment", date(2024, 1, 2)),
            
            # First sale
            ("Cash", "Sales Revenue", 1500, "Sale to customer #001", date(2024, 1, 5)),
            
            # Pay rent
            ("Rent Expense", "Cash", 800, "January rent payment", date(2024, 1, 15)),
            
            # Purchase inventory
            ("Inventory", "Accounts Payable", 3000, "Purchased inventory on credit", date(2024, 1, 20)),
            
            # Another sale
            ("Cash", "Sales Revenue", 2200, "Sale to customer #002", date(2024, 1, 25)),
            
            # Pay utilities
            ("Utilities", "Cash", 150, "Electric bill payment", date(2024, 1, 30)),
            
            # Service revenue
            ("Bank Account", "Service Revenue", 1800, "Consulting service payment", date(2024, 2, 5)),
            
            # Marketing expense
            ("Marketing", "Credit Card", 500, "Online advertising campaign", date(2024, 2, 10)),
            
            # Office supplies
            ("Office Supplies", "Cash", 200, "Purchased office supplies", date(2024, 2, 12)),
        ]
        
        entry_count = 0
        for debit_acc, credit_acc, amount, description, entry_date in sample_entries:
            try:
                system.add_journal_entry(entry_date, description, debit_acc, credit_acc, amount)
                print(f"  ✅ Added entry: {debit_acc} -> {credit_acc} ${amount}")
                entry_count += 1
            except Exception as e:
                print(f"  ❌ Failed to add entry {debit_acc} -> {credit_acc}: {e}")
        
        print(f"\n📝 Created {entry_count} new journal entries")
        
        # Show final statistics
        stats = system.get_statistics()
        print(f"\n📈 Final database statistics:")
        print(f"  - Total accounts: {stats['total_accounts']}")
        print(f"  - Postable accounts: {stats['postable_accounts']}")
        print(f"  - Total entries: {stats['total_entries']}")
        print(f"  - Date range: {stats['date_range']}")
        
        print(f"\n🎉 Sample data added successfully!")
        print(f"💡 Now restart your application to see the data!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_sample_data()
