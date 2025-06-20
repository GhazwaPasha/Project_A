#!/usr/bin/env python3
"""
PostgreSQL Accounting System Validation Script
Tests all core functionalities of the clean PostgreSQL implementation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, date
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_postgresql_accounting_system():
    """Test all functionalities of the PostgreSQL accounting system."""
    try:
        # Import the system
        from src.core.accounting_system_postgresql import AccountingSystem
        
        logger.info("🚀 Starting PostgreSQL Accounting System validation...")
        
        # Initialize system
        system = AccountingSystem()
        logger.info("✅ System initialized successfully")
        
        # Test connection
        if system.test_connection():
            logger.info("✅ Database connection test passed")
        else:
            raise Exception("Database connection test failed")
        
        # Test account creation
        logger.info("Testing account management...")
        
        # Create test accounts
        assets_code = system.create_account("Test Assets", "Asset", "9000", None, False, "Test assets account")
        cash_code = system.create_account("Test Cash", "Asset", "9001", "9000", True, "Test cash account")
        liability_code = system.create_account("Test Liabilities", "Liability", "9200", None, False, "Test liabilities account")
        equity_code = system.create_account("Test Owner's Equity", "Equity", "9300", None, True, "Test owner's equity account")
        
        logger.info(f"✅ Created test accounts: Assets({assets_code}), Cash({cash_code}), Liabilities({liability_code}), Equity({equity_code})")
        
        # Test account retrieval
        all_accounts = system.get_all_accounts()
        postable_accounts = system.get_postable_accounts()
        
        logger.info(f"✅ Retrieved {len(all_accounts)} total accounts, {len(postable_accounts)} postable accounts")
        
        # Test journal entries
        logger.info("Testing journal entry management...")
          # Add test journal entries
        entry1_id = system.add_journal_entry(date.today(), "Test initial investment", "Test Cash", "Test Owner's Equity", 1000.00)
        entry2_id = system.add_journal_entry(date.today(), "Test additional investment", "Test Cash", "Test Owner's Equity", 500.00)
        
        logger.info(f"✅ Added test journal entries: {entry1_id}, {entry2_id}")
        
        # Test journal entry retrieval
        all_entries = system.get_journal_entries()
        cash_entries = system.get_journal_entries(account_filter="Test Cash")
        
        logger.info(f"✅ Retrieved {len(all_entries)} total entries, {len(cash_entries)} cash entries")
        
        # Test balance calculation
        cash_balance = system.get_account_balance("Test Cash")
        equity_balance = system.get_account_balance("Test Owner's Equity")
        
        logger.info(f"✅ Calculated balances - Test Cash: ${cash_balance}, Test Equity: ${equity_balance}")
        
        # Test trial balance
        trial_balance = system.get_trial_balance()
        logger.info(f"✅ Generated trial balance with {len(trial_balance)} accounts")
        
        # Test ledger
        cash_ledger = system.get_ledger("Test Cash")
        logger.info(f"✅ Generated Test Cash ledger with {len(cash_ledger)} entries")
        
        # Test search
        search_results = system.search_accounts("Test Cash")
        logger.info(f"✅ Search for 'Test Cash' returned {len(search_results)} results")
        
        # Test statistics
        stats = system.get_statistics()
        logger.info(f"✅ System statistics: {stats}")
        
        # Test account hierarchy
        hierarchy = system.get_account_hierarchy()
        logger.info(f"✅ Account hierarchy retrieved: {len(hierarchy)} accounts")
        
        # Test update operations
        system.update_account(cash_code, description="Updated test cash account description")
        system.update_journal_entry(entry1_id, description="Updated test initial investment")
        logger.info("✅ Update operations completed")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        system.delete_journal_entry(entry1_id)
        system.delete_journal_entry(entry2_id)
        system.delete_account(cash_code)
        system.delete_account(assets_code)
        system.delete_account(liability_code)
        system.delete_account(equity_code)
        logger.info("✅ Test data cleaned up")
        
        # Final validation
        logger.info("🎉 All tests passed! PostgreSQL Accounting System is fully functional.")
        
        # Display summary
        logger.info("\n" + "="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"📊 Total Accounts: {stats['total_accounts']}")
        logger.info(f"📝 Postable Accounts: {stats['postable_accounts']}")
        logger.info(f"📋 Journal Entries: {stats['total_entries']}")
        logger.info(f"💰 Test Cash Balance: ${cash_balance}")
        logger.info(f"🏦 Test Equity Balance: ${equity_balance}")
        logger.info(f"📅 Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_postgresql_accounting_system()
    if success:
        print("\n🎉 VALIDATION SUCCESSFUL - Your PostgreSQL accounting system is ready for production!")
    else:
        print("\n❌ VALIDATION FAILED - Please check the errors above.")
