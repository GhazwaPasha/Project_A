"""
Business Story Journal Entries Generator
Creates realistic journal entries telling the story of a business from inception to daily operations
Covers 2 years (2023-2025) with 50+ entries per day, using our existing chart of accounts
"""

import sys
import os
import random
from datetime import datetime, timedelta, date
import csv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.accounting_system import AccountingSystem

class BusinessStoryGenerator:
    def __init__(self):
        self.system = AccountingSystem("accounting.db")
        self.entries = []
        self.current_date = date(2023, 1, 1)  # Start of business
        self.end_date = date(2025, 6, 19)     # Today
        
        # Business metrics tracking
        self.cash_balance = 0
        self.total_assets_purchased = 0
        self.monthly_revenue_growth = 1.05  # 5% monthly growth
        self.base_monthly_expenses = 15000
        
        # Get our chart of accounts
        self.load_accounts()
        
    def load_accounts(self):
        """Load and organize accounts from our chart of accounts."""
        accounts = self.system.get_postable_accounts()
        self.accounts = {}
        
        for name, acc_type, code, parent_code, level, is_postable, description in accounts:
            if acc_type not in self.accounts:
                self.accounts[acc_type] = []
            self.accounts[acc_type].append(f"{code} - {name}")
        
        print(f"📋 Loaded {len(accounts)} accounts:")
        for acc_type, accs in self.accounts.items():
            print(f"  {acc_type}: {len(accs)} accounts")
    
    def add_entry(self, description, debit_account, credit_account, amount):
        """Add a journal entry to our list."""
        entry = {
            'date': self.current_date.strftime('%Y-%m-%d'),
            'description': description,
            'debit_account': debit_account,
            'credit_account': credit_account,
            'amount': amount
        }
        self.entries.append(entry)
        
        # Update cash tracking
        if 'Cash' in credit_account:
            self.cash_balance -= amount
        elif 'Cash' in debit_account:
            self.cash_balance += amount
    
    def get_random_account(self, account_type):
        """Get a random account of specified type."""
        return random.choice(self.accounts[account_type])
    
    def generate_startup_phase(self):
        """Generate entries for business startup (January 2023)."""
        print("🚀 Generating startup phase entries...")
        
        # Day 1: Business incorporation and initial investment
        self.current_date = date(2023, 1, 1)
        
        # Owner investment
        self.add_entry(
            "Initial capital investment by owner",
            "1102 - Cash at Bank",
            "3101 - Capital",
            100000
        )
        
        # Business registration fees
        self.add_entry(
            "Business registration and legal fees",
            "5203 - Professional Fees",
            "1102 - Cash at Bank",
            2500
        )
        
        # Day 2: Office setup
        self.current_date = date(2023, 1, 2)
        
        # Office rent deposit
        self.add_entry(
            "Office rent deposit - 3 months",
            "1131 - Prepaid Expenses",
            "1102 - Cash at Bank",
            15000
        )
        
        # Office furniture purchase
        self.add_entry(
            "Purchase office furniture and fixtures",
            "1205 - Furniture & Fixtures",
            "1102 - Cash at Bank",
            25000
        )
        
        # Day 3: Equipment and technology
        self.current_date = date(2023, 1, 3)
        
        # Computer equipment
        self.add_entry(
            "Purchase computers and IT equipment",
            "1203 - Equipment",
            "1102 - Cash at Bank",
            35000
        )
        
        # Software licenses
        self.add_entry(
            "Annual software licenses",
            "1131 - Prepaid Expenses",
            "1102 - Cash at Bank",
            8000
        )
        
        # Day 4: Initial inventory
        self.current_date = date(2023, 1, 4)
        
        # Raw materials
        self.add_entry(
            "Purchase initial raw materials inventory",
            "1121 - Inventory - Raw Materials",
            "1102 - Cash at Bank",
            45000
        )
        
        # Day 5: Insurance and utilities setup
        self.current_date = date(2023, 1, 5)
        
        # Insurance premium
        self.add_entry(
            "Annual business insurance premium",
            "1131 - Prepaid Expenses",
            "1102 - Cash at Bank",
            12000
        )
        
        # Utility deposits
        self.add_entry(
            "Utility connection deposits",
            "1131 - Prepaid Expenses",
            "1102 - Cash at Bank",
            3000
        )
        
        # Continue with more startup entries...
        for day in range(6, 32):  # Rest of January
            self.current_date = date(2023, 1, day)
            self.generate_daily_startup_entries()
    
    def generate_daily_startup_entries(self):
        """Generate daily entries during startup phase."""
        num_entries = random.randint(3, 8)
        
        for _ in range(num_entries):
            entry_type = random.choice([
                'equipment_purchase', 'professional_services', 'marketing_setup',
                'inventory_purchase', 'utilities', 'employee_setup'
            ])
            
            if entry_type == 'equipment_purchase':
                amount = random.randint(1000, 15000)
                self.add_entry(
                    f"Purchase of business equipment",
                    "1203 - Equipment",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'professional_services':
                amount = random.randint(500, 5000)
                self.add_entry(
                    f"Legal and professional consultation",
                    "5203 - Professional Fees",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'marketing_setup':
                amount = random.randint(2000, 10000)
                self.add_entry(
                    f"Initial marketing and advertising",
                    "5207 - Advertising Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'inventory_purchase':
                amount = random.randint(5000, 25000)
                inventory_type = random.choice(['1121 - Inventory - Raw Materials', '1123 - Inventory - Finished Goods'])
                self.add_entry(
                    f"Inventory purchase for operations",
                    inventory_type,
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'utilities':
                amount = random.randint(800, 2500)
                self.add_entry(
                    f"Utilities setup and connection",
                    "5105 - Utilities Expense",
                    "1102 - Cash at Bank",
                    amount
                )
    
    def generate_growth_phase(self):
        """Generate entries for business growth phase (Feb 2023 - Dec 2023)."""
        print("📈 Generating growth phase entries...")
        
        current = date(2023, 2, 1)
        end_growth = date(2023, 12, 31)
        
        month_num = 1
        while current <= end_growth:
            if current.day == 1:
                month_num += 1
                print(f"  Generating entries for {current.strftime('%B %Y')}...")
            
            self.current_date = current
            self.generate_daily_growth_entries(month_num)
            current += timedelta(days=1)
    
    def generate_daily_growth_entries(self, month_num):
        """Generate daily entries during growth phase."""
        base_entries = 50
        num_entries = random.randint(base_entries, base_entries + 20)
        
        # Calculate business growth
        revenue_multiplier = (self.monthly_revenue_growth ** month_num)
        daily_revenue_base = 5000 * revenue_multiplier
        
        for i in range(num_entries):
            entry_type = random.choice([
                'sales_cash', 'sales_credit', 'inventory_purchase', 'salaries',
                'rent', 'utilities', 'marketing', 'equipment_purchase',
                'loan_payment', 'supplier_payment', 'customer_payment',
                'depreciation', 'interest_income', 'professional_fees'
            ])
            
            if entry_type == 'sales_cash':
                amount = random.randint(int(daily_revenue_base * 0.3), int(daily_revenue_base * 0.7))
                self.add_entry(
                    f"Cash sales - day {self.current_date.day}",
                    "1101 - Cash in Hand",
                    "4101 - Sales Revenue",
                    amount
                )
            
            elif entry_type == 'sales_credit':
                amount = random.randint(int(daily_revenue_base * 0.5), int(daily_revenue_base * 1.2))
                self.add_entry(
                    f"Credit sales to customers",
                    "1111 - Accounts Receivable",
                    "4101 - Sales Revenue",
                    amount
                )
            
            elif entry_type == 'inventory_purchase':
                amount = random.randint(2000, 15000)
                self.add_entry(
                    f"Raw materials purchase",
                    "1121 - Inventory - Raw Materials",
                    "2101 - Accounts Payable",
                    amount
                )
            
            elif entry_type == 'salaries':
                amount = random.randint(8000, 25000)
                self.add_entry(
                    f"Employee salaries payment",
                    "5102 - Salaries Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'rent':
                if self.current_date.day <= 5:  # Pay rent early in month
                    amount = 5000
                    self.add_entry(
                        f"Monthly office rent",
                        "5104 - Rent Expense",
                        "1102 - Cash at Bank",
                        amount
                    )
            
            elif entry_type == 'utilities':
                amount = random.randint(1200, 3500)
                self.add_entry(
                    f"Utilities payment",
                    "5105 - Utilities Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'marketing':
                amount = random.randint(1500, 8000)
                self.add_entry(
                    f"Marketing and advertising expense",
                    "5207 - Advertising Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'customer_payment':
                amount = random.randint(3000, 20000)
                self.add_entry(
                    f"Customer payment received",
                    "1102 - Cash at Bank",
                    "1111 - Accounts Receivable",
                    amount
                )
            
            elif entry_type == 'supplier_payment':
                amount = random.randint(2000, 18000)
                self.add_entry(
                    f"Payment to suppliers",
                    "2101 - Accounts Payable",
                    "1102 - Cash at Bank",
                    amount
                )
    
    def generate_mature_phase(self):
        """Generate entries for mature business phase (2024 - 2025)."""
        print("🏢 Generating mature business phase entries...")
        
        current = date(2024, 1, 1)
        
        while current <= self.end_date:
            if current.day == 1:
                print(f"  Generating entries for {current.strftime('%B %Y')}...")
            
            self.current_date = current
            self.generate_daily_mature_entries()
            current += timedelta(days=1)
    
    def generate_daily_mature_entries(self):
        """Generate daily entries for mature business."""
        base_entries = 60  # More entries for established business
        num_entries = random.randint(base_entries, base_entries + 25)
        
        # Mature business has higher, more stable revenue
        daily_revenue_base = 15000
        
        for i in range(num_entries):
            entry_type = random.choice([
                'sales_cash', 'sales_credit', 'cost_of_goods', 'salaries',
                'rent', 'utilities', 'marketing', 'equipment_purchase',
                'loan_payment', 'supplier_payment', 'customer_payment',
                'depreciation', 'interest_income', 'professional_fees',
                'insurance', 'maintenance', 'travel', 'office_supplies',
                'bank_charges', 'interest_expense', 'dividend_payment'
            ])
            
            if entry_type == 'sales_cash':
                amount = random.randint(int(daily_revenue_base * 0.4), int(daily_revenue_base * 0.8))
                payment_method = random.choice(['Cash in Hand', 'Cash at Bank', 'Cash at POS'])
                self.add_entry(
                    f"Daily cash sales",
                    f"110{random.randint(1,3)} - {payment_method}",
                    "4101 - Sales Revenue",
                    amount
                )
            
            elif entry_type == 'cost_of_goods':
                amount = random.randint(3000, 12000)
                self.add_entry(
                    f"Cost of goods sold",
                    "5101 - Cost of Goods Sold",
                    "1123 - Inventory - Finished Goods",
                    amount
                )
            
            elif entry_type == 'customer_payment':
                amount = random.randint(5000, 35000)
                self.add_entry(
                    f"Customer payment on account",
                    "1102 - Cash at Bank",
                    "1111 - Accounts Receivable",
                    amount
                )
            
            elif entry_type == 'salaries':
                amount = random.randint(15000, 45000)
                self.add_entry(
                    f"Employee salaries and wages",
                    random.choice(["5102 - Salaries Expense", "5103 - Wages Expense"]),
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'office_supplies':
                amount = random.randint(500, 3000)
                self.add_entry(
                    f"Office supplies purchase",
                    "5106 - Supplies Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'maintenance':
                amount = random.randint(1000, 8000)
                self.add_entry(
                    f"Equipment maintenance and repairs",
                    "5206 - Maintenance Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'travel':
                amount = random.randint(800, 5000)
                self.add_entry(
                    f"Business travel expenses",
                    "5208 - Travel Expense",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'interest_income':
                amount = random.randint(100, 1500)
                self.add_entry(
                    f"Interest earned on bank deposits",
                    "1102 - Cash at Bank",
                    "4201 - Interest Income",
                    amount
                )
            
            elif entry_type == 'bank_charges':
                amount = random.randint(50, 500)
                self.add_entry(
                    f"Bank service charges",
                    "5302 - Bank Charges",
                    "1102 - Cash at Bank",
                    amount
                )
            
            elif entry_type == 'loan_payment':
                if self.current_date.day <= 10:  # Monthly loan payment
                    amount = random.randint(3000, 8000)
                    principal = int(amount * 0.7)
                    interest = amount - principal
                    
                    # Principal payment
                    self.add_entry(
                        f"Loan principal payment",
                        "2201 - Bank Loan",
                        "1102 - Cash at Bank",
                        principal
                    )
                    
                    # Interest payment
                    self.add_entry(
                        f"Loan interest payment",
                        "5301 - Interest Expense",
                        "1102 - Cash at Bank",
                        interest
                    )
            
            elif entry_type == 'depreciation':
                if self.current_date.day == 28:  # Monthly depreciation
                    amount = random.randint(2000, 6000)
                    self.add_entry(
                        f"Monthly depreciation expense",
                        "5205 - Depreciation Expense",
                        random.choice([
                            "1212 - Accumulated Depreciation - Buildings",
                            "1213 - Accumulated Depreciation - Equipment"
                        ]),
                        amount
                    )
    
    def generate_all_entries(self):
        """Generate all journal entries for the business story."""
        print("📚 Generating Business Story Journal Entries")
        print("=" * 60)
        
        # Phase 1: Startup (January 2023)
        self.generate_startup_phase()
        
        # Phase 2: Growth (Feb 2023 - Dec 2023)
        self.generate_growth_phase()
        
        # Phase 3: Mature Business (2024 - 2025)
        self.generate_mature_phase()
        
        print(f"\n✅ Generated {len(self.entries)} journal entries")
        print(f"📅 Date range: {self.entries[0]['date']} to {self.entries[-1]['date']}")
        
        return self.entries
    
    def save_to_csv(self, filename="business_story_journal_entries.csv"):
        """Save entries to CSV file."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'description', 'debit_account', 'credit_account', 'amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in self.entries:
                writer.writerow(entry)
        
        print(f"💾 Saved {len(self.entries)} entries to {filename}")
    
    def import_to_system(self):
        """Import all entries to the accounting system."""
        print(f"\n🔄 Importing {len(self.entries)} entries to accounting system...")
        
        success_count = 0
        error_count = 0
        
        for i, entry in enumerate(self.entries):
            try:
                self.system.add_journal_entry(
                    entry['date'],
                    entry['description'],
                    entry['debit_account'],
                    entry['credit_account'],
                    entry['amount']
                )
                success_count += 1
                
                if (i + 1) % 1000 == 0:
                    print(f"  Imported {i + 1:,} entries...")
                    
            except Exception as e:
                print(f"  ❌ Error importing entry {i+1}: {e}")
                error_count += 1
        
        print(f"\n✅ Import completed:")
        print(f"  Successfully imported: {success_count:,} entries")
        print(f"  Errors: {error_count}")

def main():
    """Main function to generate and import business story entries."""
    generator = BusinessStoryGenerator()
    
    # Generate all entries
    entries = generator.generate_all_entries()
    
    # Save to CSV for backup
    generator.save_to_csv()
    
    # Import to system
    generator.import_to_system()
    
    print("\n🎉 Business story journal entries generation completed!")
    print("📊 Your accounting system now contains a complete business narrative")
    print("   from startup to mature operations over 2+ years")

if __name__ == "__main__":
    main()
