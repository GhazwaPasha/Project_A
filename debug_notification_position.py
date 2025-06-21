#!/usr/bin/env python3
"""
Debug script to test notification drawer positioning
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.notification_drawer import NotificationDrawer
from ui.components.notification_button import NotificationButton

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug Notification Position")
        self.setGeometry(100, 100, 1200, 800)        # Setup simple UI with main container structure like the real app
        self._setup_ui()
        
        # Create notification drawer with the main window as parent (correct approach)
        self.notification_drawer = NotificationDrawer(self)
        
        # Connect signals
        self.notification_button.notification_clicked.connect(self._toggle_drawer)
          # Add some test notifications
        QTimer.singleShot(1000, self._add_test_notifications)
        
    def _setup_ui(self):
        """Setup simple UI for testing"""
        # Main container (like the real app)
        self.main_container = QWidget()
        self.setCentralWidget(self.main_container)
        
        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: #2d2d2d; color: white;")
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 16, 0)
        
        title_label = QLabel("Debug Window")
        title_label.setFont(QFont("Segoe UI", 12))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Add notification button
        self.notification_button = NotificationButton()
        title_layout.addWidget(self.notification_button)
        
        layout.addWidget(title_bar)
        
        # Content area (like the real app)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: #1e1e1e; color: white;")
        layout.addWidget(self.content_widget, 1)
        
        # Debug info
        debug_layout = QVBoxLayout(self.content_widget)
        debug_layout.addWidget(QLabel("Window for testing notification drawer positioning"))
        
        # Test button
        test_btn = QPushButton("Test Drawer Position")
        test_btn.clicked.connect(self._debug_position)
        debug_layout.addWidget(test_btn)
        
        debug_layout.addStretch()
        
    def _toggle_drawer(self):
        """Toggle notification drawer"""
        if self.notification_drawer.is_open:
            self.notification_drawer.close_drawer()
        else:
            self.notification_drawer.open_drawer()
    
    def _add_test_notifications(self):
        """Add test notifications"""
        self.notification_drawer.add_notification("Test 1", "This is a test notification")
        self.notification_drawer.add_notification("Test 2", "Another test notification", "success")
        self.notification_drawer.add_notification("Test 3", "Warning notification", "warning")
          # Update button count
        count = self.notification_drawer.get_notification_count()
        self.notification_button.set_notification_count(count)
        
    def _debug_position(self):
        """Debug position information"""
        print(f"=== POSITION DEBUG ===")
        print(f"Window geometry: {self.geometry()}")
        print(f"Window size: {self.size()}")
        print(f"Drawer geometry: {self.notification_drawer.geometry()}")
        print(f"Drawer size: {self.notification_drawer.size()}")
        print(f"Drawer parent: {self.notification_drawer.parent()}")
        print(f"Drawer is_open: {self.notification_drawer.is_open}")
        
        # Calculate expected width
        window_width = self.size().width()
        expected_width = int(window_width * 0.20)
        expected_width = max(320, min(expected_width, 480))
        print(f"Window width: {window_width}px")
        print(f"Expected drawer width (20%): {expected_width}px")
        print(f"Actual drawer width: {self.notification_drawer.width()}px")
        
        # Force update position
        self.notification_drawer._update_position_and_size()
        print(f"After update - Drawer geometry: {self.notification_drawer.geometry()}")
        
        # Test opening the drawer
        print(f"📱 Opening drawer to test animation...")
        self.notification_drawer.open_drawer()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestMainWindow()
    window.show()
    
    sys.exit(app.exec())
