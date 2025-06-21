#!/usr/bin/env python3
"""
Test script for the new modern sync indicator with spinning arrow.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.components.modern_sync_indicator import ModernSyncStatusIndicator


class TestWindow(QMainWindow):
    """Test window for the sync indicator."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Sync Indicator Test")
        self.setGeometry(100, 100, 600, 300)
        
        # Set dark background
        self.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
                color: white;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("Modern Sync Indicator Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Sync indicator
        self.sync_indicator = ModernSyncStatusIndicator()
        layout.addWidget(self.sync_indicator)
        
        # Test buttons
        btn_start_sync = QPushButton("Start Remote Sync (with spinner)")
        btn_start_sync.clicked.connect(self.start_sync_test)
        layout.addWidget(btn_start_sync)
        
        btn_stop_sync = QPushButton("Stop Sync")
        btn_stop_sync.clicked.connect(self.stop_sync_test)
        layout.addWidget(btn_stop_sync)
        
        btn_error = QPushButton("Show Error")
        btn_error.clicked.connect(self.show_error_test)
        layout.addWidget(btn_error)
        
        btn_success = QPushButton("Show Success")
        btn_success.clicked.connect(self.show_success_test)
        layout.addWidget(btn_success)
        
        btn_local_only = QPushButton("Set Local Only")
        btn_local_only.clicked.connect(self.set_local_only)
        layout.addWidget(btn_local_only)
        
        btn_both_connected = QPushButton("Set Both Databases Connected")
        btn_both_connected.clicked.connect(self.set_both_connected)
        layout.addWidget(btn_both_connected)
        
        layout.addStretch()
        
        # Initialize with both databases connected
        self.set_both_connected()
        
    def start_sync_test(self):
        """Test starting sync with spinner."""
        status = {
            'local_available': True,
            'remote_available': True,
            'sync_status': {
                'is_syncing': True,
                'pending_operations': 5,
                'failed_operations': 0,
                'last_sync': None
            }
        }
        self.sync_indicator.update_connection_status(status)
        
    def stop_sync_test(self):
        """Test stopping sync."""
        status = {
            'local_available': True,
            'remote_available': True,
            'sync_status': {
                'is_syncing': False,
                'pending_operations': 0,
                'failed_operations': 0,
                'last_sync': "2025-06-21 12:30:00"
            }
        }
        self.sync_indicator.update_connection_status(status)
        
    def show_error_test(self):
        """Test error display."""
        self.sync_indicator.show_error("Failed to connect to remote database")
        
    def show_success_test(self):
        """Test success display."""
        self.sync_indicator.show_success("All changes synced successfully")
        
    def set_local_only(self):
        """Test local only mode."""
        status = {
            'local_available': True,
            'remote_available': False,
            'sync_status': {
                'is_syncing': False,
                'pending_operations': 0,
                'failed_operations': 0,
                'last_sync': None
            }
        }
        self.sync_indicator.update_connection_status(status)
        
    def set_both_connected(self):
        """Test both databases connected."""
        status = {
            'local_available': True,
            'remote_available': True,
            'sync_status': {
                'is_syncing': False,
                'pending_operations': 0,
                'failed_operations': 0,
                'last_sync': "2025-06-21 12:25:00"
            }
        }
        self.sync_indicator.update_connection_status(status)


def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("✓ Modern Sync Indicator Test Window Created")
    print("✓ Test the different states using the buttons")
    print("✓ The spinning arrow should appear during remote sync")
    print("✓ Left-click the status field to see recent activity")
    print("✓ Right-click the status field to trigger manual sync")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
