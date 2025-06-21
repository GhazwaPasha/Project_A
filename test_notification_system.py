#!/usr/bin/env python3
"""
Simple test script to verify the notification system works independently.
This creates a minimal PyQt6 app with just the notification components.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ui.components.notifications.notification_manager import NotificationManager
from ui.components.notifications.notification_drawer import NotificationDrawer
from ui.components.notification_button import NotificationButton


class TestWindow(QMainWindow):
    """Simple test window for notification system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notification System Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Initialize notification manager
        self.notification_manager = NotificationManager()
          # Create notification button
        self.notification_button = NotificationButton(self, self.notification_manager)
        self.notification_button.clicked.connect(self._show_notifications)
        layout.addWidget(self.notification_button)
        
        # Create test buttons
        test_btn1 = QPushButton("Add Test Notification")
        test_btn1.clicked.connect(self._add_test_notification)
        layout.addWidget(test_btn1)
        
        test_btn2 = QPushButton("Add Important Notification")
        test_btn2.clicked.connect(self._add_important_notification)
        layout.addWidget(test_btn2)
        
        test_btn3 = QPushButton("Add Warning Notification")
        test_btn3.clicked.connect(self._add_warning_notification)
        layout.addWidget(test_btn3)
          # Create notification drawer
        self.notification_drawer = NotificationDrawer(self, self.notification_manager)
        self.notification_drawer.hide()
        
        # Install event filter for click-outside-to-close
        self.installEventFilter(self)
        
        # Set up drawer positioning
        QTimer.singleShot(100, self._position_notification_drawer)
    
    def _add_test_notification(self):
        """Add a test notification."""
        self.notification_manager.add_notification(
            "Test Notification",
            "This is a test notification to verify the system works correctly.",
            "info"
        )
    
    def _add_important_notification(self):
        """Add an important notification."""
        self.notification_manager.add_notification(
            "Important Update",
            "Your account has been successfully synchronized with the server.",
            "success"
        )
    
    def _add_warning_notification(self):
        """Add a warning notification."""
        self.notification_manager.add_notification(
            "Connection Issue",
            "Unable to connect to the remote server. Please check your internet connection.",
            "warning"
        )
    
    def _show_notifications(self):
        """Show or hide the notification drawer."""
        if self.notification_drawer.isVisible():
            self.notification_drawer.hide()
        else:
            self._position_notification_drawer()
            self.notification_drawer.show()
    
    def _position_notification_drawer(self):
        """Position the notification drawer on the right side of the window."""
        # Calculate drawer width (30% of window width, max 400px)
        drawer_width = min(int(self.width() * 0.3), 400)
        drawer_height = self.height()
        
        # Position on the right side
        drawer_x = self.width() - drawer_width
        drawer_y = 0
        
        # Set geometry
        self.notification_drawer.setGeometry(drawer_x, drawer_y, drawer_width, drawer_height)
    
    def resizeEvent(self, event):
        """Handle window resize to reposition notification drawer."""
        super().resizeEvent(event)
        if hasattr(self, 'notification_drawer') and self.notification_drawer.isVisible():
            self._position_notification_drawer()
    
    def eventFilter(self, obj, event):
        """Filter events to handle click-outside-to-close for notification drawer."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent
        
        # Only handle mouse press events
        if event.type() == QEvent.Type.MouseButtonPress:
            if isinstance(event, QMouseEvent):
                # Check if notification drawer is open
                if hasattr(self, 'notification_drawer') and self.notification_drawer.isVisible():
                    # Get the global position of the click
                    global_pos = event.globalPosition().toPoint()
                    
                    # Convert to notification drawer's coordinate system
                    drawer_pos = self.notification_drawer.mapFromGlobal(global_pos)
                    
                    # Check if click is outside the drawer
                    if not self.notification_drawer.rect().contains(drawer_pos):
                        # Also check if click is not on the notification button
                        if hasattr(self, 'notification_button'):
                            btn_pos = self.notification_button.mapFromGlobal(global_pos)
                            if not self.notification_button.rect().contains(btn_pos):
                                # Click is outside both drawer and button, close drawer
                                self.notification_drawer.hide()
                                return True  # Event handled
        
        # Continue with normal event processing
        return super().eventFilter(obj, event)


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    # Add some initial test notifications after window is shown
    QTimer.singleShot(1000, window._add_test_notification)
    QTimer.singleShot(1500, window._add_important_notification)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
