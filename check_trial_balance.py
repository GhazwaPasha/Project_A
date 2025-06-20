#!/usr/bin/env python3
"""
Script to check the trial balance structure
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
        
        # Check trial balance structure
        print('\n=== Trial Balance Structure ===')
        trial_balance = system.get_trial_balance()
        
        if trial_balance:
            print(f'Number of trial balance items: {len(trial_balance)}')
            print('\nFirst item structure:')
            first_item = trial_balance[0]
            print(f'Type: {type(first_item)}')
            print(f'Keys: {list(first_item.keys()) if hasattr(first_item, "keys") else "No keys method"}')
            print(f'Content: {first_item}')
            
            print('\nFirst 3 items:')
            for i, item in enumerate(trial_balance[:3]):
                print(f'  {i+1}. {item}')
        else:
            print('No trial balance data found')
        
    except Exception as e:
        print(f'\n❌ Error: {e}')
        logging.error(f"Error checking trial balance: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
