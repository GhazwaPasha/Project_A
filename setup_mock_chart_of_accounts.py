"""
Mock Chart of Accounts Setup Script
Adds comprehensive mock chart of accounts to an existing organization
for user: ghazwairshad@gmail.com
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from src.core.supabase_manager import SupabaseManager
from src.core.auth_manager import AuthManager
from src.core.accounting_system import AccountingSystem

def get_comprehensive_chart_of_accounts():
    """Return the specific chart of accounts for the business."""
    return [
        # ASSETS (1000-1999)
{'code': '1000', 'name': 'Assets', 'type': 'asset', 'is_postable': False, 'parent_code': None},
{'code': '1100', 'name': 'Cash & Cash Equivalents', 'type': 'asset', 'is_postable': False, 'parent_code': '1000'},
{'code': '1110', 'name': 'Cash in Hand', 'type': 'asset', 'is_postable': True, 'parent_code': '1100'},
{'code': '1120', 'name': 'Cash at Bank', 'type': 'asset', 'is_postable': True, 'parent_code': '1100'},
{'code': '1130', 'name': 'Cash at POS', 'type': 'asset', 'is_postable': True, 'parent_code': '1100'},
{'code': '1200', 'name': 'Inventory', 'type': 'asset', 'is_postable': False, 'parent_code': '1000'},
{'code': '1210', 'name': 'Beverages', 'type': 'asset', 'is_postable': True, 'parent_code': '1200'},
{'code': '1220', 'name': 'Dairy', 'type': 'asset', 'is_postable': True, 'parent_code': '1200'},
{'code': '1230', 'name': 'Dry Goods', 'type': 'asset', 'is_postable': True, 'parent_code': '1200'},
{'code': '1240', 'name': 'Meat', 'type': 'asset', 'is_postable': True, 'parent_code': '1200'},
{'code': '1250', 'name': 'Vegetables', 'type': 'asset', 'is_postable': True, 'parent_code': '1200'},
        {'code': '1300', 'name': 'Accounts Receivable', 'type': 'asset', 'is_postable': False, 'parent_code': '1000'},
        {'code': '1310', 'name': 'AR - Ghazwa Irshad', 'type': 'asset', 'is_postable': True, 'parent_code': '1300'},
        {'code': '1320', 'name': 'AR - Ausairum Mehmood', 'type': 'asset', 'is_postable': True, 'parent_code': '1300'},
        {'code': '1330', 'name': 'AR - Zain Zahid', 'type': 'asset', 'is_postable': True, 'parent_code': '1300'},
        {'code': '1400', 'name': 'Fixed Assets', 'type': 'asset', 'is_postable': False, 'parent_code': '1000'},
        {'code': '1410', 'name': 'Buildings', 'type': 'asset', 'is_postable': True, 'parent_code': '1400'},
        {'code': '1420', 'name': 'Furniture & Fixtures', 'type': 'asset', 'is_postable': True, 'parent_code': '1400'},
        {'code': '1430', 'name': 'Equipment', 'type': 'asset', 'is_postable': True, 'parent_code': '1400'},
        {'code': '1440', 'name': 'Vehicles', 'type': 'asset', 'is_postable': True, 'parent_code': '1400'},
        {'code': '1500', 'name': 'Investments', 'type': 'asset', 'is_postable': True, 'parent_code': '1000'},
        
        # LIABILITIES (2000-2999)
        {'code': '2000', 'name': 'Liabilities', 'type': 'liability', 'is_postable': False, 'parent_code': None},
        {'code': '2100', 'name': 'Accounts Payable', 'type': 'liability', 'is_postable': False, 'parent_code': '2000'},
        {'code': '2110', 'name': 'Coca Cola', 'type': 'liability', 'is_postable': True, 'parent_code': '2100'},
        {'code': '2120', 'name': 'Dawn', 'type': 'liability', 'is_postable': True, 'parent_code': '2100'},
        {'code': '2130', 'name': 'RH Chicken', 'type': 'liability', 'is_postable': True, 'parent_code': '2100'},
        {'code': '2140', 'name': 'Horica Store', 'type': 'liability', 'is_postable': True, 'parent_code': '2100'},
        {'code': '2150', 'name': 'Adnan Traders', 'type': 'liability', 'is_postable': True, 'parent_code': '2100'},
        
        # EQUITY (3000-3999)
        {'code': '3000', 'name': 'Equity', 'type': 'equity', 'is_postable': False, 'parent_code': None},
        {'code': '3100', 'name': 'Owner\'s Capital', 'type': 'equity', 'is_postable': True, 'parent_code': '3000'},
        {'code': '3200', 'name': 'Drawings', 'type': 'equity', 'is_postable': False, 'parent_code': '3000'},
        {'code': '3210', 'name': 'Dr - Ghazwa Irshad', 'type': 'equity', 'is_postable': True, 'parent_code': '3200'},
        {'code': '3220', 'name': 'Dr - Ausairum Mehmood', 'type': 'equity', 'is_postable': True, 'parent_code': '3200'},
        {'code': '3230', 'name': 'Dr - Zain Zahid', 'type': 'equity', 'is_postable': True, 'parent_code': '3200'},
        {'code': '3300', 'name': 'Retained Earnings', 'type': 'equity', 'is_postable': True, 'parent_code': '3000'},
        
        # REVENUES (4000-4999)
        {'code': '4000', 'name': 'Revenues', 'type': 'revenue', 'is_postable': False, 'parent_code': None},
        {'code': '4100', 'name': 'Sales', 'type': 'revenue', 'is_postable': False, 'parent_code': '4000'},
        {'code': '4110', 'name': 'Cash Sales', 'type': 'revenue', 'is_postable': True, 'parent_code': '4100'},
        {'code': '4120', 'name': 'Credit Sales', 'type': 'revenue', 'is_postable': True, 'parent_code': '4100'},
        {'code': '4130', 'name': 'Card Sales', 'type': 'revenue', 'is_postable': True, 'parent_code': '4100'},
        {'code': '4140', 'name': 'Food Panda', 'type': 'revenue', 'is_postable': True, 'parent_code': '4100'},
        {'code': '4150', 'name': 'Dastak', 'type': 'revenue', 'is_postable': True, 'parent_code': '4100'},
        {'code': '4200', 'name': 'Other Income', 'type': 'revenue', 'is_postable': True, 'parent_code': '4000'},
        
        # EXPENSES (5000-5999)
        {'code': '5000', 'name': 'Expenses', 'type': 'expense', 'is_postable': False, 'parent_code': None},
        {'code': '5100', 'name': 'Cost of Goods Sold', 'type': 'expense', 'is_postable': False, 'parent_code': '5000'},
        {'code': '5110', 'name': 'COGS - Beverages', 'type': 'expense', 'is_postable': True, 'parent_code': '5100'},
        {'code': '5120', 'name': 'COGS - Dairy', 'type': 'expense', 'is_postable': True, 'parent_code': '5100'},
        {'code': '5130', 'name': 'COGS - Dry Goods', 'type': 'expense', 'is_postable': True, 'parent_code': '5100'},
        {'code': '5140', 'name': 'COGS - Meat', 'type': 'expense', 'is_postable': True, 'parent_code': '5100'},
        {'code': '5150', 'name': 'COGS - Vegetables', 'type': 'expense', 'is_postable': True, 'parent_code': '5100'},
        {'code': '5200', 'name': 'Operating Expenses', 'type': 'expense', 'is_postable': False, 'parent_code': '5000'},
        {'code': '5210', 'name': 'Utilities', 'type': 'expense', 'is_postable': True, 'parent_code': '5200'},
        {'code': '5220', 'name': 'Rent', 'type': 'expense', 'is_postable': True, 'parent_code': '5200'},
        {'code': '5230', 'name': 'Marketing', 'type': 'expense', 'is_postable': True, 'parent_code': '5200'},
        {'code': '5240', 'name': 'Salaries & Wages', 'type': 'expense', 'is_postable': True, 'parent_code': '5200'},
        {'code': '5250', 'name': 'Software & IT', 'type': 'expense', 'is_postable': True, 'parent_code': '5200'},
        {'code': '5300', 'name': 'Other Expenses', 'type': 'expense', 'is_postable': False, 'parent_code': '5000'},
        {'code': '5310', 'name': 'Charity', 'type': 'expense', 'is_postable': True, 'parent_code': '5300'},
        {'code': '5320', 'name': 'Travel & Tours', 'type': 'expense', 'is_postable': True, 'parent_code': '5300'},
        {'code': '5330', 'name': 'Miscellaneous', 'type': 'expense', 'is_postable': True, 'parent_code': '5300'},
    ]

def setup_chart_of_accounts_for_user(user_email: str, org_id: str = None):
    """Setup chart of accounts for the specified user's organization."""
    print(f"🎯 Setting up mock chart of accounts for user: {user_email}")
    
    try:
        # Use the known organization ID from the startup log
        if not org_id:
            org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"  # From the startup log
            
        org_name = "ghazwa irshad's Workspace"  # From the startup log
        print(f"✅ Using organization: {org_name} (ID: {org_id})")
        
        # Initialize auth manager and authenticate
        auth_manager = AuthManager()
        
        # Create a fake authenticated session to bypass RLS
        # This simulates being logged in as the user
        print(f"🔑 Authenticating as {user_email}...")
        
        # Get user ID by email (direct query)
        db_manager = SupabaseManager()
        user_result = db_manager.supabase.table('user_profiles')\
            .select('id')\
            .eq('email', user_email)\
            .execute()
            
        if not user_result.data:
            print(f"❌ User not found: {user_email}")
            return False
            
        user_id = user_result.data[0]['id']
        print(f"✅ Found user ID: {user_id}")
        
        # Initialize accounting system with proper auth context
        accounting_system = AccountingSystem(auth_manager)
        
        # Manually set the organization context
        accounting_system.current_organization_id = org_id
        
        # Get the comprehensive chart of accounts
        accounts_data = get_comprehensive_chart_of_accounts()
        
        print(f"📊 Creating {len(accounts_data)} accounts...")
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        # Create a lookup for faster parent finding
        accounts_by_code = {}
        
        # First pass: Create accounts without parent references (level 1)
        # Second pass: Create accounts with parent references (level 2 & 3)
        for pass_num in [1, 2, 3]:
            print(f"\n📋 Pass {pass_num}: Creating level {pass_num} accounts...")
            
            for account_data in accounts_data:
                try:
                    parent_code = account_data.get('parent_code')
                    current_level = 1 if not parent_code else (2 if parent_code in ['1000', '2000', '3000', '4000', '5000'] else 3)
                    
                    if current_level != pass_num:
                        continue
                    
                    # Check if account already exists
                    existing_accounts = accounting_system.get_chart_of_accounts()
                    if any(acc['code'] == account_data['code'] for acc in existing_accounts):
                        print(f"⏭️  Account {account_data['code']} already exists, skipping...")
                        skipped_count += 1
                        continue
                    
                    # Find parent_id if parent_code exists
                    parent_id = None
                    if parent_code and parent_code in accounts_by_code:
                        parent_id = accounts_by_code[parent_code]
                    elif parent_code:
                        print(f"⚠️  Parent account {parent_code} not found for {account_data['code']}, skipping for now...")
                        continue
                    
                    # Create the account using accounting system
                    try:
                        account = accounting_system.create_account(
                            code=account_data['code'],
                            name=account_data['name'],
                            account_type=account_data['type'],
                            parent_id=parent_id,
                            description=f"Auto-created account for {account_data['name']}"
                        )
                        
                        if account:
                            level_indicator = "📁" if not account_data.get('is_postable', True) else "📄"
                            print(f"✅ {level_indicator} Created: {account_data['code']} - {account_data['name']}")
                            created_count += 1
                            
                            # Store in lookup for future parent references
                            accounts_by_code[account_data['code']] = account['id']
                        else:
                            print(f"❌ Failed to create: {account_data['code']} - {account_data['name']}")
                            error_count += 1
                            
                    except Exception as create_error:
                        if "duplicate" in str(create_error).lower() or "already exists" in str(create_error).lower() or "unique" in str(create_error).lower():
                            print(f"⏭️  Skipped: {account_data['code']} - {account_data['name']} (already exists)")
                            skipped_count += 1
                        else:
                            print(f"❌ Error creating account {account_data['code']}: {create_error}")
                            error_count += 1
                            
                except Exception as e:
                    print(f"❌ Error processing account {account_data['code']}: {e}")
                    error_count += 1
        
        print(f"\n📈 Summary:")
        print(f"   ✅ Created: {created_count} accounts")
        print(f"   ⏭️  Skipped: {skipped_count} accounts (already existed)")
        print(f"   ❌ Errors: {error_count} accounts")
        print(f"   📊 Total: {len(accounts_data)} accounts processed")
        
        if created_count > 0:
            print(f"\n🎉 Successfully added {created_count} accounts to {org_name}!")
            return True
        else:
            print(f"\n⚠️  No new accounts were created.")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up chart of accounts: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    print("🚀 Mock Chart of Accounts Setup")
    print("=" * 50)
    
    # Target user email and org ID from startup log
    target_email = "ghazwairshad@gmail.com"
    target_org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"
    
    print(f"Target user: {target_email}")
    print(f"Target organization: ghazwa irshad's Workspace ({target_org_id})")
    print("-" * 50)
    
    success = setup_chart_of_accounts_for_user(target_email, target_org_id)
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Chart of accounts setup completed successfully!")
        print("\nYou can now:")
        print("- View accounts in the Chart of Accounts page")
        print("- Create journal entries using these accounts")
        print("- Generate financial reports")
    else:
        print("❌ Chart of accounts setup failed!")
        print("\nPlease check:")
        print("- User exists and is logged in at least once")
        print("- User has an organization")
        print("- Database connection is working")

if __name__ == "__main__":
    main()
