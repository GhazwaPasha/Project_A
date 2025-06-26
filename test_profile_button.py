#!/usr/bin/env python3
"""
Test script for UserProfileButton - Single Initial Display
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.components.user_profile_button import UserProfileButton

class MockAuthManager:
    """Mock auth manager for testing"""
    def get_user_profile(self):
        return {
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'full_name': 'John Doe'
        }

class MockSessionManager:
    """Mock session manager for testing"""
    def __init__(self):
        self.auth_manager = MockAuthManager()

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Profile Button Test")
        self.setFixedSize(300, 200)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add label
        label = QLabel("Testing User Profile Button with Single Initial:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # Add profile button
        session_manager = MockSessionManager()
        self.profile_button = UserProfileButton(session_manager)
        layout.addWidget(self.profile_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Connect sign out signal
        self.profile_button.sign_out_requested.connect(self.on_sign_out)
        
        # Add spacing
        layout.addStretch()
        
        print("🧪 Test: Profile button created with mock data")
        print("🧪 Expected: Should show 'J' initial in light grey circle")
        
    def on_sign_out(self):
        print("🧪 Test: Sign out clicked!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    print("🧪 Test: Application started. Check the profile button!")
    print("🧪 Test: Click the button to see dropdown with sign out option.")
    
    sys.exit(app.exec())
