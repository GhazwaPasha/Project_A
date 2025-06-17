#!/usr/bin/env python3
"""
Utility script to clear all journal entries from the accounting system.
Use with caution as this operation cannot be undone!
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.accounting_system import AccountingSystem

def main():
    try:
        # Get the database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'accounting.db')
        
        # Initialize the accounting system
        system = AccountingSystem(db_path)
        
        # Clear all entries
        entries_deleted = system.clear_journal_entries()
        
        print(f"Successfully deleted {entries_deleted} journal entries from the system.")
        
    except Exception as e:
        print(f"Error clearing journal entries: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    response = input("WARNING: This will delete ALL journal entries. This cannot be undone!\nAre you sure you want to continue? (yes/no): ")
    if response.lower() == 'yes':
        main()
    else:
        print("Operation cancelled.")
