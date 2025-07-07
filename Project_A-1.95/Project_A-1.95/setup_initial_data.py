"""
Initial Setup Script for New Schema
Sets up initial data after applying NEW_SCHEMA.sql
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.supabase_manager import SupabaseManager
from src.core.auth_manager import AuthManager
from src.core.accounting_system import AccountingSystem

def create_initial_super_admin(email: str, password: str, full_name: str):
    """Create the first super admin user."""
    print(f"Creating super admin user: {email}")
    
    auth_manager = AuthManager()
    
    # Sign up the user
    result = auth_manager.sign_up(email, password, full_name)
    
    if result['success']:
        user_id = result['user'].id
        print(f"User created with ID: {user_id}")
        
        # Make them super admin
        db_manager = SupabaseManager(user_id)
        success = db_manager.update_user_profile(user_id, {'is_super_admin': True})
        
        if success:
            print("✅ Super admin created successfully!")
            return user_id
        else:
            print("❌ Failed to set super admin flag")
            return None
    else:
        print(f"❌ Failed to create user: {result.get('error', 'Unknown error')}")
        return None

def create_initial_organization(name: str, description: str, owner_user_id: str):
    """Create the first organization."""
    print(f"Creating organization: {name}")
    
    db_manager = SupabaseManager(owner_user_id)
    
    # Create organization
    org_data = {
        'name': name,
        'description': description,
        'settings': {}
    }
    
    org = db_manager.create_organization(org_data)
    
    if org:
        org_id = org['id']
        print(f"Organization created with ID: {org_id}")
        
        # Add the user as organization owner
        success = db_manager.add_organization_member(
            org_id=org_id,
            user_id=owner_user_id,
            role='organization_owner'
        )
        
        if success:
            print("✅ Organization and membership created successfully!")
            return org_id
        else:
            print("❌ Failed to add user as organization owner")
            return None
    else:
        print("❌ Failed to create organization")
        return None

def create_sample_chart_of_accounts(org_id: str, user_id: str):
    """Create a basic chart of accounts."""
    print("Creating sample chart of accounts...")
    
    # Initialize the accounting system
    auth_manager = AuthManager()
    auth_manager.current_user = type('User', (), {'id': user_id})()
    auth_manager.db_manager = SupabaseManager(user_id)
    
    accounting_system = AccountingSystem(auth_manager)
    accounting_system.set_organization(org_id)
    
    # Basic chart of accounts
    accounts = [
        # Assets
        {'code': '1000', 'name': 'Cash', 'type': 'asset'},
        {'code': '1100', 'name': 'Accounts Receivable', 'type': 'asset'},
        {'code': '1200', 'name': 'Inventory', 'type': 'asset'},
        {'code': '1500', 'name': 'Equipment', 'type': 'asset'},
        
        # Liabilities
        {'code': '2000', 'name': 'Accounts Payable', 'type': 'liability'},
        {'code': '2100', 'name': 'Notes Payable', 'type': 'liability'},
        
        # Equity
        {'code': '3000', 'name': 'Owner\'s Equity', 'type': 'equity'},
        {'code': '3100', 'name': 'Retained Earnings', 'type': 'equity'},
        
        # Revenue
        {'code': '4000', 'name': 'Sales Revenue', 'type': 'revenue'},
        {'code': '4100', 'name': 'Service Revenue', 'type': 'revenue'},
        
        # Expenses
        {'code': '5000', 'name': 'Cost of Goods Sold', 'type': 'expense'},
        {'code': '6000', 'name': 'Operating Expenses', 'type': 'expense'},
        {'code': '6100', 'name': 'Rent Expense', 'type': 'expense'},
        {'code': '6200', 'name': 'Utilities Expense', 'type': 'expense'},
    ]
    
    created_count = 0
    for account_data in accounts:
        try:
            account = accounting_system.create_account(
                code=account_data['code'],
                name=account_data['name'],
                account_type=account_data['type']
            )
            if account:
                created_count += 1
        except Exception as e:
            print(f"Failed to create account {account_data['code']}: {e}")
    
    print(f"✅ Created {created_count} accounts successfully!")

def main():
    print("🚀 Setting up initial data for new schema...")
    print("=" * 50)
    
    # Get user input
    email = input("Super admin email: ").strip()
    password = input("Super admin password: ").strip()
    full_name = input("Super admin full name: ").strip()
    org_name = input("Organization name: ").strip()
    org_description = input("Organization description: ").strip()
    
    if not all([email, password, full_name, org_name]):
        print("❌ All fields are required!")
        return
    
    print("\n" + "=" * 50)
    
    # Step 1: Create super admin
    user_id = create_initial_super_admin(email, password, full_name)
    if not user_id:
        print("❌ Failed to create super admin. Exiting.")
        return
    
    print()
    
    # Step 2: Create organization
    org_id = create_initial_organization(org_name, org_description, user_id)
    if not org_id:
        print("❌ Failed to create organization. Exiting.")
        return
    
    print()
    
    # Step 3: Create sample chart of accounts
    create_sample_chart_of_accounts(org_id, user_id)
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print(f"Super admin: {email}")
    print(f"Organization: {org_name} ({org_id})")
    print("\nYou can now sign in to the application.")

if __name__ == "__main__":
    main()
