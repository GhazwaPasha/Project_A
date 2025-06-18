#!/usr/bin/env python3
"""
Script to specifically inspect the Reports page UI structure
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.mainwindow import MainWindow
from src.ui.components.ui_inspector import UIInspector

def main():
    app = QApplication(sys.argv)
    
    # Create the main window
    main_window = MainWindow()
    main_window.show()
    
    # Navigate to reports page (index 4 based on the _load_pages method)
    main_window.stack.setCurrentIndex(4)
    
    # Wait for the UI to update
    app.processEvents()
    
    # Get the reports page widget directly
    reports_page = main_window.stack.widget(4)
    
    if reports_page:
        # Create inspector for the reports page specifically
        inspector = UIInspector(reports_page)
        report = inspector.generate_report(format="text")
          # Save to file
        with open("reports_page_inspection.txt", "w", encoding="utf-8") as f:
            f.write("=== REPORTS PAGE UI INSPECTION ===\n\n")
            f.write(f"Page Class: {reports_page.__class__.__name__}\n")
            f.write(f"Page Type: {type(reports_page)}\n\n")
            f.write(report)
        
        print("Reports page inspection saved to: reports_page_inspection.txt")
        print(f"Reports page found: {reports_page.__class__.__name__}")
    else:
        print("Could not find Reports page widget")
    
    app.quit()

if __name__ == "__main__":
    main()
