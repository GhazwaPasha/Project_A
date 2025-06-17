#!/usr/bin/env python3
import sys
import argparse
from PyQt6.QtWidgets import QApplication
from src.ui.mainwindow import MainWindow
from src.ui.components.ui_inspector import UIInspector

def inspect_ui(output_format="text", output_file=None):
    """
    Launch the application and inspect its UI structure.
    
    Args:
        output_format (str): Output format - "text" or "json"
        output_file (str): Optional file path to save the report
    """
    # Create the application instance
    app = QApplication(sys.argv)
    
    # Create the main window
    main_window = MainWindow()
    
    # Create the inspector
    inspector = UIInspector(main_window)
    
    # Generate the report
    report = inspector.generate_report(output_file=output_file, format=output_format)
    
    if not output_file:
        print(report)
    else:
        print(f"Report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="UI Inspector CLI for analyzing application UI structure")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (text or json)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path. If not provided, prints to stdout"
    )
    
    args = parser.parse_args()
    inspect_ui(args.format, args.output)

if __name__ == "__main__":
    main()
