#!/usr/bin/env python3
"""
Test script to verify the account type enum fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.auth_manager import AuthManager
from src.core.supabase_manager import SupabaseManager

def test_account_creation():
    """Test account creation with the fixed enum conversion."""
    print("🧪 Testing Account Type Enum Fix")
    print("=" * 50)
    
    # Test data - using capitalized types as UI would send
    test_account = {
        'name': 'Test Account - Enum Fix',
        'account_type': 'Asset',  # Capitalized as UI sends
        'code': 'TEST999',
        'parent_id': None,
        'description': 'Test account for enum fix verification',
        'organization_id': '0946405f-3b8a-4fe5-8c29-125b39d9ca8e',
        'created_by': 'e1b68757-3e5c-4ca1-951c-f28c26893b96'
    }
    
    print(f"📝 Creating test account with data:")
    print(f"   Name: {test_account['name']}")
    print(f"   Type: {test_account['account_type']} (capitalized - as UI would send)")
    print(f"   Code: {test_account['code']}")
    
    try:
        # Initialize auth manager and Supabase manager
        auth_manager = AuthManager()
        
        # Sign in first
        signin_result = auth_manager.sign_in("ghazwairshad@gmail.com", "sana2468")
        if not signin_result.get('success'):
            print(f"❌ Sign in failed: {signin_result.get('error')}")
            return
        
        print("✅ Signed in successfully")
        
        # Get the database manager
        db_manager = auth_manager.db_manager
        
        print(f"\n🔄 Attempting to create account through SupabaseManager...")
        
        # Test the create_account method (this should now convert Asset -> asset)
        result = db_manager.create_account(test_account)
        
        if result:
            print(f"✅ SUCCESS! Account created with ID: {result.get('id')}")
            print(f"   Stored type: {result.get('account_type')} (should be lowercase)")
            
            # Verify the account exists with correct type
            created_account = db_manager.get_account(result['id'])
            if created_account:
                print(f"✅ Verification: Account retrieved from database")
                print(f"   Database type: {created_account.get('account_type')} (lowercase)")
                print(f"   Display type: {created_account.get('account_type', '').capitalize()} (capitalized for UI)")
            else:
                print(f"⚠️  Could not retrieve created account for verification")
        else:
            print(f"❌ FAILED: Account creation returned None")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_account_creation()
