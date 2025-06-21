#!/usr/bin/env python3
"""
Test script for AI Status Bar components
Run this to test the AI status bar functionality manually
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer
from src.ui.components.ai_status_bar.personality_engine import PersonalityEngine
from src.ui.components.ai_status_bar.reminder_manager import ReminderManager, ReminderPriority
from src.ui.components.ai_status_bar.compact_enhancer import CompactAIEnhancer
from datetime import datetime

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Status Bar Component Test")
        self.setFixedSize(800, 600)
        
        # Initialize AI components
        self.personality = PersonalityEngine()
        self.reminders = ReminderManager()
        
        # Setup UI
        self.setup_ui()
        
        # Test components
        self.test_personality()
        self.test_reminders()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test buttons
        test_mood_btn = QPushButton("Test Mood Detection")
        test_mood_btn.clicked.connect(self.test_mood_detection)
        layout.addWidget(test_mood_btn)
        
        test_reminder_btn = QPushButton("Test Reminder")
        test_reminder_btn.clicked.connect(self.test_reminder_creation)
        layout.addWidget(test_reminder_btn)
        
        test_greeting_btn = QPushButton("Test Context Greeting")
        test_greeting_btn.clicked.connect(self.test_context_greeting)
        layout.addWidget(test_greeting_btn)
        
    def test_personality(self):
        print("=== Testing Personality Engine ===")
        
        # Test mood detection
        context = {"page": "dashboard", "time_spent": 300}
        mood = self.personality.detect_mood_from_context(context)
        print(f"Detected mood: {mood}")
        
        # Test greeting generation
        greeting = self.personality.get_context_greeting("dashboard")
        print(f"Dashboard greeting: {greeting}")
        
    def test_reminders(self):
        print("=== Testing Reminder Manager ===")
          # Add test reminder
        self.reminders.add_reminder(
            title="Test Reminder",
            description="This is a test reminder",
            due_date=datetime.now(),
            priority=ReminderPriority.HIGH
        )
        
        # Check due reminders
        due_reminders = self.reminders.get_due_reminders()
        print(f"Due reminders: {len(due_reminders)}")
        
    def test_mood_detection(self):
        contexts = [
            {"page": "dashboard", "time_spent": 60},
            {"page": "journal", "time_spent": 1800},
            {"page": "reports", "time_spent": 300, "errors": 2}
        ]
        
        for context in contexts:
            mood = self.personality.detect_mood_from_context(context)
            print(f"Context {context} -> Mood: {mood}")
            
    def test_reminder_creation(self):
        reminder_data = {
            "title": f"Dynamic Reminder {datetime.now().strftime('%H:%M:%S')}",
            "description": "Dynamically created reminder for testing",
            "due_date": datetime.now(),
            "priority": ReminderPriority.MEDIUM
        }
        
        self.reminders.add_reminder(**reminder_data)
        print(f"Added reminder: {reminder_data['title']}")
        
    def test_context_greeting(self):
        pages = ["dashboard", "journal", "ledger", "trial_balance", "reports"]
        for page in pages:
            greeting = self.personality.get_context_greeting(page)
            print(f"{page.title()} greeting: {greeting}")

if __name__ == "__main__":
    print("🚀 Starting AI Status Bar Component Test...")
    
    app = QApplication(sys.argv)
    
    # Test components individually first
    print("\n1. Testing PersonalityEngine...")
    personality = PersonalityEngine()
    print(f"   Default mood: {personality.current_mood}")
    print(f"   Sample greeting: {personality.get_context_greeting('dashboard')}")
    
    print("\n2. Testing ReminderManager...")
    reminders = ReminderManager()
    print(f"   Reminder manager initialized: {reminders is not None}")
    
    print("\n3. Creating test window...")
    window = TestWindow()
    window.show()
    
    print("\n✅ Test window created. Close the window to exit.")
    print("   Click the buttons in the window to test different features.")
    
    sys.exit(app.exec())
