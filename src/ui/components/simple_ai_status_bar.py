"""
Simple AI Status Bar - Enhanced with dynamic status display and AI integration
The status bar itself becomes the input field when expanded
"""
from PyQt6.QtWidgets import QLineEdit, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPalette
import threading
import time
import random
import json
import os
from datetime import datetime, timedelta

class SimpleAIStatusBar(QLineEdit):
    """Enhanced AI status bar with dynamic status display, notifications, and motivational messages"""
    ai_command_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_expanded = False
        self.is_processing = False
        self.placeholder_text = "Ask AI anything..."
        
        # Dynamic status management
        self.current_state = "idle"  # idle, processing, notification, background_task
        self.last_activity_time = datetime.now()
        self.last_motivational_message_time = datetime.now() - timedelta(hours=1)
        self.current_page_context = None
        self.unread_notifications_count = 0
        self.background_processes = []
        
        # Message preferences (will be loaded from user settings later)
        self.motivational_enabled = True
        self.wellness_enabled = True
        self.break_reminder_interval = 2  # hours
        self.last_break_reminder = datetime.now() - timedelta(hours=2)
          # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
        self._setup_dynamic_status()
        
    def _setup_dynamic_status(self):
        """Setup timers and monitoring for dynamic status display"""
        # Main status update timer - checks every 2 minutes for better performance
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_dynamic_status)
        self.status_timer.start(120000)  # 2 minutes instead of 30 seconds
        
        # Notification checker - checks every 30 seconds for responsive notifications
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self._check_notifications)
        self.notification_timer.start(30000)  # 30 seconds instead of 10 seconds
        
        # Initial status set
        self._update_dynamic_status()
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Set initial properties - start as a read-only status display
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)        # Set initial size - compact for title bar
        self.setFixedHeight(30)  # Reduced height to 30px
        self.setFixedWidth(350)
        
        # Connect events
        self.returnPressed.connect(self._process_input)
        
    def _setup_animations(self):
        """Setup smooth animations"""
        # Width animation for smooth expansion
        self.width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.width_animation.setDuration(300)
        self.width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Width animation for minimum width to ensure proper center expansion
        self.min_width_animation = QPropertyAnimation(self, b"minimumWidth")
        self.min_width_animation.setDuration(300)
        self.min_width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def _apply_styling(self):
        """Apply styling to match date range selector custom date fields"""
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 4px 12px;
                selection-background-color: rgba(100, 181, 246, 0.3);
                outline: none;
                text-align: center;
            }
            
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
                outline: none;
            }
            
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: white;
                outline: none;
                text-align: left;
            }
            
            QLineEdit[readOnly="true"] {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                color: white;
                outline: none;
                text-align: center;
            }
            
            QLineEdit[readOnly="true"]:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
                outline: none;
                text-align: center;
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse click to expand"""
        if not self.is_expanded and not self.is_processing and self.isReadOnly():
            self._expand_for_input()
        else:
            super().mousePressEvent(event)
            
    def focusOutEvent(self, event):
        """Handle losing focus - collapse if not processing"""
        super().focusOutEvent(event)
        if self.is_expanded and not self.text().strip() and not self.is_processing:
            QTimer.singleShot(50, self._collapse_to_normal)
            
    def _expand_for_input(self):
        """Expand the status bar to become an input field"""
        self.is_expanded = True
        
        # Transform into input field
        self.setReadOnly(False)
        self.clear()
        self.setPlaceholderText("Type your question...")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setFocus()
        
        # Animate width expansion from center
        self.width_animation.setStartValue(350)
        self.width_animation.setEndValue(500)
        self.min_width_animation.setStartValue(350)
        self.min_width_animation.setEndValue(500)
        
        # Start both animations simultaneously for center expansion
        self.width_animation.start()
        self.min_width_animation.start()
        
        # Update fixed width after animation
        QTimer.singleShot(300, lambda: self.setFixedWidth(500))        
    def _process_input(self):
        """Process user input by emitting a signal."""
        user_input = self.text().strip()
        if not user_input or self.is_processing:
            return
            
        self.ai_command_submitted.emit(user_input)

    def show_processing_indicator(self):
        """Display a processing message."""
        self.is_processing = True
        self.setReadOnly(True)
        self.setText("Processing...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def hide_processing_indicator(self):
        """Hide the processing message and collapse the bar."""
        self.is_processing = False
        self._collapse_to_normal()

    def set_ai_response(self, response: str):
        """Display the AI's final response message."""
        self.is_processing = False
        self.setText(response)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Collapse after a delay to allow user to read the response
        QTimer.singleShot(4000, self._collapse_to_normal)

    def set_error_message(self, error_message: str):
        """Display an error message."""
        self.is_processing = False
        self.setText(f"Error: {error_message}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Collapse after a delay
        QTimer.singleShot(5000, self._collapse_to_normal)

    def _collapse_to_normal(self):
        """Collapse the input field back to a status display"""
        self.is_expanded = False
        self.is_processing = False
        
        # Restore read-only status display
        self.setReadOnly(True)
        self.setPlaceholderText("") # Clear placeholder
        self.setText("Ask AI anything...") # Reset to default
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clearFocus()
        
        # Animate width collapse
        self.width_animation.setStartValue(self.width())
        self.width_animation.setEndValue(350)
        self.min_width_animation.setStartValue(self.width())
        self.min_width_animation.setEndValue(350)
        
        self.width_animation.start()
        self.min_width_animation.start()
          # Reset fixed width after animation
        QTimer.singleShot(300, lambda: self.setFixedWidth(350))
    
    def set_context(self, page_name, context_data=None):
        """Set the current page context for the AI status bar"""
        self.current_page_context = page_name.lower() if page_name else None
        if not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
    
    def set_processing_status(self, status_message):
        """Set a custom processing status message"""
        if self.is_processing:
            self.setText(status_message)
    
    def update_activity(self):
        """Update last activity time - call this when user interacts with the app"""
        self.last_activity_time = datetime.now()
    
    def _get_motivational_messages(self):
        """Get categorized motivational messages"""
        return {
            "work_motivation": [
                "Great job staying on top of your finances! 📊",
                "Every transaction recorded is a step toward better financial control 💪",
                "Your attention to detail makes all the difference in accounting ✨",
                "Consistent bookkeeping today = stress-free reporting tomorrow 🎯",
                "You're building a solid financial foundation! 🏗️",
                "Each entry brings clarity to your business performance 📈",
                "Your systematic approach to bookkeeping is paying off 💼"
            ],
            "wellness": [
                "Remember to take a short break and stretch your eyes 👀",
                "You've been working hard - time for a 5-minute breather? ☕",
                "Stay hydrated while crunching those numbers! 💧",
                "Good posture = better focus. Adjust your seat and carry on! 🪑",
                "Deep breath in, numbers out - you've got this! 🧘‍♀️",
                "Take time to appreciate how much you've accomplished 🙏",
                "Progress over perfection - you're doing great 🌱"
            ],
            "achievement": [
                "You've completed several entries today - excellent progress! 🏆",
                "Your books are looking organized and professional 📈",
                "Month-end tasks completed efficiently - well done! 🎉",
                "Your financial records show real attention to detail 🔍",
                "Another productive session in the books! 📚"
            ],
            "time_based": {
                "morning": [
                    "Good morning! Ready to tackle today's accounting tasks? ☀️",
                    "Fresh start, fresh books - let's make it a productive day! 🌅",
                    "Morning focus = accurate entries. You've got this! ⭐"
                ],
                "afternoon": [
                    "Afternoon productivity boost coming right up! ⚡",
                    "Halfway through the day - maintaining that accuracy! 🎯",
                    "Steady progress through the afternoon 📊"
                ],
                "evening": [
                    "Wrapping up another productive day of bookkeeping 🌙",
                    "End of day approaching - great work today! 🌅",
                    "Time to review today's accomplishments ✨"
                ]
            }
        }
    
    def _get_context_messages(self):
        """Get context-aware messages based on current page"""
        return {
            "dashboard": [
                "Your financial overview looks comprehensive 📊",
                "Dashboard showing healthy business metrics 📈",
                "Quick insights available - ask me anything! 🤖"
            ],
            "journal": [
                "Journal entries are the heart of good bookkeeping 📝",
                "Every transaction tells a story about your business 📖",
                "Accurate journal entries = reliable reports 🎯"
            ],
            "accounts": [
                "Well-organized chart of accounts = clear reporting 🗂️",
                "Your account structure looks professional 💼",
                "Account balances reflecting business health 📊"
            ],            "reports": [
                "Reports transform data into business insights 📈",
                "Financial reports are your business compass 🧭",
                "Numbers tell the story - you're the author ✍️"
            ]
        }
    
    def _update_dynamic_status(self):
        """Update the status bar with dynamic content when idle"""
        try:
            if self.is_expanded or self.is_processing:
                return
                
            current_time = datetime.now()
            
            # Check for background processes first
            if self.background_processes:
                self._show_background_process_status()
                return
                
            # Check for unread notifications
            if self.unread_notifications_count > 0:
                self._show_notification_reminder()
                return
                
            # Check if it's time for a motivational message
            time_since_last_message = current_time - self.last_motivational_message_time
            if time_since_last_message.total_seconds() > 3600:  # 1 hour
                self._show_motivational_message()
                return
                
            # Check for break reminders
            time_since_last_break = current_time - self.last_break_reminder
            if (self.wellness_enabled and 
                time_since_last_break.total_seconds() > self.break_reminder_interval * 3600):
                self._show_break_reminder()
                return
                
            # Default context-aware message
            self._show_context_message()
        except Exception as e:
            # Silent fail - don't disrupt the UI
            print(f"AI Status Bar update error: {e}")
    
    def _show_motivational_message(self):
        """Display a motivational message"""
        if not self.motivational_enabled:
            return
            
        messages = self._get_motivational_messages()
        current_hour = datetime.now().hour
        
        # Choose message category based on time and activity
        if 6 <= current_hour < 12:
            category = random.choice(["work_motivation", "time_based"])
            if category == "time_based":
                message = random.choice(messages["time_based"]["morning"])
            else:
                message = random.choice(messages["work_motivation"])
        elif 12 <= current_hour < 18:
            category = random.choice(["work_motivation", "achievement", "time_based"])
            if category == "time_based":
                message = random.choice(messages["time_based"]["afternoon"])
            else:
                message = random.choice(messages[category])
        else:
            category = random.choice(["achievement", "time_based"])
            if category == "time_based":
                message = random.choice(messages["time_based"]["evening"])
            else:
                message = random.choice(messages["achievement"])
        
        self.setText(message)
        self.placeholder_text = message
        self.last_motivational_message_time = datetime.now()
        
        # Reset to normal after 10 seconds
        QTimer.singleShot(10000, self._reset_to_default_message)
    
    def _show_break_reminder(self):
        """Show wellness break reminder"""
        if not self.wellness_enabled:
            return
            
        messages = self._get_motivational_messages()["wellness"]
        message = random.choice(messages)
        
        self.setText(message)
        self.placeholder_text = message
        self.last_break_reminder = datetime.now()
        
        # Reset to normal after 15 seconds (longer for wellness messages)
        QTimer.singleShot(15000, self._reset_to_default_message)
    
    def _show_notification_reminder(self):
        """Show notification reminder"""
        if self.unread_notifications_count == 1:
            message = f"You have 1 unread notification 🔔"
        else:
            message = f"You have {self.unread_notifications_count} unread notifications 🔔"
            
        self.setText(message)
        self.placeholder_text = message
    
    def _show_background_process_status(self):
        """Show background process status"""
        if not self.background_processes:
            return
            
        # Show the most recent/important process
        process = self.background_processes[-1]
        message = f"{process.get('message', 'Background process running')} {process.get('progress', '')}"
        
        self.setText(message)
        self.placeholder_text = message
    
    def _show_context_message(self):
        """Show context-aware message based on current page"""
        messages = self._get_context_messages()
        
        if self.current_page_context and self.current_page_context in messages:
            message = random.choice(messages[self.current_page_context])
        else:
            message = "🤖 AI Assistant - Ask me anything!"
            
        self.setText(message)
        self.placeholder_text = message
    
    def _reset_to_default_message(self):
        """Reset to default dynamic message"""
        if not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
    
    def _check_notifications(self):
        """Check for new notifications and update count"""
        try:
            # Check if reminders_data.json exists and get unread count
            reminders_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reminders_data.json')
            if os.path.exists(reminders_file):
                with open(reminders_file, 'r') as f:
                    reminders_data = json.load(f)
                    
                # Count unread notifications (assuming there's an 'unread' field)
                unread_count = 0
                for reminder in reminders_data.get('reminders', []):
                    if reminder.get('status') == 'active' and not reminder.get('acknowledged', False):
                        unread_count += 1
                        
                if unread_count != self.unread_notifications_count:
                    old_count = self.unread_notifications_count
                    self.unread_notifications_count = unread_count
                    
                    # Show new notification alert if count increased
                    if unread_count > old_count and not self.is_expanded:
                        self._show_new_notification_alert()
                        
        except Exception as e:
            # Silent fail - don't disrupt the UI
            pass
    
    def _show_new_notification_alert(self):
        """Show alert for new notification"""
        alert_message = "New notification arrived! 🔔✨"
        self.setText(alert_message)
        self.placeholder_text = alert_message
        
        # Flash effect - brief highlight
        original_style = self.styleSheet()
        highlight_style = original_style.replace(
            "border: 1px solid rgba(0, 0, 0, 0.3)",
            "border: 2px solid rgba(100, 181, 246, 0.8)"
        )
        self.setStyleSheet(highlight_style)
        
        # Reset style and message after 3 seconds
        QTimer.singleShot(3000, lambda: [
            self.setStyleSheet(original_style),
            self._reset_to_default_message()
        ])
    
    # Background process management methods
    def add_background_process(self, process_id, message, progress=""):
        """Add a background process to track"""
        process = {
            'id': process_id,
            'message': message,
            'progress': progress,
            'start_time': datetime.now()
        }
        self.background_processes.append(process)
        
        if not self.is_expanded and not self.is_processing:
            self._show_background_process_status()
    
    def update_background_process(self, process_id, message=None, progress=None):
        """Update a background process"""
        for process in self.background_processes:
            if process['id'] == process_id:
                if message:
                    process['message'] = message
                if progress:
                    process['progress'] = progress
                    
                if not self.is_expanded and not self.is_processing:
                    self._show_background_process_status()
                break
    
    def remove_background_process(self, process_id):
        """Remove a completed background process"""
        self.background_processes = [p for p in self.background_processes if p['id'] != process_id]
        
        # Update display if this was the last process
        if not self.background_processes and not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
    
    def handle_ai_response(self, response_text: str):
        """Handle response from AI command processor"""
        self.setText(response_text)
        self.is_processing = False
        
        # Auto-collapse after showing response for 5 seconds
        QTimer.singleShot(5000, self._collapse_to_normal)
    
    def handle_ai_error(self, error_message: str):
        """Handle AI processing errors"""
        self.setText(f"AI Error: {error_message}")
        self.is_processing = False
        QTimer.singleShot(3000, self._reset_to_default_message)
    
    def handle_processing_started(self):
        """Handle AI processing started signal"""
        self.set_processing_status("AI is thinking...")
    
    def handle_processing_finished(self):
        """Handle AI processing finished signal"""
        # Processing status will be updated by other handlers
        pass
    
    def _reset_to_default_message(self):
        """Reset to default dynamic message"""
        if not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
