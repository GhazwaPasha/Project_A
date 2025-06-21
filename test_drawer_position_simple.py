"""
Simple test to debug notification drawer positioning
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from src.ui.components.notification_drawer import NotificationDrawer

class SimpleTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notification Drawer Position Test")
        self.setGeometry(100, 100, 1000, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Info label
        info_label = QLabel("Window Size: 1000x600\nClick 'Test Drawer' to see positioning")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 14px; margin: 20px;")
        layout.addWidget(info_label)
        
        # Test button
        test_btn = QPushButton("Test Drawer Position")
        test_btn.clicked.connect(self.test_drawer_position)
        layout.addWidget(test_btn)
        
        # Create drawer
        self.drawer = NotificationDrawer(self)
        
        # Test some notifications
        self.drawer.add_notification("Test 1", "This is a test notification")
        self.drawer.add_notification("Test 2", "Another test notification")
        
    def test_drawer_position(self):
        """Test the drawer position directly without animation"""
        print(f"\n🧪 POSITION TEST:")
        print(f"   Window size: {self.width()}x{self.height()}")
        print(f"   Drawer size: {self.drawer.width()}x{self.drawer.height()}")
        
        # Calculate where the drawer SHOULD be
        window_width = self.width()
        drawer_width = self.drawer.width()
        expected_x = window_width - drawer_width
        expected_y = 0
        
        print(f"   Expected position: ({expected_x}, {expected_y})")
        
        # Move drawer to expected position WITHOUT animation
        self.drawer.move(expected_x, expected_y)
        self.drawer.show()
        self.drawer.raise_()
        
        # Print actual position
        actual_pos = self.drawer.pos()
        print(f"   Actual position: ({actual_pos.x()}, {actual_pos.y()})")
        
        # Test opening the drawer normally
        print(f"\n🎭 Now testing normal open_drawer()...")
        self.drawer.hide()  # Hide first
        self.drawer.open_drawer()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleTestWindow()
    window.show()
    sys.exit(app.exec())
