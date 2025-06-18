#!/usr/bin/env python3
"""
Script to analyze margins and layout structure of Reports page
"""
import sys
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QGridLayout
from src.ui.mainwindow import MainWindow

def analyze_widget_margins(widget, path="", indent=0):
    """Analyze a widget's margins and layout properties"""
    indent_str = "  " * indent
    
    result = []
    
    # Basic widget info
    result.append(f"{indent_str}Widget: {widget.__class__.__name__}")
    result.append(f"{indent_str}Path: {path}")
    result.append(f"{indent_str}Position: ({widget.x()}, {widget.y()}) Size: {widget.width()}x{widget.height()}")
    result.append(f"{indent_str}Visible: {widget.isVisible()}")
    
    # Layout analysis
    if widget.layout():
        layout = widget.layout()
        result.append(f"{indent_str}Layout: {layout.__class__.__name__}")
        
        # Get margins
        margins = layout.contentsMargins()
        result.append(f"{indent_str}Layout Margins: left={margins.left()}, top={margins.top()}, right={margins.right()}, bottom={margins.bottom()}")
        result.append(f"{indent_str}Layout Spacing: {layout.spacing()}")
        
        # Size policy
        policy = widget.sizePolicy()
        result.append(f"{indent_str}Size Policy: h={policy.horizontalPolicy().name}, v={policy.verticalPolicy().name}")
        
    result.append("")
    
    return result

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
        results.append("=== REPORTS PAGE MARGIN ANALYSIS ===\n")
        
        # Analyze the main reports page
        results.extend(analyze_widget_margins(reports_page, "ReportsPage"))
          # Find and analyze the stacked widget
        stacked_widget = None
        for child in reports_page.findChildren(type(None)):
            if hasattr(child, '__class__') and 'StackedWidget' in child.__class__.__name__:
                stacked_widget = child
                break
                
        # Also try direct children
        if not stacked_widget:
            for i in range(reports_page.layout().count()):
                item = reports_page.layout().itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if 'StackedWidget' in widget.__class__.__name__:
                        stacked_widget = widget
                        break
                
        if stacked_widget:
            results.extend(analyze_widget_margins(stacked_widget, "ReportsPage/QStackedWidget", 1))
            
            # Get the overview page (should be index 0)
            overview_page = stacked_widget.widget(0)
            if overview_page:
                results.extend(analyze_widget_margins(overview_page, "ReportsPage/QStackedWidget/OverviewPage", 2))
                  # Find scroll area
                scroll_area = None
                for child in overview_page.findChildren(type(None)):
                    if hasattr(child, '__class__') and 'ScrollArea' in child.__class__.__name__:
                        scroll_area = child
                        break
                        
                # Also try direct children of overview page
                if not scroll_area and overview_page.layout():
                    for i in range(overview_page.layout().count()):
                        item = overview_page.layout().itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if 'ScrollArea' in widget.__class__.__name__:
                                scroll_area = widget
                                break
                        
                if scroll_area:
                    results.extend(analyze_widget_margins(scroll_area, "ReportsPage/QStackedWidget/OverviewPage/QScrollArea", 3))
                    
                    # Get scroll content widget
                    scroll_widget = scroll_area.widget()
                    if scroll_widget:
                        results.extend(analyze_widget_margins(scroll_widget, "ReportsPage/QStackedWidget/OverviewPage/QScrollArea/ScrollWidget", 4))
        
        # Save analysis
        with open("reports_margin_analysis.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        
        print("Reports page margin analysis saved to: reports_margin_analysis.txt")
        print(f"Reports page found: {reports_page.__class__.__name__}")
    else:
        print("Could not find Reports page widget")
    
    app.quit()

if __name__ == "__main__":
    main()
