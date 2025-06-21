#!/usr/bin/env python3
"""
Demo script to showcase the new Windows 11-style notification system
Run this to see the notification drawer and enhanced bell icon in action
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.notification_button import NotificationButton
from ui.components.notification_drawer import NotificationDrawer

class NotificationDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows 11 Notification System Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Title bar simulation
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: rgba(32, 32, 32, 0.9); border-radius: 8px;")
        title_layout = QHBoxLayout(title_bar)
        
        # Add notification button
        self.notification_button = NotificationButton()
        self.notification_button.notification_clicked.connect(self._toggle_notifications)
        title_layout.addStretch()
        title_layout.addWidget(self.notification_button)
        
        layout.addWidget(title_bar)
        
        # Demo buttons
        button_layout = QHBoxLayout()
        
        add_notification_btn = QPushButton("Add Test Notification")
        add_notification_btn.clicked.connect(self._add_test_notification)
        
        add_sync_btn = QPushButton("Add Sync Notification")
        add_sync_btn.clicked.connect(self._add_sync_notification)
        
        add_ai_btn = QPushButton("Add AI Notification")
        add_ai_btn.clicked.connect(self._add_ai_notification)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_notifications)
        
        button_layout.addWidget(add_notification_btn)
        button_layout.addWidget(add_sync_btn)
        button_layout.addWidget(add_ai_btn)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Create notification drawer
        self.notification_drawer = NotificationDrawer(self)
        self.notification_drawer.drawer_closed.connect(self._on_drawer_closed)
        
        # Demo styling
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 20, 25, 1),
                    stop:1 rgba(15, 15, 20, 1));
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Auto-demo timer
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self._auto_demo)
        self.demo_timer.start(3000)  # Add notification every 3 seconds
        
        self.demo_count = 0
        
    def _toggle_notifications(self):
        """Toggle notification drawer"""
        if self.notification_drawer.is_open:
            self.notification_drawer.close_drawer()
        else:
            self.notification_drawer.open_drawer()
            
    def _add_test_notification(self):
        """Add a test notification"""
        self.notification_drawer.add_notification(
            "Test Notification", 
            "This is a test notification to demonstrate the system",
            "info"
        )
        self._update_button_count()
        
    def _add_sync_notification(self):
        """Add a sync notification"""
        self.notification_drawer.add_notification(
            "Sync Complete", 
            "Your data has been synchronized successfully",
            "sync"
        )
        self._update_button_count()
        
    def _add_ai_notification(self):
        """Add an AI notification"""
        self.notification_drawer.add_notification(
            "AI Insight", 
            "Unusual spending pattern detected in your expenses",
            "warning"
        )
        self._update_button_count()
        
    def _clear_notifications(self):
        """Clear all notifications"""
        self.notification_drawer._clear_all_notifications()
        self.notification_button.set_notification_count(0)
        
    def _update_button_count(self):
        """Update notification button count"""
        count = self.notification_drawer.get_notification_count()
        self.notification_button.set_notification_count(count)
        
    def _on_drawer_closed(self):
        """Handle drawer being closed"""
        pass
        
    def _auto_demo(self):
        """Auto demo notifications"""
        self.demo_count += 1
        
        demo_notifications = [
            ("Welcome", "Application started successfully", "success"),
            ("Sync Status", "Background synchronization in progress", "sync"),
            ("AI Assistant", "New insights available in your dashboard", "info"),
            ("System Update", "New features have been installed", "info"),
            ("Data Export", "Your monthly report is ready for download", "success"),
            ("Account Alert", "Unusual transaction detected", "warning"),
        ]
        
        if self.demo_count <= len(demo_notifications):
            title, message, ntype = demo_notifications[self.demo_count - 1]
            self.notification_drawer.add_notification(title, message, ntype)
            self._update_button_count()
        else:
            self.demo_timer.stop()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better appearance
    
    # Set dark palette
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    demo = NotificationDemo()
    demo.show()
    
    print("🔔 Windows 11 Notification System Demo")
    print("=" * 40)
    print("Features demonstrated:")
    print("• Enhanced bell icon with notification badge")
    print("• Windows 11-style notification drawer (slides from RIGHT)")
    print("• Smooth slide-in/out animations")
    print("• Mica-compatible glassmorphism effects")
    print("• Different notification types (info, sync, warning, success)")
    print("• Click outside to close functionality")
    print("• Modern typography and spacing")
    print("• Proper overlay positioning below title bar")
    print("\nTry clicking the bell icon in the top-right corner!")
    print("The drawer will slide in from the right like Windows 11 Action Center!")
    print("Press F6/F7 in the main app for more notification demos.")
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
