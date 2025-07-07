"""
Simple Chart of Accounts Setup Script
Creates accounts directly using service role key to bypass RLS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from supabase import create_client

# Use service role key to bypass RLS
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Need service role key

if not SUPABASE_SERVICE_KEY:
    print("❌ SUPABASE_SERVICE_ROLE_KEY not found in environment variables!")
    print("This script requires service role key to bypass Row Level Security.")
    print("Please add SUPABASE_SERVICE_ROLE_KEY to your .env file.")
    sys.exit(1)

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

def setup_accounts():
    """Setup chart of accounts using service role key"""
    print("🚀 Setting up Chart of Accounts with Service Role")
    print("=" * 50)
    
    # Organization ID from startup log
    org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"
    
    # Initialize Supabase with service role key
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    accounts_data = get_comprehensive_chart_of_accounts()
    
    print(f"📊 Creating {len(accounts_data)} accounts...")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    # Store account IDs for parent references
    account_ids = {}
    
    # Create accounts in 3 passes to handle hierarchy
    for pass_num in [1, 2, 3]:
        print(f"\n📋 Pass {pass_num}: Creating level {pass_num} accounts...")
        
        for account_data in accounts_data:
            try:
                parent_code = account_data.get('parent_code')
                current_level = 1 if not parent_code else (2 if parent_code in ['1000', '2000', '3000', '4000', '5000'] else 3)
                
                if current_level != pass_num:
                    continue
                
                # Check if account already exists
                existing = supabase.table('accounts')\
                    .select('id')\
                    .eq('organization_id', org_id)\
                    .eq('code', account_data['code'])\
                    .execute()
                    
                if existing.data:
                    print(f"⏭️  Account {account_data['code']} already exists, skipping...")
                    skipped_count += 1
                    # Store ID for potential parent references
                    account_ids[account_data['code']] = existing.data[0]['id']
                    continue
                
                # Find parent_id if parent_code exists
                parent_id = None
                if parent_code and parent_code in account_ids:
                    parent_id = account_ids[parent_code]
                elif parent_code:
                    print(f"⚠️  Parent account {parent_code} not found for {account_data['code']}, skipping...")
                    continue
                
                # Create account record
                account_record = {
                    'organization_id': org_id,
                    'code': account_data['code'],
                    'name': account_data['name'],
                    'account_type': account_data['type'],
                    'parent_id': parent_id,
                    'is_active': True,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Insert account
                result = supabase.table('accounts')\
                    .insert(account_record)\
                    .execute()
                
                if result.data:
                    level_indicator = "📁" if not account_data.get('is_postable', True) else "📄"
                    print(f"✅ {level_indicator} Created: {account_data['code']} - {account_data['name']}")
                    created_count += 1
                    
                    # Store ID for future parent references
                    account_ids[account_data['code']] = result.data[0]['id']
                else:
                    print(f"❌ Failed to create: {account_data['code']} - {account_data['name']}")
                    error_count += 1
                    
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    print(f"⏭️  Skipped: {account_data['code']} - {account_data['name']} (already exists)")
                    skipped_count += 1
                else:
                    print(f"❌ Error creating account {account_data['code']}: {e}")
                    error_count += 1
    
    print(f"\n📈 Summary:")
    print(f"   ✅ Created: {created_count} accounts")
    print(f"   ⏭️  Skipped: {skipped_count} accounts (already existed)")
    print(f"   ❌ Errors: {error_count} accounts")
    print(f"   📊 Total: {len(accounts_data)} accounts processed")
    
    print("\n" + "=" * 50)
    if created_count > 0:
        print("🎉 Chart of accounts setup completed successfully!")
        print("\nYou can now:")
        print("- View accounts in the Chart of Accounts page")
        print("- Create journal entries using these accounts")
        print("- Generate financial reports")
    else:
        print("⚠️  No new accounts were created.")

if __name__ == "__main__":
    setup_accounts()
