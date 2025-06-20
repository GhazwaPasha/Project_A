import sys
import traceback
import os
from PyQt6.QtWidgets import QApplication

# Set Mistral API key
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'

# Import the accounting system
from src.core.accounting_system_postgresql import AccountingSystem

def test_individual_pages():
    """Test each page individually."""
    app = QApplication(sys.argv)
    
    try:
        print("Creating accounting system...")
        system = AccountingSystem()
        print("✅ System created")
        
        # Test each page one by one
        pages = [
            ("Dashboard", "src.ui.pages.dashboard", "DashboardPage"),
            ("Journal", "src.ui.pages.journal", "JournalPage"),
            ("Ledger", "src.ui.pages.ledger", "LedgerPage"),
            ("TrialBalance", "src.ui.pages.trial_balance", "TrialBalancePage"),
            ("Reports", "src.ui.pages.reports", "ReportsPage"),
            ("Accounts", "src.ui.pages.accounts_hierarchy", "HierarchicalAccountsPage"),
            ("Settings", "src.ui.pages.settings", "SettingsPage"),
        ]
        
        for page_name, module_path, class_name in pages:
            try:
                print(f"\n🔍 Testing {page_name}...")
                module = __import__(module_path, fromlist=[class_name])
                PageClass = getattr(module, class_name)
                print(f"  Imported {class_name}")
                
                page = PageClass(system, parent=None)
                print(f"  ✅ {page_name} created successfully")
                
            except Exception as e:
                print(f"  ❌ {page_name} failed: {e}")
                print("  Full traceback:")
                traceback.print_exc()
                break
                
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    test_individual_pages()
