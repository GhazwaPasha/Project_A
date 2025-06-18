#!/usr/bin/env python3
"""
Script to analyze the visual layout structure of Reports page to find spacing issues
"""
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout
from src.ui.mainwindow import MainWindow

def analyze_widget_tree(widget, path="", indent=0):
    """Analyze the complete widget tree with positions and sizes"""
    indent_str = "  " * indent
    results = []
    
    # Get widget info
    class_name = widget.__class__.__name__
    object_name = widget.objectName() or "unnamed"
    visible = widget.isVisible()
    x, y = widget.x(), widget.y()
    w, h = widget.width(), widget.height()
    
    # Flag potentially problematic widgets
    flags = []
    if not visible and h > 10:
        flags.append("HIDDEN")
    if h > 100 and class_name == "QLabel":
        flags.append("LARGE_LABEL")
    if h > 50 and not visible:
        flags.append("HIDDEN_LARGE")
    if w == 0 or h == 0:
        flags.append("ZERO_SIZE")
    
    flag_str = f" [{', '.join(flags)}]" if flags else ""
    
    results.append(f"{indent_str}{class_name}({object_name}) - Pos:({x},{y}) Size:{w}x{h} Visible:{visible}{flag_str}")
    
    # Show text content for labels
    if isinstance(widget, QLabel) and hasattr(widget, 'text'):
        text = widget.text()
        if text:
            # Truncate long text
            display_text = text[:50] + "..." if len(text) > 50 else text
            results.append(f"{indent_str}  Text: '{display_text}'")
        else:
            results.append(f"{indent_str}  Text: EMPTY")
    
    # Show layout info
    if widget.layout():
        layout = widget.layout()
        margins = layout.contentsMargins()
        spacing = layout.spacing()
        results.append(f"{indent_str}  Layout: {layout.__class__.__name__} spacing={spacing} margins=({margins.left()},{margins.top()},{margins.right()},{margins.bottom()})")
    
    # Get direct children and sort by position for better readability
    children = []
    for child in widget.findChildren(type(None)):
        if child.parent() == widget:
            children.append(child)
    
    # Sort children by y position, then x position
    children.sort(key=lambda c: (c.y(), c.x()))
    
    # Analyze children
    for child in children:
        child_results = analyze_widget_tree(child, f"{path}/{class_name}", indent + 1)
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
        # Get the overview page specifically (first widget in stack)
        stacked_widget = None
        for child in reports_page.findChildren(type(None)):
            if hasattr(child, '__class__') and 'StackedWidget' in child.__class__.__name__:
                stacked_widget = child
                break
                
        if stacked_widget:
            overview_page = stacked_widget.widget(0)
            if overview_page:
                print("Analyzing Reports page overview structure...")
                
                results = []
                results.append("=== REPORTS PAGE VISUAL STRUCTURE ANALYSIS ===\n")
                
                widget_tree = analyze_widget_tree(overview_page, "OverviewPage")
                results.extend(widget_tree)
                
                # Save analysis
                with open("reports_visual_structure.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(results))
                
                print("Reports page visual structure saved to: reports_visual_structure.txt")
                print(f"Analyzed {len(widget_tree)} widgets")
            else:
                print("Could not find overview page")
        else:
            print("Could not find stacked widget")
    else:
        print("Could not find Reports page widget")
    
    app.quit()

if __name__ == "__main__":
    main()
