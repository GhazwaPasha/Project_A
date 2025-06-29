#!/usr/bin/env python3
"""
Debug script to test parent account suggestions
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.unified_accounting_system import UnifiedAccountingSystem
from src.core.auth_manager import AuthManager

def test_parent_suggestions():
    """Test the parent account suggestions logic."""
    try:
        # Initialize system
        auth_manager = AuthManager()
        system = UnifiedAccountingSystem(auth_manager)
        
        print("=== Testing Parent Account Suggestions ===")
        print(f"System organization ID: {getattr(system, 'current_organization_id', 'None')}")
        
        # Get all accounts
        all_accounts = system.get_chart_of_accounts(active_only=False)
        print(f"Total accounts found: {len(all_accounts)}")
        
        if not all_accounts:
            print("❌ No accounts found - this explains why suggestions are empty!")
            print("Need to either:")
            print("1. Set proper organization context")
            print("2. Create test accounts")
            print("3. Check if user is logged in")
            return
        
        # Show first few accounts
        print("\nFirst 5 accounts:")
        for i, account in enumerate(all_accounts[:5]):
            if isinstance(account, dict):
                print(f"  {i+1}. {account.get('code', 'No code')} - {account.get('name', 'No name')}")
                print(f"      Type: {account.get('account_type', 'No type')}")
                print(f"      Level: {account.get('level', 'No level')}")
                print(f"      Parent ID: {account.get('parent_id', 'None')}")
            else:
                print(f"  {i+1}. {account}")
            print()
        
        # Test filter logic for Level 2 Asset accounts
        current_type = "asset"
        level = 2
        
        print(f"\n=== Testing filter for Level {level} {current_type} accounts ===")
        eligible_parents = []
        
        for account in all_accounts:
            if isinstance(account, dict):
                name = account.get('name', '')
                acc_type = account.get('account_type', '') or account.get('type', '')
                code = account.get('code', '')
                acc_level = account.get('level', 1)
                
                print(f"Account: {code} - {name}")
                print(f"  Type: '{acc_type}' vs '{current_type}' = {acc_type.lower() == current_type.lower()}")
                print(f"  Level: {acc_level} < {level} = {acc_level < level}")
                print(f"  Has name/code: {bool(name.strip() and code.strip())}")
                
                if (acc_type and acc_type.lower() == current_type.lower() and 
                    acc_level < level and name.strip() and code.strip()):
                    display_text = f"{code} - {name}"
                    eligible_parents.append(display_text)
                    print(f"  ✅ ELIGIBLE: {display_text}")
                else:
                    print(f"  ❌ Not eligible")
                print()
        
        print(f"\nTotal eligible parents: {len(eligible_parents)}")
        for parent in eligible_parents:
            print(f"  - {parent}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parent_suggestions()
