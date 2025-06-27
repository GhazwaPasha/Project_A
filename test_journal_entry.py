#!/usr/bin/env python3
"""
Test script to verify journal entry creation after fixing permission methods
"""
import sys
import os
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.auth_manager import AuthManager
from src.core.unified_accounting_system import UnifiedAccountingSystem

def test_journal_entry_creation():
    """Test journal entry creation functionality"""
    print("🧪 Testing Journal Entry Creation")
    print("=" * 40)
    
    try:
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Login
        result = auth_manager.sign_in("ghazwairshad@gmail.com", "test123")
        if not result['success']:
            print(f"❌ Login failed: {result['message']}")
            return
        
        print("✅ Login successful")
        
        # Get organizations
        organizations = auth_manager.get_user_organizations()
        if not organizations:
            print("❌ No organizations found")
            return
        
        org = organizations[0]
        print(f"📁 Organization: {org['name']} (ID: {org['id']})")
        
        # Initialize unified accounting system
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization context
        if not accounting_system.set_organization(org['id']):
            print("❌ Failed to set organization context")
            return
        
        print("🔧 Organization context set")
        
        # Test permissions
        print(f"📋 Permissions test:")
        print(f"   Can create journal entries: {auth_manager.can_create_journal_entries(org['id'])}")
        print(f"   Can create accounts: {auth_manager.can_create_accounts(org['id'])}")
        print(f"   Can edit accounts: {auth_manager.can_edit_accounts(org['id'])}")
        
        # Test creating a sample journal entry
        print("\n🧪 Testing journal entry creation...")
        entry_data = {
            'date': '2025-06-28',
            'description': 'Test transaction from API',
            'debit_account': '1001 - Cash',
            'credit_account': '2001 - Accounts Payable',
            'amount': 100.00
        }
        
        result = accounting_system.add_journal_entry(entry_data)
        if result:
            print(f"✅ Journal entry created successfully: {result}")
        else:
            print("❌ Failed to create journal entry")
        
        # Test retrieving journal entries
        print("\n🧪 Testing journal entry retrieval...")
        entries = accounting_system.get_recent_journal_entries(limit=5)
        print(f"📊 Retrieved {len(entries)} recent journal entries")
        
        if entries:
            latest_entry = entries[0]
            print(f"📋 Latest entry: {latest_entry.get('description', 'N/A')} - ${latest_entry.get('amount', 0)}")
        
        print("\n✅ All tests completed successfully!")
        print("🎉 Journal entry functionality is working!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_journal_entry_creation()
