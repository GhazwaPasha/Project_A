#!/usr/bin/env python3
"""
Export journal entries to CSV with simplified account names (without codes).
Columns: Date, Description, Debit Account, Credit Account, Amount
"""

import os
import sys
import csv
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.accounting_system import AccountingSystem

def strip_account_code(account_name):
    """Remove the account code from the account name format 'CODE - Name'"""
    if ' - ' in account_name:
        return account_name.split(' - ', 1)[1]
    return account_name

def export_to_csv(output_file='journal_entries.csv'):
    """Export journal entries to CSV with simplified format."""
    try:
        # Initialize accounting system
        system = AccountingSystem()
        
        # Get all entries ordered by date
        cursor = system.conn.cursor()
        cursor.execute('''
            SELECT 
                date,
                description,
                debit_account,
                credit_account,
                amount
            FROM journal_entries 
            ORDER BY date, timestamp
        ''')
        
        entries = cursor.fetchall()
        print(f"Exporting {len(entries)} entries to {output_file}...")
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Date',
                'Description',
                'Debit Account',
                'Credit Account',
                'Amount'
            ])
            
            # Write entries
            for entry in entries:
                date, description, debit_account, credit_account, amount = entry
                
                # Remove codes from account names
                debit_account_name = strip_account_code(debit_account)
                credit_account_name = strip_account_code(credit_account)
                
                writer.writerow([
                    date,
                    description,
                    debit_account_name,
                    credit_account_name,
                    f"{amount:.2f}"
                ])
        
        print(f"Successfully exported to {output_file}")
        
        # Print some basic statistics
        print("\nBasic Statistics:")
        print(f"Total number of entries: {len(entries):,}")
        
        # Calculate total debits
        total_amount = sum(entry[4] for entry in entries)
        print(f"Total transaction value: ${total_amount:,.2f}")
        
        # Date range
        if entries:
            first_date = entries[0][0]
            last_date = entries[-1][0]
            print(f"Date range: {first_date} to {last_date}")
        
    except Exception as e:
        print(f"Error exporting entries: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Get output filename from command line if provided
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'journal_entries.csv'
    export_to_csv(output_file)
