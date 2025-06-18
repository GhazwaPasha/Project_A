#!/usr/bin/env python3
"""
Script to find empty or hidden elements in Reports page that might be causing spacing issues
"""
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QTextEdit, QPushButton
from src.ui.mainwindow import MainWindow

def analyze_empty_elements(widget, path="", indent=0):
    """Find empty or problematic elements that might cause spacing issues"""
    indent_str = "  " * indent
    results = []
    
    # Check if this is a text-based widget
    if isinstance(widget, (QLabel, QLineEdit, QTextEdit, QPushButton)):
        text_content = ""
        
        if hasattr(widget, 'text'):
            text_content = widget.text()
        elif hasattr(widget, 'toPlainText'):
            text_content = widget.toPlainText()
            
        # Report empty or suspicious text elements
        if not text_content or text_content.strip() == "":
            results.append(f"{indent_str}EMPTY {widget.__class__.__name__}: '{text_content}'")
            results.append(f"{indent_str}  Position: ({widget.x()}, {widget.y()}) Size: {widget.width()}x{widget.height()}")
            results.append(f"{indent_str}  Visible: {widget.isVisible()}")
            results.append(f"{indent_str}  Path: {path}/{widget.__class__.__name__}")
            results.append("")
        elif len(text_content.strip()) < 5:  # Very short text might be problematic
            results.append(f"{indent_str}SHORT {widget.__class__.__name__}: '{text_content}'")
            results.append(f"{indent_str}  Position: ({widget.x()}, {widget.y()}) Size: {widget.width()}x{widget.height()}")
            results.append(f"{indent_str}  Visible: {widget.isVisible()}")
            results.append(f"{indent_str}  Path: {path}/{widget.__class__.__name__}")
            results.append("")
    
    # Check for widgets with unusual sizes that might be taking up space
    if widget.height() > 0 and widget.width() > 0:
        if widget.height() > 50 and not widget.isVisible():
            results.append(f"{indent_str}HIDDEN LARGE {widget.__class__.__name__}")
            results.append(f"{indent_str}  Position: ({widget.x()}, {widget.y()}) Size: {widget.width()}x{widget.height()}")
            results.append(f"{indent_str}  Path: {path}/{widget.__class__.__name__}")
            results.append("")
    
    # Recursively check children
    for child in widget.findChildren(type(None)):
        if child.parent() == widget:  # Only direct children
            child_results = analyze_empty_elements(child, f"{path}/{widget.__class__.__name__}", indent + 1)
            results.extend(child_results)
    
    return results

def analyze_layout_spacing(widget, path="", indent=0):
    """Analyze layout spacing and margins that might be excessive"""
    indent_str = "  " * indent
    results = []
    
    if widget.layout():
        layout = widget.layout()
        margins = layout.contentsMargins()
        spacing = layout.spacing()
        
        # Flag unusual spacing or margins
        if spacing > 50:
            results.append(f"{indent_str}LARGE SPACING: {widget.__class__.__name__} spacing={spacing}")
            results.append(f"{indent_str}  Path: {path}")
            results.append("")
            
        if margins.top() > 50 or margins.bottom() > 50:
            results.append(f"{indent_str}LARGE MARGINS: {widget.__class__.__name__}")
            results.append(f"{indent_str}  Margins: top={margins.top()}, bottom={margins.bottom()}")
            results.append(f"{indent_str}  Path: {path}")
            results.append("")
    
    # Check children
    for child in widget.findChildren(type(None)):
        if child.parent() == widget:
            child_results = analyze_layout_spacing(child, f"{path}/{widget.__class__.__name__}", indent + 1)
            results.extend(child_results)
    
    return results

def main():
    app = QApplication(sys.argv)
    
    # Create the main window
    main_window = MainWindow()
    main_window.show()
    
    # Navigate to reports page (index 4)
    main_window.stack.setCurrentIndex(4)
    app.processEvents()
    
    # Get the reports page widget
    reports_page = main_window.stack.widget(4)
    
    if reports_page:
        results = []
        results.append("=== REPORTS PAGE EMPTY ELEMENTS ANALYSIS ===\n")
        
        # Find empty elements
        empty_elements = analyze_empty_elements(reports_page, "ReportsPage")
        if empty_elements:
            results.append("EMPTY/SHORT TEXT ELEMENTS:")
            results.extend(empty_elements)
            results.append("\n" + "="*50 + "\n")
        
        # Find spacing issues
        spacing_issues = analyze_layout_spacing(reports_page, "ReportsPage")
        if spacing_issues:
            results.append("SPACING/MARGIN ISSUES:")
            results.extend(spacing_issues)
        
        # Save analysis
        with open("reports_empty_elements.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        
        print("Reports page empty elements analysis saved to: reports_empty_elements.txt")
        print(f"Found {len(empty_elements)} potential empty element issues")
        print(f"Found {len(spacing_issues)} potential spacing issues")
    else:
        print("Could not find Reports page widget")
    
    app.quit()

if __name__ == "__main__":
    main()
