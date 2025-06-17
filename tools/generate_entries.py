#!/usr/bin/env python3
"""
Script to populate the accounting system with realistic business transactions
covering incorporation and two years of operations.
"""

import os
import sys
import random
from datetime import datetime, timedelta
import decimal
from tqdm import tqdm

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.accounting_system import AccountingSystem

class BusinessTransactionGenerator:
    def __init__(self, system):
        self.system = system
        decimal.getcontext().prec = 2
        
        # Business parameters
        self.company_name = "TechSolutions Inc."
        self.initial_investment = 500000  # Initial capital investment
        self.monthly_rent = 3500
        self.average_salary = 5500
        self.employee_count = 15
        self.product_cost_range = (50, 200)  # Cost per unit
        self.selling_price_multiplier = 2.5  # Markup multiplier
          # Get accounts from system
        cursor = self.system.conn.cursor()
        cursor.execute('SELECT name, code FROM accounts WHERE is_postable = 1')
        db_accounts = cursor.fetchall()
        
        # Common accounts with proper code-name format
        self.accounts = {
            'cash': f"1110 - Cash",
            'bank': f"1120 - Bank Account",
            'ar': f"1130 - Accounts Receivable",
            'inventory': f"1140 - Inventory",
            'equipment': f"1210 - Equipment",
            'furniture': f"1220 - Furniture and Fixtures",
            'ap': f"2110 - Accounts Payable",
            'loans': f"2210 - Bank Loans",
            'capital': f"3110 - Share Capital",
            'retained': f"3120 - Retained Earnings",
            'sales': f"4110 - Sales Revenue",
            'service': f"4120 - Service Revenue",
            'interest': f"4210 - Interest Income",
            'cogs': f"5110 - Cost of Goods Sold",
            'salary': f"5210 - Salary Expense",
            'rent': f"5220 - Rent Expense",
            'utilities': f"5230 - Utilities Expense",
            'insurance': f"5240 - Insurance Expense",
            'marketing': f"5250 - Marketing Expense",
            'office': f"5260 - Office Supplies",
            'depreciation': f"5270 - Depreciation",
            'maintenance': f"5280 - Maintenance and Repairs",
            'bank_fees': f"5310 - Bank Charges",
            'misc': f"5320 - Miscellaneous Expenses"
        }

    def generate_startup_entries(self, start_date):
        """Generate initial entries for business incorporation and setup."""
        entries = []
        
        # Initial capital investment
        entries.append({
            'date': start_date,
            'description': f'Initial capital investment - {self.company_name} incorporation',
            'debit_account': self.accounts['bank'],
            'credit_account': self.accounts['capital'],
            'amount': self.initial_investment
        })
        
        # Purchase of initial equipment
        equipment_cost = 75000
        entries.append({
            'date': start_date,
            'description': 'Purchase of initial office equipment and computers',
            'debit_account': self.accounts['equipment'],
            'credit_account': self.accounts['bank'],
            'amount': equipment_cost
        })
        
        # Purchase of furniture
        furniture_cost = 25000
        entries.append({
            'date': start_date,
            'description': 'Purchase of office furniture and fixtures',
            'debit_account': self.accounts['furniture'],
            'credit_account': self.accounts['bank'],
            'amount': furniture_cost
        })
        
        # Initial inventory purchase
        inventory_cost = 100000
        entries.append({
            'date': start_date,
            'description': 'Initial inventory purchase',
            'debit_account': self.accounts['inventory'],
            'credit_account': self.accounts['ap'],
            'amount': inventory_cost
        })
        
        # Rent deposit and first month
        rent_deposit = self.monthly_rent * 2
        entries.append({
            'date': start_date,
            'description': 'Office lease deposit and first month rent',
            'debit_account': self.accounts['rent'],
            'credit_account': self.accounts['bank'],
            'amount': rent_deposit
        })
        
        return entries

    def generate_daily_entries(self, date):
        """Generate realistic daily business transactions."""
        entries = []
        
        # Sales transactions (multiple per day)
        num_sales = random.randint(30, 70)
        for _ in range(num_sales):
            unit_cost = random.uniform(self.product_cost_range[0], self.product_cost_range[1])
            quantity = random.randint(1, 10)
            sale_amount = unit_cost * self.selling_price_multiplier * quantity
            cost_amount = unit_cost * quantity
            
            # 70% chance of cash sale, 30% credit
            if random.random() < 0.7:
                payment_account = self.accounts['cash']
            else:
                payment_account = self.accounts['ar']
            
            entries.append({
                'date': date,
                'description': f'Product sale - Invoice #{random.randint(10000, 99999)}',
                'debit_account': payment_account,
                'credit_account': self.accounts['sales'],
                'amount': round(sale_amount, 2)
            })
            
            entries.append({
                'date': date,
                'description': f'Cost of goods sold entry',
                'debit_account': self.accounts['cogs'],
                'credit_account': self.accounts['inventory'],
                'amount': round(cost_amount, 2)
            })
        
        # Daily operating expenses (random selection)
        if random.random() < 0.3:  # 30% chance of office supplies purchase
            amount = random.uniform(100, 500)
            entries.append({
                'date': date,
                'description': 'Office supplies purchase',
                'debit_account': self.accounts['office'],
                'credit_account': self.accounts['cash'],
                'amount': round(amount, 2)
            })
        
        if random.random() < 0.2:  # 20% chance of maintenance expense
            amount = random.uniform(200, 1000)
            entries.append({
                'date': date,
                'description': 'Equipment maintenance and repairs',
                'debit_account': self.accounts['maintenance'],
                'credit_account': self.accounts['cash'],
                'amount': round(amount, 2)
            })
            
        # Bank transfers (cash to bank)
        if random.random() < 0.8:  # 80% chance of daily bank deposit
            amount = random.uniform(5000, 15000)
            entries.append({
                'date': date,
                'description': 'Daily cash deposit to bank',
                'debit_account': self.accounts['bank'],
                'credit_account': self.accounts['cash'],
                'amount': round(amount, 2)
            })
            
        return entries

    def generate_monthly_entries(self, date):
        """Generate monthly recurring transactions."""
        entries = []
        
        # Rent payment
        entries.append({
            'date': date,
            'description': 'Monthly office rent payment',
            'debit_account': self.accounts['rent'],
            'credit_account': self.accounts['bank'],
            'amount': self.monthly_rent
        })
        
        # Salary payments
        total_salary = self.average_salary * self.employee_count
        entries.append({
            'date': date,
            'description': 'Monthly salary payments',
            'debit_account': self.accounts['salary'],
            'credit_account': self.accounts['bank'],
            'amount': total_salary
        })
        
        # Utility payments
        utility_amount = random.uniform(1500, 2500)
        entries.append({
            'date': date,
            'description': 'Monthly utilities payment',
            'debit_account': self.accounts['utilities'],
            'credit_account': self.accounts['bank'],
            'amount': round(utility_amount, 2)
        })
        
        # Insurance payment
        insurance_amount = 2000
        entries.append({
            'date': date,
            'description': 'Monthly insurance premium',
            'debit_account': self.accounts['insurance'],
            'credit_account': self.accounts['bank'],
            'amount': insurance_amount
        })
        
        # Marketing expenses
        marketing_amount = random.uniform(5000, 15000)
        entries.append({
            'date': date,
            'description': 'Monthly marketing expenses',
            'debit_account': self.accounts['marketing'],
            'credit_account': self.accounts['bank'],
            'amount': round(marketing_amount, 2)
        })
        
        return entries

    def generate_entries(self, start_date, end_date):
        """Generate all entries between start and end date."""
        entries = []
        
        # Add startup entries
        entries.extend(self.generate_startup_entries(start_date))
          # Generate daily and monthly entries
        days_total = (end_date - start_date).days + 1
        current_date = start_date
        
        with tqdm(total=days_total, desc="Generating entries") as pbar:
            while current_date <= end_date:
                # Daily entries
                entries.extend(self.generate_daily_entries(current_date))
                
                # Monthly entries on 1st of each month
                if current_date.day == 1:
                    entries.extend(self.generate_monthly_entries(current_date))
                
                current_date += timedelta(days=1)
                pbar.update(1)
        
        return entries

def main():
    try:
        # Initialize accounting system
        system = AccountingSystem()
        
        # Create generator
        generator = BusinessTransactionGenerator(system)
        
        # Generate entries for past two years
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        print(f"Generating entries from {start_date} to {end_date}...")
        entries = generator.generate_entries(start_date, end_date)        # Add entries to system in batches
        print(f"\nAdding {len(entries)} entries to the database...")
        
        # Convert dates to strings and prepare entries for batch insert
        prepared_entries = []
        for entry in entries:
            prepared_entries.append({
                'date': entry['date'].strftime('%Y-%m-%d'),
                'description': entry['description'],
                'debit_account': entry['debit_account'],
                'credit_account': entry['credit_account'],
                'amount': entry['amount']
            })
        
        # Process in batches of 1000
        batch_size = 1000
        with tqdm(total=len(prepared_entries), desc="Saving entries") as pbar:
            for i in range(0, len(prepared_entries), batch_size):
                batch = prepared_entries[i:i + batch_size]
                system.add_journal_entries_batch(batch)
                pbar.update(len(batch))
        
        print(f"Successfully generated {len(entries)} journal entries.")
        
    except Exception as e:
        print(f"Error generating entries: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
