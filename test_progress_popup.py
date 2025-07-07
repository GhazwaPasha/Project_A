#!/usr/bin/env python3
"""
Test script for the workspace switching progress popup
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

# Add the src directory to the path
sys.path.insert(0, 'src')

from ui.components.workspace_switching_progress import WorkspaceSwitchingProgress

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Popup Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create test button
        test_button = QPushButton("Test Progress Popup")
        test_button.clicked.connect(self.test_progress_popup)
        layout.addWidget(test_button)
        
        # Create progress popup
        self.progress_popup = WorkspaceSwitchingProgress(self)
        print(f"🧪 Progress popup created: {self.progress_popup}")
        print(f"🧪 Progress popup visible: {self.progress_popup.isVisible()}")
        print(f"🧪 Progress popup geometry: {self.progress_popup.geometry()}")
        
    def test_progress_popup(self):
        """Test the progress popup with simulated workspace switching steps"""
        print("🧪 Starting progress popup test...")
        
        # Show the popup
        print(f"🧪 About to show progress popup...")
        self.progress_popup.show_progress(self)
        print(f"🧪 Progress popup show_progress called")
        print(f"🧪 Progress popup visible after show: {self.progress_popup.isVisible()}")
        print(f"🧪 Progress popup geometry after show: {self.progress_popup.geometry()}")
        
        # Simulate workspace switching steps
        steps = [
            ("Updating navigation...", 10),
            ("Updating window title...", 20),
            ("Updating workspace switcher...", 30),
            ("Updating session context...", 40),
            ("Updating accounting system...", 50),
            ("Refreshing data...", 60),
            ("Refreshing DashboardPage...", 65),
            ("Refreshing JournalPage...", 70),
            ("Refreshing LedgerPage...", 75),
            ("Refreshing ReportsPage...", 80),
            ("Refreshing AccountsPage...", 85),
            ("Completing workspace switch...", 95),
            ("Workspace switch complete!", 100)
        ]
        
        # Update progress step by step
        for i, (status, progress) in enumerate(steps):
            QTimer.singleShot(i * 500, lambda s=status, p=progress: self.progress_popup.update_status(s, p))
        
        # Hide the popup after all steps
        QTimer.singleShot(len(steps) * 500 + 1000, self.progress_popup.hide_progress)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 