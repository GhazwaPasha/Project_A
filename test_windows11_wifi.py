#!/usr/bin/env python3
"""
Windows 11 Style WiFi Indicator Demo
Shows the different connection states
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette, QColor

# Add current directory to path for imports
sys.path.insert(0, '.')

from src.ui.components.compact_connection_indicator import CompactConnectionIndicator

class WiFiIndicatorDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows 11 WiFi Indicator Demo")
        self.setGeometry(100, 100, 400, 300)
        
        # Dark theme to match your app
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QLabel {
                color: white;
                font-size: 14px;
                margin: 10px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Windows 11 Style WiFi Connection Indicator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # WiFi indicator
        self.wifi_indicator = CompactConnectionIndicator()
        self.wifi_indicator.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 6px;
                margin: 20px;
            }
        """)
        layout.addWidget(self.wifi_indicator)
        
        # Status label
        self.status_label = QLabel("Status: Disconnected")
        layout.addWidget(self.status_label)
        
        # Control buttons
        btn_connected = QPushButton("🌐 Show Connected State")
        btn_connected.clicked.connect(self.show_connected)
        layout.addWidget(btn_connected)
        
        btn_connecting = QPushButton("🔄 Show Connecting Animation")
        btn_connecting.clicked.connect(self.show_connecting)
        layout.addWidget(btn_connecting)
        
        btn_disconnected = QPushButton("📶 Show Disconnected State")
        btn_disconnected.clicked.connect(self.show_disconnected)
        layout.addWidget(btn_disconnected)
        
        btn_auto_cycle = QPushButton("🔄 Auto Cycle States")
        btn_auto_cycle.clicked.connect(self.start_auto_cycle)
        layout.addWidget(btn_auto_cycle)
        
        # Auto cycle timer
        self.cycle_timer = QTimer()
        self.cycle_timer.timeout.connect(self.cycle_states)
        self.cycle_state = 0
        
        # Start with disconnected state
        self.show_disconnected()
        
    def show_connected(self):
        self.wifi_indicator.update_connection_status(True)
        self.wifi_indicator.set_connecting_state(False)
        self.status_label.setText("Status: Connected - White solid bars")
        
    def show_connecting(self):
        self.wifi_indicator.set_connecting_state(True)
        self.status_label.setText("Status: Connecting - Blue animated bars")
        
    def show_disconnected(self):
        self.wifi_indicator.update_connection_status(False)
        self.wifi_indicator.set_connecting_state(False)
        self.status_label.setText("Status: Disconnected - White outline bars")
        
    def start_auto_cycle(self):
        if self.cycle_timer.isActive():
            self.cycle_timer.stop()
            self.status_label.setText("Auto cycle stopped")
        else:
            self.cycle_timer.start(2000)  # Change every 2 seconds
            self.status_label.setText("Auto cycling states...")
            
    def cycle_states(self):
        if self.cycle_state == 0:
            self.show_disconnected()
        elif self.cycle_state == 1:
            self.show_connecting()
        elif self.cycle_state == 2:
            self.show_connected()
            
        self.cycle_state = (self.cycle_state + 1) % 3

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    demo = WiFiIndicatorDemo()
    demo.show()
    
    print("🧪 Windows 11 WiFi Indicator Demo Started")
    print("Try the different connection states and hover over the indicator!")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
