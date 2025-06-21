#!/usr/bin/env python3
"""
VS Code Style AI Status Bar Demo
Demonstrates the new VS Code search field styling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from src.ui.components.ai_status_bar.compact_enhancer import CompactAIEnhancer

class VSCodeStyleDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VS Code Style AI Status Bar Demo")
        self.setFixedSize(800, 400)
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e1e;
                color: #cccccc;
            }
            QLabel {
                color: #cccccc;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton {
                background: #0e639c;
                border: 1px solid #007acc;
                border-radius: 3px;
                color: white;
                padding: 6px 12px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background: #1177bb;
            }
        """)
        
        self.setup_ui()
        self.setup_demo_features()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("🎨 VS Code Style AI Status Bar")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Demo AI status bar
        demo_label = QLabel("AI Status Bar (VS Code Style):")
        demo_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(demo_label)
        
        self.ai_status_bar = self.create_vscode_ai_bar()
        layout.addWidget(self.ai_status_bar)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        mood_btn = QPushButton("Change Mood")
        mood_btn.clicked.connect(self.demo_mood_change)
        controls_layout.addWidget(mood_btn)
        
        text_btn = QPushButton("Update Text")
        text_btn.clicked.connect(self.demo_text_change)
        controls_layout.addWidget(text_btn)
        
        urgent_btn = QPushButton("Show Urgent")
        urgent_btn.clicked.connect(self.demo_urgent_highlight)
        controls_layout.addWidget(urgent_btn)
        
        layout.addLayout(controls_layout)
        
        # Info
        info_label = QLabel("""
        Features Demonstrated:
        • VS Code search field colors (#3c3c3c background, #5a5a5a border)
        • Proper border radius (4px) and sizing (28px height)
        • Hover effects with VS Code blue (#0e639c)
        • Clean typography with Segoe UI font
        • Animated mood changes and text transitions
        • Urgent notification highlighting
        """)
        info_label.setStyleSheet("""
            font-size: 12px; 
            color: #888888; 
            background: #2d2d2d; 
            padding: 15px; 
            border-radius: 6px;
            border: 1px solid #404040;
        """)
        layout.addWidget(info_label)
        
    def create_vscode_ai_bar(self):
        """Create the VS Code styled AI status bar"""
        ai_container = QFrame()
        ai_container.setObjectName("CompactAIBar")
        ai_container.setFixedHeight(28)
        ai_container.setMaximumWidth(500)
        ai_container.setMinimumWidth(300)
        
        layout = QHBoxLayout(ai_container)
        layout.setContentsMargins(8, 0, 8, 0)  # Remove vertical margins
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center content vertically
        
        # AI Avatar
        self.avatar = QLabel("🤖")
        self.avatar.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 4px;
                border-radius: 4px;
                background: rgba(97, 175, 239, 0.15);
                border: 1px solid rgba(97, 175, 239, 0.3);
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }
        """)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.avatar)
          # Status text
        self.status_text = QLabel("Search anything or ask AI... 🔍")
        self.status_text.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.status_text, 1)
        
        # Action buttons
        reminder_btn = QPushButton("📋")
        reminder_btn.setFixedSize(22, 22)
        reminder_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                color: #cccccc;
                font-size: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        layout.addWidget(reminder_btn)
        
        expand_btn = QPushButton("💬")
        expand_btn.setFixedSize(22, 22)
        expand_btn.setStyleSheet("""
            QPushButton {
                background: rgba(97, 175, 239, 0.2);
                border: 1px solid rgba(97, 175, 239, 0.4);
                border-radius: 3px;
                color: #ffffff;
                font-size: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(97, 175, 239, 0.3);
                border: 1px solid rgba(97, 175, 239, 0.6);
            }
        """)
        layout.addWidget(expand_btn)
        
        # Apply VS Code styling
        ai_container.setStyleSheet("""
            QFrame#CompactAIBar {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                margin: 2px;
            }
            QFrame#CompactAIBar:hover {
                border: 1px solid #0e639c;
            }
        """)
        
        # Initialize enhancer for animations
        self.enhancer = CompactAIEnhancer(ai_container, self.status_text, self.avatar)
        
        return ai_container
        
    def setup_demo_features(self):
        """Setup automatic demo features"""
        self.demo_texts = [
            "Search anything or ask AI... 🔍",
            "Type to find accounts, transactions... 📊",
            "AI ready to help with your books 🤖",
            "Search entries or ask about balances... 💰",
            "Find reports, analyze data... 📈"
        ]
        self.current_text_index = 0
        
        self.moods = ["happy", "excited", "focused", "tired"]
        self.current_mood_index = 0
        
        # Auto-cycle demo
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.auto_demo_cycle)
        self.demo_timer.start(4000)  # Change every 4 seconds
        
    def auto_demo_cycle(self):
        """Automatically cycle through demo features"""
        self.demo_text_change()
        
    def demo_mood_change(self):
        """Demonstrate mood change animation"""
        self.current_mood_index = (self.current_mood_index + 1) % len(self.moods)
        mood = self.moods[self.current_mood_index]
        self.enhancer.pulse_avatar(mood)
        
    def demo_text_change(self):
        """Demonstrate text change animation"""
        self.current_text_index = (self.current_text_index + 1) % len(self.demo_texts)
        new_text = self.demo_texts[self.current_text_index]
        self.enhancer.animate_text_change(new_text)
        
    def demo_urgent_highlight(self):
        """Demonstrate urgent notification highlighting"""
        self.enhancer.highlight_urgent()

if __name__ == "__main__":
    print("🎨 Starting VS Code Style AI Status Bar Demo...")
    
    app = QApplication(sys.argv)
    
    window = VSCodeStyleDemo()
    window.show()
    
    print("✅ Demo window created!")
    print("   Features:")
    print("   • VS Code colors and styling")
    print("   • Automatic text cycling")
    print("   • Interactive mood changes")
    print("   • Urgent notification demo")
    
    sys.exit(app.exec())
