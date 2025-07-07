#!/usr/bin/env python3
"""
Test script to verify workspace switching functionality
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_workspace_switching():
    """Test that workspace switching properly updates accounting system context"""
    try:
        from src.core.auth_manager import AuthManager
        from src.core.session_manager import SessionManager
        from src.core.accounting_system import AccountingSystem
        
        print("🔍 Testing workspace switching functionality...")
        
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Test login (you'll need to provide credentials)
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        
        result = auth_manager.sign_in(email, password)
        if not result.get('success'):
            print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
            return False
        
        print(f"✅ Login successful for {email}")
        
        # Initialize session manager
        session_manager = SessionManager(auth_manager)
        session_manager.initialize_session(result['user'])
        
        # Get available organizations
        organizations = session_manager.get_available_organizations()
        print(f"📋 Found {len(organizations)} organizations:")
        for i, org in enumerate(organizations):
            print(f"   {i+1}. {org.get('name', 'Unknown')} (ID: {org.get('id', 'Unknown')}) Type: {org.get('organization_type', 'Unknown')}")
        
        if len(organizations) < 2:
            print("⚠️ Need at least 2 organizations to test switching")
            return False
        
        # Initialize accounting system
        accounting_system = AccountingSystem(auth_manager)
        
        # Test switching between organizations
        for i, org in enumerate(organizations):
            org_id = org['id']
            org_name = org['name']
            
            print(f"\n🔄 Testing organization {i+1}: {org_name}")
            
            # Set organization in session manager
            success = session_manager.set_active_organization(org_id)
            if not success:
                print(f"❌ Failed to set active organization: {org_name}")
                continue
            
            # Set organization in accounting system
            success = accounting_system.set_organization(org_id)
            if not success:
                print(f"❌ Failed to set organization in accounting system: {org_name}")
                continue
            
            print(f"✅ Organization context set to: {org_name}")
            
            # Test data access
            try:
                accounts = accounting_system.get_chart_of_accounts()
                journal_entries = accounting_system.get_journal_entries()
                
                print(f"   📊 Accounts: {len(accounts)}")
                print(f"   📝 Journal entries: {len(journal_entries)}")
                
                # Check if data is from the correct organization
                if accounts:
                    first_account = accounts[0]
                    account_org_id = first_account.get('organization_id')
                    if account_org_id == org_id:
                        print(f"   ✅ Data belongs to correct organization")
                    else:
                        print(f"   ❌ Data belongs to wrong organization: {account_org_id} != {org_id}")
                
            except Exception as e:
                print(f"   ❌ Error accessing data: {e}")
        
        print("\n✅ Workspace switching test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_workspace_switching()
    sys.exit(0 if success else 1) 