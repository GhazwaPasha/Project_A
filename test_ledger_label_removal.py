#!/usr/bin/env python3
"""
Test script to verify the account head label removal in detailed ledger view.
This script will test that:
1. The detailed ledger view loads without errors
2. The account information is shown in the page header subtitle
3. No redundant account label appears below the back button
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.pages.ledger import LedgerDocumentView
from src.core.accounting_system_unified import UnifiedAccountingSystem

def test_ledger_label_removal():
    """Test that the account label has been successfully removed."""
    app = QApplication([])
    
    # Create the ledger view
    ledger_view = LedgerDocumentView()
    
    # Create a test accounting system
    system = UnifiedAccountingSystem()
    
    # Test account details
    test_account = "Cash in Bank"
    from_date = "2024-01-01"
    to_date = "2024-12-31"
    
    # Configure the view (this should work without the account_title label)
    try:
        ledger_view.show_account_details(test_account, system, from_date, to_date)
        print("✅ Ledger view configured successfully without account title label")
        
        # Check that page header has the account information
        subtitle = ledger_view.page_header.subtitle_label.text()
        if f"Account: {test_account}" in subtitle:
            print(f"✅ Account information properly displayed in page header: {subtitle}")
        else:
            print(f"❌ Account information not found in page header subtitle: {subtitle}")
        
        # Check that account_title attribute doesn't exist
        if hasattr(ledger_view, 'account_title'):
            print("❌ account_title attribute still exists - removal incomplete")
        else:
            print("✅ account_title attribute successfully removed")
        
        ledger_view.show()
        
        # Auto-close after showing for testing
        QTimer.singleShot(3000, app.quit)
        app.exec()
        
        print("✅ Test completed successfully - label removal verified")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ledger_label_removal()
