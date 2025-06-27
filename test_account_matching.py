#!/usr/bin/env python3
"""
Test script to verify account matching functionality after fixes
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.core.unified_accounting_system import UnifiedAccountingSystem
from src.core.auth_manager import AuthManager

def test_account_matching():
    """Test the account matching functionality"""
    print("🧪 Testing Account Matching System")
    print("=" * 40)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Create unified system
        system = UnifiedAccountingSystem(auth_manager)
        
        # Try to log in a test user (use existing credentials)
        print("📋 Testing account data retrieval...")
        
        # Set organization context (using known org ID from startup)
        system.set_organization("0946405f-3b8a-4fe5-8c29-125b39d9ca8e")
        
        # Test get_postable_accounts
        print("📊 Fetching postable accounts...")
        accounts_data = system.get_postable_accounts()
        
        print(f"✅ Retrieved {len(accounts_data)} postable accounts")
        
        if accounts_data:
            print("📄 Sample accounts (first 5):")
            for i, acc in enumerate(accounts_data[:5]):
                print(f"   {i+1}. Type: {type(acc).__name__}")
                if isinstance(acc, tuple):
                    print(f"      Tuple: (name='{acc[0]}', type='{acc[1]}', code='{acc[2]}', parent_code='{acc[3]}', level={acc[4]}, is_postable={acc[5]})")
                    # Test the formatted account string
                    formatted = f"{acc[2]} - {acc[0]}"
                    print(f"      Formatted: '{formatted}'")
                else:
                    print(f"      Dict: {acc}")
                print()
        
        # Test formatted account list generation (like bulk entry does)
        print("🔗 Testing formatted account list generation...")
        try:
            formatted_accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data]
            print(f"✅ Successfully generated {len(formatted_accounts)} formatted account strings")
            
            if formatted_accounts:
                print("📄 Sample formatted accounts (first 5):")
                for i, formatted in enumerate(formatted_accounts[:5]):
                    print(f"   {i+1}. '{formatted}'")
                print()
                
        except Exception as e:
            print(f"❌ Error generating formatted accounts: {e}")
            return False
        
        print("✅ Account matching system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during account matching test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_account_matching()
    sys.exit(0 if success else 1)
