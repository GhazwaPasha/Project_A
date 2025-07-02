#!/usr/bin/env python3
"""
Diagnostic script to debug journal entry saving issues
Run this after authenticating to see what's happening
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_journal_entry_system():
    """Check the journal entry system status"""
    print("🔍 JOURNAL ENTRY DIAGNOSTIC TOOL")
    print("=" * 50)
    
    try:
        from src.core.auth_manager import AuthManager
        from src.core.unified_accounting_system import UnifiedAccountingSystem
        
        # Initialize system (you need to be authenticated first)
        print("🔐 Initializing authentication...")
        auth_manager = AuthManager()
        
        # Check if user is authenticated
        current_user = auth_manager.get_current_user()
        if not current_user:
            print("❌ No authenticated user found. Please run the main app and login first.")
            return
            
        print(f"✅ Authenticated as: {current_user.get('email', 'Unknown')}")
        
        # Get organizations
        organizations = auth_manager.get_user_organizations()
        if not organizations:
            print("❌ No organizations found for user")
            return
            
        print(f"✅ Found {len(organizations)} organization(s)")
        
        # Initialize accounting system
        system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization context (use first org)
        org = organizations[0]
        org_id = org.get('id')
        system.set_organization(org_id)
        print(f"✅ Using organization: {org.get('name', 'Unknown')} (ID: {org_id})")
        
        # Check connectivity
        print("\n🌐 CONNECTIVITY CHECK")
        print("-" * 30)
        online_status = system.is_online
        print(f"Online status: {'✅ Online' if online_status else '📱 Offline'}")
        
        # Check accounts
        print("\n📋 ACCOUNTS CHECK")
        print("-" * 30)
        try:
            accounts = system.get_chart_of_accounts(active_only=False)
            print(f"Total accounts found: {len(accounts)}")
            
            if accounts:
                print("\nFirst 10 accounts:")
                for i, account in enumerate(accounts[:10]):
                    print(f"  {i+1:2d}. ID: {account.get('id', 'N/A'):4s} | Name: {account.get('name', 'N/A')}")
                
                # Check for common account names
                print("\n🔍 Checking for common account names:")
                test_accounts = ['Cash', 'Sales Revenue', 'Sales', 'Revenue', 'Cash on Hand', 'Sales Income']
                for test_name in test_accounts:
                    account_id = system._resolve_account_name_to_id(test_name)
                    status = f"✅ Found (ID: {account_id})" if account_id else "❌ Not found"
                    print(f"  '{test_name}': {status}")
            else:
                print("❌ No accounts found! You need to set up your chart of accounts first.")
                
        except Exception as e:
            print(f"❌ Error retrieving accounts: {e}")
        
        # Test journal entry transformation
        print("\n🔄 JOURNAL ENTRY TRANSFORMATION TEST")
        print("-" * 40)
        
        test_entry = {
            'date': '2024-01-15',
            'description': 'Test Cash Sale',
            'debit_account': 'Cash',
            'credit_account': 'Sales Revenue',
            'amount': '150.00'
        }
        
        print(f"Test entry data: {test_entry}")
        
        try:
            print("Attempting data transformation...")
            journal_data, journal_lines = system._transform_journal_entry_data(test_entry)
            print("✅ Transformation successful!")
            print(f"Entry number: {journal_data.get('entry_number')}")
            print(f"Lines created: {len(journal_lines)}")
        except Exception as e:
            print(f"❌ Transformation failed: {e}")
            print("This is likely why your journal entries aren't being saved.")
        
        # Check permissions
        print("\n🔒 PERMISSIONS CHECK")
        print("-" * 30)
        try:
            can_create = auth_manager.can_create_journal_entries(org_id)
            print(f"Can create journal entries: {'✅ Yes' if can_create else '❌ No'}")
        except Exception as e:
            print(f"❌ Error checking permissions: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 DIAGNOSIS COMPLETE")
        
        if not accounts:
            print("\n💡 RECOMMENDED ACTIONS:")
            print("1. Set up your chart of accounts first")
            print("2. Make sure you have 'Cash' and 'Sales Revenue' accounts")
            print("3. Try running the account setup scripts")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the project directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    check_journal_entry_system() 