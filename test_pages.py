import sys
import traceback
import os
import logging
from PyQt6.QtWidgets import QApplication

# Set Mistral API key as environment variable for local dev
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import PostgreSQL accounting system
from src.core.accounting_system_postgresql import AccountingSystem

def test_pages():
    """Test each page individually to find the problematic one."""
    
    # Initialize system
    print("Initializing accounting system...")
    system = AccountingSystem()
    print("✅ Accounting system initialized")
    
    # Test each page
    pages_to_test = [
        ("DashboardPage", "src.ui.pages.dashboard"),
        ("JournalPage", "src.ui.pages.journal"),
        ("LedgerPage", "src.ui.pages.ledger"),
        ("TrialBalancePage", "src.ui.pages.trial_balance"),
        ("ReportsPage", "src.ui.pages.reports"),
        ("HierarchicalAccountsPage", "src.ui.pages.accounts_hierarchy"),
        ("SettingsPage", "src.ui.pages.settings"),
    ]
    
    for page_name, module_name in pages_to_test:
        try:
            print(f"\n🔍 Testing {page_name}...")
            
            # Import the module
            module = __import__(module_name, fromlist=[page_name])
            PageClass = getattr(module, page_name)
            
            print(f"  ✅ {page_name} imported successfully")
            
            # Try to instantiate the page
            page = PageClass(system, parent=None)
            print(f"  ✅ {page_name} instantiated successfully")
            
        except Exception as e:
            print(f"  ❌ {page_name} failed: {e}")
            print(f"  Full traceback:")
            traceback.print_exc()
            print("-" * 50)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    test_pages()
