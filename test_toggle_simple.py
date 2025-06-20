"""
Simple test to verify the journal page expandable form toggle is working
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.mainwindow import MainWindow
from src.core.config import Config

def test_toggle():
    """Test the toggle functionality"""
    # Configure and start app
    Config.initialize()
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Navigate to journal page programmatically
    try:
        # Get the journal page
        journal_page = None
        for i in range(window.main_content.count()):
            widget = window.main_content.widget(i)
            if hasattr(widget, '__class__') and 'Journal' in widget.__class__.__name__:
                journal_page = widget
                break
        
        if journal_page:
            print("✅ Found journal page")
            
            # Access the single entry tab
            if hasattr(journal_page, 'single_entry_tab'):
                single_tab = journal_page.single_entry_tab
                print("✅ Found single entry tab")
                
                # Check if form exists
                if hasattr(single_tab, 'entry_form'):
                    print("✅ Found entry form")
                    print("📋 Toggle test ready - click the 'New Transaction' header to test expansion")
                else:
                    print("❌ Entry form not found")
            else:
                print("❌ Single entry tab not found")
        else:
            print("❌ Journal page not found")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_toggle()
