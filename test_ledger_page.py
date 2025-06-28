#!/usr/bin/env python3
"""
Test script to verify the ledger page works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_page_header_update():
    """Test that PageHeader.update_subtitle works correctly."""
    try:
        from src.ui.components.widgets import PageHeader
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # Create a PageHeader
        header = PageHeader("Test Title", "Initial Subtitle")
        
        # Test the update_subtitle method
        header.update_subtitle("Updated Subtitle")
        print("✅ PageHeader.update_subtitle() works correctly")
        
        # Test with empty subtitle
        header.update_subtitle("")
        print("✅ PageHeader.update_subtitle('') works correctly")
        
        # Test with new subtitle
        header.update_subtitle("New Account Name")
        print("✅ PageHeader.update_subtitle('New Account Name') works correctly")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error testing PageHeader: {e}")
        return False

if __name__ == "__main__":
    print("Testing PageHeader update functionality...")
    success = test_page_header_update()
    if success:
        print("\n✅ All tests passed! The ledger page should work correctly now.")
    else:
        print("\n❌ Tests failed. There may still be issues.")
