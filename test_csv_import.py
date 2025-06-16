#!/usr/bin/env python3
"""
Quick test script to check CSV import functionality
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_import():
    """Test if we can import the enhanced CSV import dialog."""
    try:
        from src.ui.components.enhanced_csv_import import EnhancedCSVImportDialog
        print("✅ Enhanced CSV import dialog imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_account_matcher():
    """Test if we can import the account matcher."""
    try:
        from src.core.account_matcher import AccountMatcher
        print("✅ Account matcher imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_pandas():
    """Test if pandas is available."""
    try:
        import pandas as pd
        print("✅ Pandas imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Pandas import error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing CSV import dependencies...")
    
    success = True
    success &= test_pandas()
    success &= test_account_matcher()
    success &= test_import()
    
    if success:
        print("\n🎉 All tests passed! CSV import should work.")
    else:
        print("\n💥 Some tests failed. There may be import issues.")
