#!/usr/bin/env python3
"""
Test script for the WiFi Icon Connection Indicator
Shows the final WiFi icon with correct states:
- Connected: White color
- Disconnected: Dark grey color
- Connecting: Pulsing white
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPalette, QColor

# Add src to path for imports
sys.path.insert(0, 'src')
from ui.components.compact_connection_indicator import CompactConnectionIndicator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WiFiIconDemo(QMainWindow):
    """Demo window to showcase the WiFi icon indicator"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WiFi Icon Connection Indicator - Final Demo")
        self.setGeometry(100, 100, 500, 300)
        
        # Apply dark theme to match the app
        self._apply_dark_theme()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("WiFi Icon Connection Indicator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin: 20px;")
        layout.addWidget(title)
        
        # Create indicator container
        indicator_container = QWidget()
        indicator_layout = QHBoxLayout(indicator_container)
        indicator_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add the WiFi icon indicator
        self.indicator = CompactConnectionIndicator()
        indicator_layout.addWidget(self.indicator)
        
        # Add status label
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: white; margin-left: 10px; font-size: 14px;")
        indicator_layout.addWidget(self.status_label)
        
        layout.addWidget(indicator_container)
        
        # Control buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.simulate_connect)
        self.connect_btn.setStyleSheet(self._get_button_style())
        button_layout.addWidget(self.connect_btn)
        
        # Disconnect button
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.simulate_disconnect)
        self.disconnect_btn.setStyleSheet(self._get_button_style())
        button_layout.addWidget(self.disconnect_btn)
        
        # Connecting animation button
        self.connecting_btn = QPushButton("Show Connecting Animation")
        self.connecting_btn.clicked.connect(self.simulate_connecting)
        self.connecting_btn.setStyleSheet(self._get_button_style())
        button_layout.addWidget(self.connecting_btn)
        
        layout.addWidget(button_container)
        
        # Description
        description = QLabel(
            "WiFi Icon States:\\n"
            "• Connected: White icon\\n"
            "• Connecting: Pulsing white animation\\n"
            "• Disconnected: Dark grey icon\\n\\n"
            "No green/red colors, clean and simple design."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #ccc; font-size: 12px; margin: 20px; line-height: 1.4;")
        layout.addWidget(description)
        
        # Auto-cycle timer for demonstration
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.auto_cycle_states)
        self.demo_phase = 0
        
        # Start with disconnected state
        self.simulate_disconnect()
        
        logger.info("WiFi icon indicator demo initialized")
        
    def _apply_dark_theme(self):
        """Apply dark theme to match the main application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
        """)
        
    def _get_button_style(self):
        """Get styled button CSS"""
        return """
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                margin: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """
        
    def simulate_connect(self):
        """Simulate connection established"""
        self.indicator.update_connection_status(True)
        self.indicator.set_connecting_state(False)
        self.status_label.setText("Connected - White Icon")
        self.status_label.setStyleSheet("color: white; margin-left: 10px; font-size: 14px;")
        logger.info("Simulated connection established - icon should be white")
        
    def simulate_disconnect(self):
        """Simulate connection lost"""
        self.indicator.update_connection_status(False)
        self.indicator.set_connecting_state(False)
        self.status_label.setText("Disconnected - Dark Grey Icon")
        self.status_label.setStyleSheet("color: #808080; margin-left: 10px; font-size: 14px;")
        logger.info("Simulated connection lost - icon should be dark grey")
        
    def simulate_connecting(self):
        """Simulate connecting animation"""
        self.indicator.update_connection_status(False)
        self.indicator.set_connecting_state(True)
        self.status_label.setText("Connecting - Pulsing White")
        self.status_label.setStyleSheet("color: #cccccc; margin-left: 10px; font-size: 14px;")
        logger.info("Simulated connecting state - icon should pulse white")
        
        # Auto-connect after 3 seconds
        QTimer.singleShot(3000, self.simulate_connect)
        
    def auto_cycle_states(self):
        """Automatically cycle through states for demo"""
        states = [
            (self.simulate_disconnect, "Auto: Disconnected (Dark Grey)"),
            (self.simulate_connecting, "Auto: Connecting (Pulsing White)"),
            (self.simulate_connect, "Auto: Connected (White)")
        ]
        
        if self.demo_phase < len(states):
            action, status = states[self.demo_phase]
            action()
            logger.info(f"Auto-cycle: {status}")
            self.demo_phase += 1
        else:
            self.demo_phase = 0
            
    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key.Key_Space:
            # Space bar to toggle auto-cycle
            if self.demo_timer.isActive():
                self.demo_timer.stop()
                logger.info("Auto-cycle stopped")
            else:
                self.demo_timer.start(3000)  # 3 second intervals
                logger.info("Auto-cycle started")
        elif event.key() == Qt.Key.Key_1:
            self.simulate_disconnect()
        elif event.key() == Qt.Key.Key_2:
            self.simulate_connecting()
        elif event.key() == Qt.Key.Key_3:
            self.simulate_connect()
        else:
            super().keyPressEvent(event)

def main():
    """Run the WiFi icon indicator demo"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("WiFi Icon Demo")
    app.setApplicationVersion("1.0")
    
    # Create and show demo window
    demo = WiFiIconDemo()
    demo.show()
    
    logger.info("WiFi icon demo started. Press SPACE for auto-cycle, 1/2/3 for manual states")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
