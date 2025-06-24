#!/usr/bin/env python3
"""
WiFi Connection Indicator Test
Demonstrates the different connection states
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette, QColor

# Add src to path
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.compact_connection_indicator import CompactConnectionIndicator

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WiFi Connection Indicator Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Title
        title = QLabel("WiFi Connection Indicator Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Connection indicator in a titlebar-like layout
        titlebar_layout = QHBoxLayout()
        titlebar_layout.addStretch()
        
        self.connection_indicator = CompactConnectionIndicator()
        titlebar_layout.addWidget(self.connection_indicator)
        
        # Create a dark titlebar-like container
        titlebar_widget = QWidget()
        titlebar_widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px;
                margin: 10px;
            }
        """)
        titlebar_widget.setLayout(titlebar_layout)
        titlebar_widget.setFixedHeight(40)
        layout.addWidget(titlebar_widget)
        
        # Status label
        self.status_label = QLabel("Connection Status: Initializing...")
        layout.addWidget(self.status_label)
        
        # Test buttons
        button_layout = QHBoxLayout()
        
        offline_btn = QPushButton("Test Offline")
        offline_btn.clicked.connect(self.test_offline)
        button_layout.addWidget(offline_btn)
        
        poor_btn = QPushButton("Test Poor")
        poor_btn.clicked.connect(self.test_poor)
        button_layout.addWidget(poor_btn)
        
        good_btn = QPushButton("Test Good")
        good_btn.clicked.connect(self.test_good)
        button_layout.addWidget(good_btn)
        
        excellent_btn = QPushButton("Test Excellent")
        excellent_btn.clicked.connect(self.test_excellent)
        button_layout.addWidget(excellent_btn)
        
        connecting_btn = QPushButton("Test Connecting")
        connecting_btn.clicked.connect(self.test_connecting)
        button_layout.addWidget(connecting_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Auto-cycle through states
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.auto_cycle)
        self.cycle_state = 0
        
        auto_btn = QPushButton("Start Auto Cycle")
        auto_btn.clicked.connect(self.toggle_auto_cycle)
        layout.addWidget(auto_btn)
        
        # Start with offline state
        self.test_offline()
    
    def test_offline(self):
        self.connection_indicator.update_connection_status(False, 'none')
        self.status_label.setText("Connection Status: Offline (No Internet)")
        
    def test_poor(self):
        self.connection_indicator.update_connection_status(True, 'poor')
        self.status_label.setText("Connection Status: Online (Poor Connection)")
        
    def test_good(self):
        self.connection_indicator.update_connection_status(True, 'good')
        self.status_label.setText("Connection Status: Online (Good Connection)")
        
    def test_excellent(self):
        self.connection_indicator.update_connection_status(True, 'excellent')
        self.status_label.setText("Connection Status: Online (Excellent Connection)")
        
    def test_connecting(self):
        self.connection_indicator.set_connecting_state(True)
        self.status_label.setText("Connection Status: Connecting...")
        # Auto-stop connecting after 3 seconds
        QTimer.singleShot(3000, lambda: self.connection_indicator.set_connecting_state(False))
    
    def toggle_auto_cycle(self):
        if self.auto_timer.isActive():
            self.auto_timer.stop()
            self.sender().setText("Start Auto Cycle")
        else:
            self.auto_timer.start(2000)  # Change every 2 seconds
            self.sender().setText("Stop Auto Cycle")
    
    def auto_cycle(self):
        states = [
            (self.test_offline, "Offline"),
            (self.test_poor, "Poor"),
            (self.test_good, "Good"), 
            (self.test_excellent, "Excellent"),
            (self.test_connecting, "Connecting")
        ]
        
        state_func, state_name = states[self.cycle_state]
        state_func()
        print(f"Auto cycle: {state_name}")
        
        self.cycle_state = (self.cycle_state + 1) % len(states)

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = TestWindow()
    window.show()
    
    print("🧪 WiFi Connection Indicator Test Started")
    print("Try the different connection states and hover over the indicator!")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
